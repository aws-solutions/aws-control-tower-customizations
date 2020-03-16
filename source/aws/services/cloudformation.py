##############################################################################
#  Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.   #
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
from utils.retry_decorator import try_except_retry
from aws.utils.boto3_session import Boto3Session


class StackSet(Boto3Session):
    def __init__(self, logger, **kwargs):
        self.logger = logger
        __service_name = 'cloudformation'
        super().__init__(logger, __service_name, **kwargs)
        self.cfn_client = super().get_client()
        self.operation_in_prog_except_msg =  \
            'Caught exception OperationInProgressException'  \
            ' handling the exception...'

    def describe_stack_set(self, stack_set_name):
        try:
            response = self.cfn_client.describe_stack_set(
                StackSetName=stack_set_name
            )
            return response
        except Exception:
            pass

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

    def list_stack_instances(self, **kwargs):
        try:
            response = self.cfn_client.list_stack_instances(**kwargs)
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def list_stack_instances_per_account(self, stack_name,
                                         account_id,
                                         max_results=20):
        try:
            response = self.cfn_client.list_stack_instances(
                StackSetName=stack_name,
                StackInstanceAccount=account_id,
                MaxResults=max_results
            )
            stack_instance_list = response.get('Summaries', [])
            next_token = response.get('NextToken', None)

            while next_token is not None:
                self.logger.info("Next Token Returned: {}".format(next_token))
                self.cfn_client.list_stack_instances(
                    StackSetName=stack_name,
                    StackInstanceAccount=account_id,
                    MaxResults=max_results,
                    NextToken=next_token
                )
                self.logger.info("Extending Stack Instance List")
                stack_instance_list.extend(response.get('Summaries', []))
                next_token = response.get('NextToken', None)
            return stack_instance_list
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
                Capabilities=[capabilities],
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

    def create_stack_instances(self, stack_set_name, account_list, region_list,
                               failed_tolerance_percent=0,
                               max_concurrent_percent=100):
        try:
            response = self.cfn_client.create_stack_instances(
                StackSetName=stack_set_name,
                Accounts=account_list,
                Regions=region_list,
                OperationPreferences={
                    'FailureTolerancePercentage': failed_tolerance_percent,
                    'MaxConcurrentPercentage': max_concurrent_percent
                }
            )
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'OperationInProgressException':
                self.logger.info(self.operation_in_prog_except_msg)
                return {"OperationId": "OperationInProgressException"}
            else:
                self.logger.log_unhandled_exception(e)
                raise

    def create_stack_instances_with_override_params(
        self, stack_set_name, account_list, region_list,
        override_params, failed_tolerance_percent=0,
            max_concurrent_percent=100):
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
                    'FailureTolerancePercentage': failed_tolerance_percent,
                    'MaxConcurrentPercentage': max_concurrent_percent
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
                               override_params,
                               failed_tolerance_percent=0,
                               max_concurrent_percent=100):
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
                    'FailureTolerancePercentage': failed_tolerance_percent,
                    'MaxConcurrentPercentage': max_concurrent_percent
                }
            )
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'OperationInProgressException':
                self.logger.info(self.operation_in_prog_except_msg)
                return {"OperationId": "OperationInProgressException"}
            else:
                self.logger.log_unhandled_exception(e)
                raise

    def update_stack_set(self, stack_set_name, parameter, template_url,
                         capabilities, failed_tolerance_percent=0,
                         max_concurrent_percent=100):
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
                Capabilities=[capabilities],
                AdministrationRoleARN=os.environ.get(
                    'ADMINISTRATION_ROLE_ARN'),
                ExecutionRoleName=os.environ.get('EXECUTION_ROLE_NAME'),
                OperationPreferences={
                    'FailureTolerancePercentage': failed_tolerance_percent,
                    'MaxConcurrentPercentage': max_concurrent_percent
                }
            )
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'OperationInProgressException':
                self.logger.info(self.operation_in_prog_except_msg)
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
                               retain_condition=False,
                               failed_tolerance_percent=0,
                               max_concurrent_percent=100):
        try:
            response = self.cfn_client.delete_stack_instances(
                StackSetName=stack_set_name,
                Accounts=account_list,
                Regions=region_list,
                RetainStacks=retain_condition,
                OperationPreferences={
                    'FailureTolerancePercentage': failed_tolerance_percent,
                    'MaxConcurrentPercentage': max_concurrent_percent
                }
            )
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'OperationInProgressException':
                self.logger.info(self.operation_in_prog_except_msg)
                return {"OperationId": "OperationInProgressException"}
            else:
                self.logger.log_unhandled_exception(e)
                raise

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

    def list_stack_set_operations(self, **kwargs):
        try:
            response = self.cfn_client.list_stack_set_operations(**kwargs)
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise


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
