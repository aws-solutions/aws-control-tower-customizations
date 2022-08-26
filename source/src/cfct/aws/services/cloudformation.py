##############################################################################
#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.   #
#                                                                            #
#  Licensed under the Apache License, Version 2.0 (the "License").           #
#  You may not use this file except in compliance                            #
#  with the License. A copy of the License is located at                     #
#                                                                            #
#      http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                            #
#  or in the "license" file accompanying this file. This file is             #
#  distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY  #
#  KIND, express or implied. See the License for the specific language       #
#  governing permissions  and limitations under the License.                 #
##############################################################################

# !/bin/python

import os
from botocore.exceptions import ClientError
from cfct.utils.retry_decorator import try_except_retry
from cfct.aws.utils.boto3_session import Boto3Session
from cfct.types import StackSetInstanceTypeDef, StackSetRequestTypeDef, ResourcePropertiesTypeDef
import json

from typing import Dict, List, Any


class StackSet(Boto3Session):
    DEPLOYED_BY_CFCT_TAG = {"Key": "AWS_Solutions", "Value": "CustomControlTowerStackSet"}
    CFCT_STACK_SET_PREFIX = "CustomControlTower-"
    DEPLOY_METHOD = "stack_set"

    def __init__(self, logger, **kwargs):
        self.logger = logger
        __service_name = 'cloudformation'
        self.max_concurrent_percent = int(
            os.environ.get('MAX_CONCURRENT_PERCENT', 100))
        self.failed_tolerance_percent = int(
            os.environ.get('FAILED_TOLERANCE_PERCENT', 10))
        self.region_concurrency_type = os.environ.get(
            'REGION_CONCURRENCY_TYPE', 'PARALLEL').upper()
        self.max_results_per_page = 20
        super().__init__(logger, __service_name, **kwargs)
        self.cfn_client = super().get_client()

        self.operation_in_progress_except_msg =  \
            'Caught exception OperationInProgressException'  \
            ' handling the exception...'

    @try_except_retry()
    def describe_stack_set(self, stack_set_name):
        try:
            response = self.cfn_client.describe_stack_set(
                StackSetName=stack_set_name
            )
            return response
        except self.cfn_client.exceptions.StackSetNotFoundException:
            pass
        except Exception as e:
            self.logger.log_unhandled_exception(e)
            raise

    @try_except_retry()
    def describe_stack_set_operation(self, stack_set_name, operation_id):
        try:
            response = self.cfn_client.describe_stack_set_operation(
                StackSetName=stack_set_name,
                OperationId=operation_id
            )
            return response
        except ClientError as e:
            self.logger.error("'{}' StackSet Operation ID: {} not found."
                              .format(stack_set_name, operation_id))
            self.logger.log_unhandled_exception(e)
            raise

    @try_except_retry()
    def list_stack_instances(self, **kwargs):
        try:
            response = self.cfn_client.list_stack_instances(**kwargs)
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def get_accounts_and_regions_per_stack_set(self, stack_name):
        """
            List deployed stack instances for a stack set and returns the list
            of accounts and regions where the stack instances are deployed.
        :param stack_name: stack set name
        :return:
            list of accounts and regions where provided stack instances are
            deployed
        """
        try:
            response = self.cfn_client.list_stack_instances(
                StackSetName=stack_name,
                MaxResults=self.max_results_per_page
            )
            stack_instance_list = response.get('Summaries', [])
            # build the account and region list for the stack set
            # using list(set(LIST)) to remove the duplicate values from the list
            account_list = list(set([stack_instance['Account']
                                     for stack_instance
                                     in stack_instance_list]))
            region_list = list(set([stack_instance['Region']
                                    for stack_instance
                                    in stack_instance_list]))
            next_token = response.get('NextToken', None)

            while next_token is not None:
                self.logger.info("Next Token Returned: {}".format(next_token))
                response = self.cfn_client.list_stack_instances(
                    StackSetName=stack_name,
                    MaxResults=self.max_results_per_page,
                    NextToken=next_token
                )
                stack_instance_list = response.get('Summaries', [])
                next_token = response.get('NextToken', None)

                # update account and region lists
                additional_account_list = list(set([stack_instance['Account']
                                                    for stack_instance in
                                                    stack_instance_list]))
                additional_region_list = list(set([stack_instance['Region']
                                                   for stack_instance
                                                   in stack_instance_list]))
                account_list = account_list + additional_account_list
                region_list = region_list + additional_region_list
            return list(set(account_list)), list(set(region_list))
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def create_stack_set(self, stack_set_name, template_url,
                         cf_params, capabilities, tag_key, tag_value):
        try:
            parameters = []
            param_dict = {}
            for key, value in cf_params.items():
                """This condition checks if the value is a List and convert
                it into a Comma-delimited string. Note: Remember to change
                the parameter type from 'List<AWS::EC2::*::*>' (Supported
                AWS-Specific Parameter Types) to 'CommaDelimitedList' in the
                 template."""

                if type(value) == list:
                    value = ",".join(map(str, value))
                param_dict['ParameterKey'] = key
                param_dict['ParameterValue'] = value
                parameters.append(param_dict.copy())

            response = self.cfn_client.create_stack_set(
                StackSetName=stack_set_name,
                TemplateURL=template_url,
                Parameters=parameters,
                Capabilities=json.loads(capabilities),
                Tags=[
                    {
                        'Key': tag_key,
                        'Value': tag_value
                    },
                ],
                AdministrationRoleARN=os.environ.get(
                    'ADMINISTRATION_ROLE_ARN'),
                ExecutionRoleName=os.environ.get('EXECUTION_ROLE_NAME')
            )
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def create_stack_instances(self, stack_set_name, account_list, region_list):
        try:
            response = self.cfn_client.create_stack_instances(
                StackSetName=stack_set_name,
                Accounts=account_list,
                Regions=region_list,
                OperationPreferences={
                    'FailureTolerancePercentage': self.failed_tolerance_percent,
                    'MaxConcurrentPercentage': self.max_concurrent_percent,
                    'RegionConcurrencyType': self.region_concurrency_type
                }
            )
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'OperationInProgressException':
                self.logger.info(self.operation_in_progress_except_msg)
                return {"OperationId": "OperationInProgressException"}
            else:
                self.logger.log_unhandled_exception(e)
                raise

    def create_stack_instances_with_override_params(self, stack_set_name,
                                                    account_list, region_list,
                                                    override_params):
        try:
            parameters = []
            param_dict = {}
            for key, value in override_params.items():
                """This condition checks if the value is a List and convert
                it  into a Comma-delimited string. Note: Remember to change
                the parameter type from 'List<AWS::EC2::*::*>' (Supported
                AWS-Specific Parameter Types) to 'CommaDelimitedList' in the
                 template."""

                if type(value) == list:
                    value = ",".join(map(str, value))
                param_dict['ParameterKey'] = key
                param_dict['ParameterValue'] = value
                parameters.append(param_dict.copy())

            response = self.cfn_client.create_stack_instances(
                StackSetName=stack_set_name,
                Accounts=account_list,
                Regions=region_list,
                ParameterOverrides=parameters,
                OperationPreferences={
                    'FailureTolerancePercentage': self.failed_tolerance_percent,
                    'MaxConcurrentPercentage': self.max_concurrent_percent,
                    'RegionConcurrencyType': self.region_concurrency_type
                }
            )
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'OperationInProgressException':
                self.logger.info("Caught exception "
                                 "'OperationInProgressException', "
                                 "handling the exception...")
                return {"OperationId": "OperationInProgressException"}
            else:
                self.logger.log_unhandled_exception(e)
                raise

    def update_stack_instances(self, stack_set_name, account_list, region_list,
                               override_params):
        try:
            parameters = []
            param_dict = {}
            for key, value in override_params.items():
                """This condition checks if the value is a List and convert
                it into a Comma-delimited string. Note: Remember to change
                the parameter type from 'List<AWS::EC2::*::*>' (Supported
                AWS-Specific Parameter Types) to 'CommaDelimitedList' in
                 the template."""

                if type(value) == list:
                    value = ",".join(map(str, value))
                param_dict['ParameterKey'] = key
                param_dict['ParameterValue'] = value
                parameters.append(param_dict.copy())

            response = self.cfn_client.update_stack_instances(
                StackSetName=stack_set_name,
                Accounts=account_list,
                Regions=region_list,
                ParameterOverrides=parameters,
                OperationPreferences={
                    'FailureTolerancePercentage': self.failed_tolerance_percent,
                    'MaxConcurrentPercentage': self.max_concurrent_percent,
                    'RegionConcurrencyType': self.region_concurrency_type
                }
            )
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'OperationInProgressException':
                self.logger.info(self.operation_in_progress_except_msg)
                return {"OperationId": "OperationInProgressException"}
            else:
                self.logger.log_unhandled_exception(e)
                raise

    def update_stack_set(self, stack_set_name, parameter, template_url,
                         capabilities):
        try:
            parameters = []
            param_dict = {}
            for key, value in parameter.items():
                """This condition checks if the value is a List and convert
                it  into a Comma-delimited string. Note: Remember to change
                the parameter type from 'List<AWS::EC2::*::*>' (Supported
                AWS-Specific Parameter Types) to 'CommaDelimitedList' in the
                 template."""

                if type(value) == list:
                    value = ",".join(map(str, value))
                param_dict['ParameterKey'] = key
                param_dict['ParameterValue'] = value
                parameters.append(param_dict.copy())

            response = self.cfn_client.update_stack_set(
                StackSetName=stack_set_name,
                TemplateURL=template_url,
                Parameters=parameters,
                Capabilities=json.loads(capabilities),
                AdministrationRoleARN=os.environ.get(
                    'ADMINISTRATION_ROLE_ARN'),
                ExecutionRoleName=os.environ.get('EXECUTION_ROLE_NAME'),
                OperationPreferences={
                    'FailureTolerancePercentage': self.failed_tolerance_percent,
                    'MaxConcurrentPercentage': self.max_concurrent_percent,
                    'RegionConcurrencyType': self.region_concurrency_type
                }
            )
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'OperationInProgressException':
                self.logger.info(self.operation_in_progress_except_msg)
                return {"OperationId": "OperationInProgressException"}
            else:
                self.logger.log_unhandled_exception(e)
                raise

    def delete_stack_set(self, stack_set_name):
        try:
            response = self.cfn_client.delete_stack_set(
                StackSetName=stack_set_name,
            )
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def delete_stack_instances(self, stack_set_name, account_list, region_list,
                               retain_condition=False):
        try:
            response = self.cfn_client.delete_stack_instances(
                StackSetName=stack_set_name,
                Accounts=account_list,
                Regions=region_list,
                RetainStacks=retain_condition,
                OperationPreferences={
                    'FailureTolerancePercentage': self.failed_tolerance_percent,
                    'MaxConcurrentPercentage': self.max_concurrent_percent,
                    'RegionConcurrencyType': self.region_concurrency_type
                }
            )
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'OperationInProgressException':
                self.logger.info(self.operation_in_progress_except_msg)
                return {"OperationId": "OperationInProgressException"}
            else:
                self.logger.log_unhandled_exception(e)
                raise

    @try_except_retry()
    def describe_stack_instance(self, stack_set_name, account_id, region):
        try:
            response = self.cfn_client.describe_stack_instance(
                StackSetName=stack_set_name,
                StackInstanceAccount=account_id,
                StackInstanceRegion=region
            )
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    @try_except_retry()
    def list_stack_set_operations(self, **kwargs):
        try:
            response = self.cfn_client.list_stack_set_operations(**kwargs)
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def _filter_managed_stack_set_names(self, list_stackset_response: Dict[str, Any]) -> List[str]:
        """
        Reduces a list of given stackset summaries to only those considered managed by CfCT
        """
        managed_stack_set_names: List[str] = []
        for summary in list_stackset_response['Summaries']:
            stack_set_name = summary['StackSetName']
            try:
                response: Dict[str, Any] = self.cfn_client.describe_stack_set(StackSetName=stack_set_name)
            except ClientError as error:
                if error.response['Error']['Code'] == "StackSetNotFoundException":
                    continue
                raise

            if self.is_managed_by_cfct(describe_stackset_response=response):
                managed_stack_set_names.append(stack_set_name)
        
        return managed_stack_set_names

    def get_managed_stack_set_names(self) -> List[str]:
        """
        Discovers all StackSets prefixed with 'CustomControlTower-' and that
        have the tag {Key: AWS_Solutions, Value: CustomControlTowerStackSet}
        """

        managed_stackset_names: List[str] = []
        paginator = self.cfn_client.get_paginator("list_stack_sets")
        for page in paginator.paginate(Status="ACTIVE"):
            managed_stackset_names.extend(self._filter_managed_stack_set_names(list_stackset_response=page))
        return managed_stackset_names

    def is_managed_by_cfct(self, describe_stackset_response: Dict[str, Any]) -> bool:
        """
        A StackSet is considered managed if it has both the prefix we expect, and the proper tag
        """
        
        has_tag = StackSet.DEPLOYED_BY_CFCT_TAG in describe_stackset_response['StackSet']['Tags']
        has_prefix = describe_stackset_response['StackSet']['StackSetName'].startswith(StackSet.CFCT_STACK_SET_PREFIX)
        is_active = describe_stackset_response['StackSet']['Status'] == "ACTIVE"
        return all((has_prefix, has_tag, is_active))

    def get_stack_sets_not_present_in_manifest(self, manifest_stack_sets: List[str]) -> List[str]:
        """
        Compares list of stacksets defined in the manifest versus the stacksets in the account
        and returns a list of all stackset names to be deleted
        """

        # Stack sets defined in the manifest will not have the CFCT_STACK_SET_PREFIX
        # To make comparisons simpler
        manifest_stack_sets_with_prefix = [f"{StackSet.CFCT_STACK_SET_PREFIX}{name}" for name in manifest_stack_sets]
        cfct_deployed_stack_sets = self.get_managed_stack_set_names()
        return list(set(cfct_deployed_stack_sets).difference(set(manifest_stack_sets_with_prefix)))

    def generate_delete_request(self, stacksets_to_delete: List[str]) -> List[StackSetRequestTypeDef]:
        requests: List[StackSetRequestTypeDef] = []
        for stackset_name in stacksets_to_delete:
            deployed_instances = self._get_stackset_instances(stackset_name=stackset_name)
            requests.append(StackSetRequestTypeDef(
                RequestType="Delete",
                ResourceProperties=ResourcePropertiesTypeDef(
                    StackSetName=stackset_name,
                    TemplateURL="DeleteStackSetNoopURL",
                    Capabilities=json.dumps(["CAPABILITY_NAMED_IAM", "CAPABILITY_AUTO_EXPAND"]),
                    Parameters={},
                    AccountList=list({instance['account'] for instance in deployed_instances}),
                    RegionList=list({instance['region'] for instance in deployed_instances}),
                    SSMParameters={}
                ),
                SkipUpdateStackSet="yes",
            ))
        return requests


    def _get_stackset_instances(self, stackset_name: str) -> List[StackSetInstanceTypeDef]:
        instance_regions_and_accounts: List[StackSetInstanceTypeDef] = []
        paginator = self.cfn_client.get_paginator("list_stack_instances")
        for page in paginator.paginate(StackSetName=stackset_name):
            for summary in page['Summaries']:
                instance_regions_and_accounts.append(StackSetInstanceTypeDef(
                    account=summary['Account'],
                    region=summary['Region'],
                ))

        return instance_regions_and_accounts


class Stacks(Boto3Session):
    def __init__(self, logger, region, **kwargs):
        self.logger = logger
        __service_name = 'cloudformation'
        kwargs.update({'region': region})
        super().__init__(logger, __service_name, **kwargs)
        self.cfn_client = super().get_client()

    @try_except_retry()
    def describe_stacks(self, stack_name):
        try:
            response = self.cfn_client.describe_stacks(
                StackName=stack_name
            )
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise
