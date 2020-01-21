######################################################################################################################
#  Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.                                           #
#                                                                                                                    #
#  Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance        #
#  with the License. A copy of the License is located at                                                             #
#                                                                                                                    #
#      http://www.apache.org/licenses/LICENSE-2.0                                                                                    #
#                                                                                                                    #
#  or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES #
#  OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions    #
#  and limitations under the License.                                                                                #
######################################################################################################################

# !/bin/python

from lib.organizations import Organizations as Org
from lib.scp import ServiceControlPolicy as SCP
from lib.cloudformation import StackSet, Stacks
from lib.assume_role_helper import AssumeRole
from lib.metrics import Metrics
from lib.ssm import SSM
from lib.ec2 import EC2
from lib.sts import STS
from os import environ
import requests
from botocore.exceptions import ClientError
from json import dumps
import inspect
import os
import json
from lib.helper import convert_http_url_to_s3_url, download_remote_file
import time
from random import randint


class CloudFormation(object):
    """
    This class handles requests from Cloudformation (StackSet) State Machine.
    """

    def __init__(self, event, logger):
        self.event = event
        self.params = event.get('ResourceProperties')
        self.logger = logger
        self.logger.info(self.__class__.__name__ + " Class Event")
        self.logger.info(event)

    def describe_stack_set(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)

            # add loop flag to handle Skip StackSet Update choice
            if self.event.get('LoopFlag') is None:
                self.event.update({'LoopFlag': 'not-applicable'})

            # To prevent CFN from throwing 'Response object is too long.' when the event payload gets overloaded
            # Deleting the 'OldResourceProperties' from event, since it not being used in the SM

            if self.event.get('OldResourceProperties'):
                self.event.pop('OldResourceProperties', '')

            # Check if stack set already exist
            stack_set = StackSet(self.logger)
            response = stack_set.describe_stack_set(self.params.get('StackSetName'))
            self.logger.info("Describe Response")
            self.logger.info(response)
            # If stack_set already exist, skip to create the stack_set_instance
            if response is not None:
                value = "yes"
                self.logger.info("Found existing stack set.")
            else:
                value = "no"
                self.logger.info("Existing stack set not found.")
            self.event.update({'StackSetExist': value})
            return self.event
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def describe_stack_set_operation(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)
            self.event.update({'RetryDeleteFlag': False})

            stack_set = StackSet(self.logger)
            response = stack_set.describe_stack_set_operation(self.params.get('StackSetName'),
                                                              self.event.get('OperationId'))
            self.logger.info(response)
            operation_status = response.get('StackSetOperation', {}).get('Status')
            self.logger.info("Operation Status: {}".format(operation_status))
            if operation_status == 'FAILED':
                account_id = self.params.get('AccountList')[0] if type(self.params.get('AccountList')) is list else None
                if account_id:
                    for region in self.params.get('RegionList'):
                        self.logger.info("Account: {} - describing stack instance in {} region".format(account_id, region))
                        try:
                            resp = stack_set.describe_stack_instance(self.params.get('StackSetName'), account_id, region)
                            self.event.update({region: resp.get('StackInstance', {}).get('StatusReason')})
                        except ClientError as e:
                            # When CFN has triggered StackInstance delete and the SCP is still attached (due to race condition), then it fails to delete the stack
                            # and StackSet throws the StackInstanceNotFoundException exception back, the CFN stack in target account ends up with 'DELETE_FAILED' state
                            # so it should try again
                            if e.response['Error']['Code'] == 'StackInstanceNotFoundException' and self.event.get('RequestType') == 'Delete':
                                self.logger.exception("Caught exception 'StackInstanceNotFoundException', sending the flag to go back to Delete Stack Instances stage...")
                                self.event.update({'RetryDeleteFlag': True})
                            else:
                                message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
                                self.logger.exception(message)
                                raise


            operation_status = response.get('StackSetOperation', {}).get('Status')
            self.event.update({'OperationStatus': operation_status})

            return self.event
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def list_stack_instances_account_ids(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)

            if self.event.get('NextToken') is None or self.event.get('NextToken') == 'Complete':
                accounts = []
            else:
                accounts = self.event.get('StackInstanceAccountList', [])

            # Check if stack instances exist
            stack_set = StackSet(self.logger)
            if self.event.get('NextToken') is not None and self.event.get('NextToken') != 'Complete':
                response = stack_set.list_stack_instances(StackSetName=self.params.get('StackSetName'), MaxResults=20,
                                                          NextToken=self.event.get('NextToken'))
            else:
                response = stack_set.list_stack_instances(StackSetName=self.params.get('StackSetName'), MaxResults=20)

            self.logger.info("List SI Accounts Response")
            self.logger.info(response)

            if response:
                if not response.get('Summaries'):  # 'True' if list is empty
                    self.event.update({'NextToken': 'Complete'})
                    self.logger.info("No existing stack instances found. (Summaries List: Empty)")
                else:
                    for instance in response.get('Summaries'):
                        account_id = instance.get('Account')
                        accounts.append(account_id)
                    self.event.update({'StackInstanceAccountList': list(set(accounts))})
                    self.logger.info("Next Token Returned: {}".format(response.get('NextToken')))

                    if response.get('NextToken') is None:
                        self.event.update({'NextToken': 'Complete'})
                    else:
                        self.event.update({'NextToken': response.get('NextToken')})

            return self.event
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def list_stack_instances(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)

            if 'ParameterOverrides' in self.params.keys():
                self.logger.info("Override parameters found in the event")
                self.event.update({'OverrideParametersExist': 'yes'})
            else:
                self.logger.info("Override parameters NOT found in the event")
                self.event.update({'OverrideParametersExist': 'no'})

            # Check if stack instances exist
            stack_set = StackSet(self.logger)
            # if account list is not present then only create StackSet and skip stack instance creation
            if type(self.params.get('AccountList')) is not list:
                self.event.update({'InstanceExist': 'no'})
                self.event.update({'NextToken': 'Complete'})
                self.event.update({'CreateInstance': 'no'})
                self.event.update({'DeleteInstance': 'no'})
                return self.event
            else:
                if self.event.get('NextToken') is not None and self.event.get('NextToken') != 'Complete':
                    self.logger.info('Found next token')
                    response = stack_set.list_stack_instances(StackSetName=self.params.get('StackSetName'),
                                                              StackInstanceAccount=self.params.get('AccountList')[0],
                                                              MaxResults=20,
                                                              NextToken=self.event.get('NextToken')
                                                              )
                else:
                    self.logger.info('Next token not found.')
                    response = stack_set.list_stack_instances(StackSetName=self.params.get('StackSetName'),
                                                              StackInstanceAccount=self.params.get('AccountList')[0],
                                                              MaxResults = 20)
                self.logger.info("List SI Response")
                self.logger.info(response)

                if response is not None:
                    if not response.get('Summaries'):  # 'True' if list is empty
                        self.event.update({'InstanceExist': 'no'})
                        self.event.update({'NextToken': 'Complete'}) # exit loop
                        self.event.update({'CreateInstance': 'yes'}) # create stack instance set to yes
                        self.event.update({'DeleteInstance': 'no'})  # delete stack instance set to no
                        self.logger.info("No existing stack instances found. (Summaries List: Empty)")
                        return self.event
                    else:
                        self.logger.info("Found existing stack instance.")
                        # Delete path in SM, will skip StackSet deletion if InstanceExist is 'yes'
                        self.event.update({'InstanceExist': 'yes'})
                        # Iterate through response to check if stack instance exists in
                        # account and region in the given self.event.
                        account_id = ""
                        existing_region_list = [] if self.event.get('ExistingRegionList') is None else self.event.get(
                            'ExistingRegionList')
                        existing_account_list = [] if self.event.get('StackInstanceAccountList') is None \
                            else self.event.get('StackInstanceAccountList')
                        for instance in response.get('Summaries'):
                            if instance.get('Region') not in existing_region_list:
                                self.logger.info("Region {} not in the region list. Adding it..."
                                                 .format(instance.get('Region')))
                                # appending to the list
                                existing_region_list.append(instance.get('Region'))
                            else:
                                self.logger.info("Already in the region list. Skipping...")
                            account_id = instance.get('Account')

                        self.logger.info("Region List: {} for Account: {}".format(existing_region_list, account_id))

                        self.logger.info("Next Token Returned: {}".format(response.get('NextToken')))

                        if response.get('NextToken') is None:
                            # replace the region list in the self.event
                            add_region_list = self._add_list(self.params.get('RegionList'), existing_region_list)
                            self.logger.info("Add region list: {}".format(add_region_list))

                            # Build a region list if the event is from AVM
                            delete_region_list = self._delete_list(self.params.get('RegionList'), existing_region_list)
                            self.logger.info("Delete region list: {}".format(delete_region_list))

                            add_account_list = self._add_list(self.params.get('AccountList'), existing_account_list)
                            self.logger.info("Add account list: {}".format(add_account_list))

                            delete_account_list = self._delete_list(self.params.get('AccountList'), existing_account_list)
                            self.logger.info("Delete account list: {}".format(delete_account_list))

                            if add_account_list and add_region_list: # both are not empty - region and account was added
                                self.event.update({'LoopFlag': 'yes'})
                            elif delete_account_list and delete_region_list: # both are not empty - region and account was delete
                                self.event.update({'LoopFlag': 'yes'})
                            else:
                                self.event.update({'LoopFlag': 'no'})

                            self._update_event_for_add(add_account_list, add_region_list)
                            self._update_event_for_delete(delete_account_list, delete_region_list)
                            self.event.update({'ExistingRegionList': existing_region_list})
                        else:
                            self.event.update({'NextToken': response.get('NextToken')})
                            # Update the self.event with existing_region_list
                            self.event.update({'ExistingRegionList': existing_region_list})
                        return self.event
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def _update_event_for_delete(self, delete_account_list, delete_region_list):
        if delete_account_list or delete_region_list:
            self.event.update({'DeleteAccountList': delete_account_list})
            self.event.update({'DeleteRegionList': delete_region_list})
            self.event.update({'DeleteInstance': 'yes'})
            self.event.update({'NextToken': 'Complete'})
        else:
            self.event.update({'DeleteInstance': 'no'})
            self.event.update({'NextToken': 'Complete'})

    def _update_event_for_add(self, add_account_list, add_region_list):
        if add_account_list or add_region_list:
            self.event.update({'AddAccountList': add_account_list})
            self.event.update({'AddRegionList': add_region_list})
            self.event.update({'CreateInstance': 'yes'})
            self.event.update({'NextToken': 'Complete'})
        else:
            self.event.update({'CreateInstance': 'no'})
            self.event.update({'NextToken': 'Complete'})

    def _add_list(self, new_list, existing_list):
        event_set = set(new_list)
        existing_set = set(existing_list)
        add_list = list(event_set - event_set.intersection(existing_set))
        return add_list

    def _delete_list(self, new_list, existing_list):
        event_set = set(new_list)
        existing_set = set(existing_list)
        delete_list = list(event_set.union(existing_set) - event_set)
        return delete_list

    def _get_ssm_secure_string(self, parameters):
        if parameters.get('ALZRegion'):
            ssm = SSM(self.logger, parameters.get('ALZRegion'))
        else:
            ssm = SSM(self.logger)

        self.logger.info("Updating Parameters")
        self.logger.info(parameters)
        copy = parameters.copy()
        for key, value in copy.items():
            if type(value) is str and value.startswith('_get_ssm_secure_string_'):
                ssm_param_key = value[len('_get_ssm_secure_string_'):]
                decrypted_value = ssm.get_parameter(ssm_param_key)
                copy.update({key: decrypted_value})
            elif type(value) is str and value.startswith('_alfred_decapsulation_'):
                decapsulated_value = value[(len('_alfred_decapsulation_')+1):]
                self.logger.info("Removing decapsulation header. Printing decapsulated value below:")
                copy.update({key: decapsulated_value})
        return copy

    def create_stack_set(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)

            # Create a new stack set
            stack_set = StackSet(self.logger)
            self.logger.info("Creating StackSet")
            parameters = self._get_ssm_secure_string(self.params.get('Parameters'))
            response = stack_set.create_stack_set(self.params.get('StackSetName'),
                                                  self.params.get('TemplateURL'),
                                                  parameters,
                                                  self.params.get('Capabilities'))
            if response.get('StackSetId') is not None:
                value = "success"
            else:
                value = "failure"
            self.event.update({'StackSetStatus': value})
            # set create stack instance flag to yes (Handle SM Condition: Create or Delete Stack Instance?)
            self.event.update({'CreateInstance': 'yes'})
            # set delete stack instance flag to no (Handle SM Condition: Delete Stack Instance or Finish?)
            self.event.update({'DeleteInstance': 'no'})
            return self.event
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def create_stack_instances(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)

            # Create stack instances
            stack_set = StackSet(self.logger)
            # set to default values (new instance creation)
            account_list = self.params.get('AccountList')
            region_list = self.params.get('RegionList')

            # if AddAccountList is not empty
            if self.event.get('AddAccountList') is not None:
                if len(self.event.get('AddAccountList')) != 0:
                    account_list = self.event.get('AddAccountList')

            # if AddRegionList is not empty
            if self.event.get('AddRegionList') is not None:
                if len(self.event.get('AddRegionList')) != 0:
                    region_list = self.event.get('AddRegionList')

            if self.event.get('LoopFlag') == 'yes': # both  AddAccountList and AddRegionList is not empty
                # create new stack instance in new account only with all regions
                # new stack instances in new region for existing accounts will be deployed in the second round
                account_list = self.event.get('AddAccountList')
                region_list = self.params.get('RegionList')

            self.event.update({'ActiveAccountList': account_list})
            self.event.update({'ActiveRegionList': region_list})

            self.logger.info("Creating StackSet Instance: {}".format(self.params.get('StackSetName')))
            if 'ParameterOverrides' in self.params:
                self.logger.info("Found 'ParameterOverrides' key in the event.")
                parameters = self._get_ssm_secure_string(self.params.get('ParameterOverrides'))
                response = stack_set.create_stack_instances_with_override_params(self.params.get('StackSetName'),
                                                                                 account_list,
                                                                                 region_list,
                                                                                 parameters)
            else:
                response = stack_set.create_stack_instances(self.params.get('StackSetName'),
                                                            account_list,
                                                            region_list)
            self.logger.info(response)
            self.logger.info("Operation ID: {}".format(response.get('OperationId')))
            self.event.update({'OperationId': response.get('OperationId')})
            return self.event
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def update_stack_set(self):
        # Updates the stack set and all associated stack instances.
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)
            stack_set = StackSet(self.logger)

            # Update existing StackSet
            self.logger.info("Updating Stack Set: {}".format(self.params.get('StackSetName')))

            parameters = self._get_ssm_secure_string(self.params.get('Parameters'))
            response = stack_set.update_stack_set(self.params.get('StackSetName'),
                                                  parameters,
                                                  self.params.get('TemplateURL'),
                                                  self.params.get('Capabilities'))

            self.logger.info("Response Update Stack Set")
            self.logger.info(response)
            self.logger.info("Operation ID: {}".format(response.get('OperationId')))
            self.event.update({'OperationId': response.get('OperationId')})
            return self.event
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def update_stack_instances(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)

            stack_set = StackSet(self.logger)
            override_parameters = self.params.get('ParameterOverrides') # this should come from the event
            self.logger.info("override_params_list={}".format(override_parameters))

            response = stack_set.update_stack_instances(self.params.get('StackSetName'),
                                                        self.params.get('AccountList'),
                                                        self.params.get('RegionList'),
                                                        override_parameters)
            self.logger.info("Update Stack Instance Response")
            self.logger.info(response)
            self.logger.info("Operation ID: {}".format(response.get('OperationId')))
            self.event.update({'OperationId': response.get('OperationId')})
            # need for Delete Stack Instance or Finish? choice in the state machine. No will route to Finish path.
            self.event.update({'DeleteInstance': 'no'})
            return self.event

        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def delete_stack_set(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)
            # Delete StackSet
            stack_set = StackSet(self.logger)
            self.logger.info("Deleting StackSet: {}".format(self.params.get('StackSetName')))
            self.logger.info(stack_set.delete_stack_set(self.params.get('StackSetName')))
            return self.event
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def delete_stack_instances(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)

            # set to default values (new instance creation)
            account_list = self.params.get('AccountList')
            region_list = self.event.get('ExistingRegionList') # full region list

            # if AddAccountList is not empty
            if self.event.get('DeleteAccountList') is not None:
                if len(self.event.get('DeleteAccountList')) != 0:
                    account_list = self.event.get('DeleteAccountList')

            # if AddRegionList is not empty
            if self.event.get('DeleteRegionList') is not None:
                if len(self.event.get('DeleteRegionList')) != 0:
                    region_list = self.event.get('DeleteRegionList')

            if self.event.get('LoopFlag') == 'yes':  # both  DeleteAccountList and DeleteRegionList is not empty
                # delete stack instance in deleted account with all regions
                # stack instances in all regions for existing accounts will be deletion in the second round
                account_list = self.event.get('DeleteAccountList')
                region_list = self.event.get('ExistingRegionList') # full region list

            self.event.update({'ActiveAccountList': account_list})
            self.event.update({'ActiveRegionList': region_list})

            # Delete stack_set_instance(s)
            stack_set = StackSet(self.logger)
            self.logger.info("Deleting Stack Instance: {}".format(self.params.get('StackSetName')))

            response = stack_set.delete_stack_instances(self.params.get('StackSetName'),
                                                        account_list,
                                                        region_list)
            self.logger.info(response)
            self.logger.info("Operation ID: {}".format(response.get('OperationId')))
            self.event.update({'OperationId': response.get('OperationId')})
            return self.event
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise


class ServiceControlPolicy(object):
    """
    This class handles requests from Service Control Policy State Machine.
    """

    def __init__(self, event, logger):
        self.event = event
        self.params = event.get('ResourceProperties')
        self.logger = logger
        self.logger.info(self.__class__.__name__ + " Class Event")
        self.logger.info(event)

    def _load_policy(self, relative_policy_path):
        policy_file = download_remote_file(self.logger, relative_policy_path)

        self.logger.info("Parsing the policy file: {}".format(policy_file))

        with open(policy_file, 'r') as content_file:
            policy_file_content = content_file.read()

        #Check if valid json
        json.loads(policy_file_content)
        #Return the Escaped JSON text
        return policy_file_content.replace('"', '\"').replace('\n', '\r\n').replace(" ", "")


    def list_policies(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)
            # Check if PolicyName attribute exists in event, if so, it is called for attach or detach policy
            if 'PolicyName' in self.event:
                policy_name = self.event.get('PolicyName')
            else:
                policy_name = self.params.get('PolicyDocument').get('Name')

            # Check if SCP already exist
            scp = SCP(self.logger)
            pages = scp.list_policies()

            for page in pages:
                policies_list = page.get('Policies')

                # iterate through the policies list
                for policy in policies_list:
                    if policy.get('Name') == policy_name:
                        self.logger.info("Policy Found")
                        self.event.update({'PolicyId': policy.get('Id')})
                        self.event.update({'PolicyArn': policy.get('Arn')})
                        self.event.update({'PolicyExist': "yes"})
                        return self.event
                    else:
                        continue

            self.event.update({'PolicyExist': "no"})
            return self.event
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def create_policy(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)
            policy_doc = self.params.get('PolicyDocument')

            scp = SCP(self.logger)
            self.logger.info("Creating Service Control Policy")
            policy_s3_url = convert_http_url_to_s3_url(policy_doc.get('PolicyURL'))
            policy_content = self._load_policy(policy_s3_url)

            response = scp.create_policy(policy_doc.get('Name'),
                                         policy_doc.get('Description'),
                                         policy_content)
            self.logger.info("Create SCP Response")
            self.logger.info(response)
            policy_id = response.get('Policy').get('PolicySummary').get('Id')
            self.event.update({'PolicyId': policy_id})
            return self.event

        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def update_policy(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)
            policy_doc = self.params.get('PolicyDocument')
            policy_id = self.event.get('PolicyId')
            policy_s3_url = convert_http_url_to_s3_url(policy_doc.get('PolicyURL'))
            policy_content = self._load_policy(policy_s3_url)

            scp = SCP(self.logger)
            self.logger.info("Updating Service Control Policy")
            response = scp.update_policy(policy_id, policy_doc.get('Name'),
                                         policy_doc.get('Description'),
                                         policy_content)
            self.logger.info("Update SCP Response")
            self.logger.info(response)
            policy_id = response.get('Policy').get('PolicySummary').get('Id')
            self.event.update({'PolicyId': policy_id})
            return self.event

        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def delete_policy(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)
            policy_id = self.event.get('PolicyId')

            scp = SCP(self.logger)
            self.logger.info("Deleting Service Control Policy")
            response = scp.delete_policy(policy_id)
            self.logger.info("Delete SCP Response")
            self.logger.info(response)
            status = 'Policy: {} deleted successfully'.format(policy_id)
            self.event.update({'Status': status})
            return self.event

        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def attach_policy(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)
            if self.params.get('AccountId') == "":
                target_id = self.event.get('OUId')
            else:
                target_id = self.params.get('AccountId')
            policy_id = self.event.get('PolicyId')
            scp = SCP(self.logger)
            response = scp.attach_policy(policy_id, target_id)
            self.logger.info("Attach Policy Response")
            self.logger.info(response)
            status = 'Policy: {} attached successfully to Target: {}'.format(policy_id, target_id)
            self.event.update({'Status': status})
            return self.event

        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def detach_policy(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)
            if self.params.get('AccountId') == "":
                target_id = self.event.get('OUId')
            else:
                target_id = self.params.get('AccountId')
            policy_id = self.event.get('PolicyId')
            scp = SCP(self.logger)
            response = scp.detach_policy(policy_id, target_id)
            self.logger.info("Detach Policy Response")
            self.logger.info(response)
            status = 'Policy: {} detached successfully from Target: {}'.format(policy_id, target_id)
            self.event.update({'Status': status})
            return self.event

        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def _strip_list_items(self, array):
        return [item.strip() for item in array]

    def _remove_empty_strings(self, array):
        return [x for x in array if x != '']

    def _list_sanitizer(self, array):
        stripped_array = self._strip_list_items(array)
        return self._remove_empty_strings(stripped_array)

    def _empty_seperator_handler(self, delimiter, nested_ou_name):
        if delimiter == "":
            nested_ou_name_list = [nested_ou_name]
        else:
            nested_ou_name_list = nested_ou_name.split(delimiter)
        return nested_ou_name_list

    def get_ou_id(self, nested_ou_name, delimiter):
        try:
            org = Org(self.logger)
            response = org.list_roots()
            root_id = response['Roots'][0].get('Id')
            self.logger.info("Organizations Root Id: {}".format(root_id))
            self.logger.info("Looking up the OU Id for OUName: {} with nested ou delimiter: {}".format(nested_ou_name, delimiter))
            return self._get_ou_id(org, root_id, nested_ou_name, delimiter)
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def _get_ou_id(self, org, parent_id, nested_ou_name, delimiter):
        try:
            nested_ou_name_list = self._empty_seperator_handler(delimiter, nested_ou_name)
            response = self._list_ou_for_parent(org, parent_id, self._list_sanitizer(nested_ou_name_list))
            self.logger.info(response)
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def _list_ou_for_parent(self, org, parent_id, nested_ou_name_list):
        try:
            ou_list = org.list_organizational_units_for_parent(parent_id)
            index = 0  # always process the first item
            self.logger.info("Looking for existing OU: {} under parent id: {}".format(nested_ou_name_list[index], parent_id))
            for dictionary in ou_list:
                if dictionary.get('Name') == nested_ou_name_list[index]:
                    self.logger.info("OU Name: {} exists under parent id: {}".format(dictionary.get('Name'), parent_id))
                    nested_ou_name_list.pop(index) # pop the first item in the list
                    if len(nested_ou_name_list) == 0:
                        self.logger.info("Returning last level OU ID: {}".format(dictionary.get('Id')))
                        return dictionary.get('Id')
                    else:
                        return self._list_ou_for_parent(org, dictionary.get('Id'), nested_ou_name_list)
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def list_policies_for_ou(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)
            ou_name = self.event.get('OUName')
            delimiter = self.params.get('OUNameDelimiter')
            policy_name = self.params.get('PolicyDocument').get('Name')

            # Check if SCP already exist
            scp = SCP(self.logger)

            ou_id = self.get_ou_id(ou_name, delimiter)
            self.event.update({'OUId': ou_id})
            pages = scp.list_policies_for_target(ou_id)

            for page in pages:
                policies_list = page.get('Policies')

                # iterate through the policies list
                for policy in policies_list:
                    if policy.get('Name') == policy_name:
                        self.logger.info("Policy Found")
                        self.event.update({'PolicyId': policy.get('Id')})
                        self.event.update({'PolicyArn': policy.get('Arn')})
                        self.event.update({'PolicyAttached': "yes"})
                        return self.event
                    else:
                        continue

            self.event.update({'PolicyAttached': "no"})
            return self.event
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def list_policies_for_account(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)
            account_id = self.params.get('AccountId')
            policy_name = self.event.get('PolicyName')

            # Check if SCP already exist
            scp = SCP(self.logger)
            pages = scp.list_policies_for_target(account_id)

            for page in pages:
                policies_list = page.get('Policies')

                # iterate through the policies list
                for policy in policies_list:
                    if policy.get('Name') == policy_name:
                        self.logger.info("Policy Found")
                        self.event.update({'PolicyId': policy.get('Id')})
                        self.event.update({'PolicyArn': policy.get('Arn')})
                        self.event.update({'PolicyAttached': "yes"})
                        return self.event
                    else:
                        continue

            self.event.update({'PolicyAttached': "no"})
            return self.event
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def detach_policy_from_all_accounts(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)
            policy_id = self.event.get('PolicyId')
            scp = SCP(self.logger)

            pages = scp.list_targets_for_policy(policy_id)
            accounts = []

            for page in pages:
                target_list = page.get('Targets')

                # iterate through the policies list
                for target in target_list:
                    account_id = target.get('TargetId')
                    scp.detach_policy(policy_id, account_id)
                    accounts.append(account_id)

            status = 'Policy: {} detached successfully from Accounts: {}'.format(policy_id, accounts)
            self.event.update({'Status': status})
            return self.event

        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def enable_policy_type(self):
        try:
            org = Org(self.logger)
            response = org.list_roots()
            self.logger.info("List roots Response")
            self.logger.info(response)
            root_id = response['Roots'][0].get('Id')

            scp = SCP(self.logger)
            scp.enable_policy_type(root_id)
            return self.event
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise


class GeneralFunctions(object):
    """
    This class handles requests from Cloudformation (StackSet) State Machine.
    """

    def __init__(self, event, logger):
        self.event = event
        self.params = event.get('ResourceProperties')
        self.logger = logger
        self.logger.info(self.__class__.__name__ + " Class Event")
        self.logger.info(event)

    def export_cfn_output(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)

            regions = self.params.get('RegionList')
            accounts = self.params.get('AccountList')
            stack_set_name = self.params.get('StackSetName')
            stack_set = StackSet(self.logger)

            if len(accounts) == 0 or len(regions) == 0:
                self.logger.info("Either AccountList or RegionList empty; so skipping the export_cfn_output ")
                return self.event

            self.logger.info("Picking the first account from AccountList")
            account = accounts[0]

            self.logger.info("Picking the first region from RegionList")
            region = regions[0]

            # First retrieve the Stack ID from the target account, region deployed via the StackSet
            response = stack_set.describe_stack_instance(stack_set_name, account, region)

            stack_id = response.get('StackInstance').get('StackId')
            self.logger.info("stack_id={}".format(stack_id))
            if stack_id:
                stack_name = stack_id.split('/')[1]
            else:
                raise Exception("Describe Stack Instance failed to retrieve the StackId for StackSet: {} in account: {} and region: {}".format(stack_set_name, account, region))
            self.logger.info("stack_name={}".format(stack_name))

            # instantiate STS class
            _assume_role = AssumeRole()
            cfn = Stacks(self.logger, credentials=_assume_role(self.logger, account), region=region)

            response = cfn.describe_stacks(stack_name)
            stacks = response.get('Stacks')

            if stacks is not None and type(stacks) is list:
                for stack in stacks:
                    if stack.get('StackId') == stack_id:
                        self.logger.info("Found Stack: {}".format(stack.get('StackName')))
                        self.logger.info("Exporting Output of Stack: {} from Account: {} and region: {}"
                                         .format(stack.get('StackName'), str(account), region))
                        outputs = stack.get('Outputs')
                        if outputs is not None and type(outputs) is list:
                            for output in outputs:
                                key = 'output_' + output.get('OutputKey').lower()
                                value = output.get('OutputValue')
                                self.event.update({key: value})
            return self.event

        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def account_initialization_check(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)

            sts = STS(self.logger)
            account = self.event.get('AccountId')
            region = os.environ.get('AWS_REGION')

            role_arn = "arn:aws:iam::" + str(account) + ":role/AWSControlTowerExecution"
            session_name = "check_account_creation_role"

            # assume role
            credentials = sts.assume_role_new_account(role_arn, session_name)
            self.logger.info("Assuming IAM role: {}".format(role_arn))

            if credentials.get('Error') is not None:
                self.event.update({'AccountInitialized': "no"})
                self.event.update({'Error': credentials.get('Error')})
                return self.event
            else:
                # instantiate EC2 class using temporary security credentials
                self.logger.info("Validating account initialization, ID: {}".format(account))
                ec2 = EC2(self.logger, region, credentials=credentials)

                try:
                    # Checking if EC2 Service Initialized
                    response = ec2.describe_regions()
                    self.logger.info('EC2 DescribeRegion Response')
                    self.logger.info(response)

                    # If API call succeeds
                    self.logger.info('Account Initialized')
                    self.event.update({'AccountInitialized': "yes"})
                    return self.event
                except Exception as e:
                    # If API call fails
                    self.logger.error('Error: {}'.format(e))
                    self.logger.error('Account still initializing, waiting for the Organization State Machine to retry...')
                    self.event.update({'AccountInitialized': "no"})
                    self.event.update({'Error': 'An error occurred when calling the DescribeRegions operation.'})
                    return self.event

        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def nested_dictionary_iteration(self, dictionary):
        for key, value in dictionary.items():
            if type(value) is dict:
                yield (key, value)
                yield from self.nested_dictionary_iteration(value)
            else:
                yield (key, value)

    def ssm_put_parameters(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.params)
            ssm = SSM(self.logger)
            ssm_params = self.params.get('SSMParameters')
            ssm_value = 'NotFound'
            if ssm_params is not None and type(ssm_params) is dict:
                # iterate through the keys to save them in SSM Parameter Store
                for key, value in ssm_params.items():
                    if value.startswith('$[') and value.endswith(']'):
                        value = value[2:-1]
                    # Iterate through all the keys in the event (includes the nested keys)
                    for k, v in self.nested_dictionary_iteration(self.event):
                        if value.lower() == k.lower():
                            ssm_value = v
                            break
                        else:
                            ssm_value = 'NotFound'
                    if ssm_value == 'NotFound':
                        # Raise Exception if the key is not found in the State Machine output
                        raise Exception("Unable to find the key: {} in the State Machine Output".format(value))
                    else:
                        self.logger.info("Adding value for SSM Parameter Store Key: {}".format(key))
                        ssm.put_parameter(key, ssm_value)
            else:
                self.logger.info("Nothing to add in SSM Parameter Store")
            return self.event
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            gf = GeneralFunctions(self.event, self.logger)
            gf.send_failure_to_cfn()
            raise

    def send_status(self, response_status):
        try:
            response_url = self.event.get('ResponseURL')
            reason = 'See details in State Machine Execution: ' + self.event.get('StateMachineArn')
            response_body = {}
            response_body.update({'Status': response_status})
            response_body.update({'Reason': reason})
            response_body.update({'PhysicalResourceId': self.event.get('PhysicalResourceId')})
            response_body.update({'StackId': self.event.get('StackId')})
            response_body.update({'RequestId': self.event.get('RequestId')})
            response_body.update({'LogicalResourceId': self.event.get('LogicalResourceId')})
            response_body.update({'Data': self.event})

            json_response_body = dumps(response_body)

            self.logger.info("Response Body")
            self.logger.info(json_response_body)

            headers = {
                'content-type': '',
                'content-length': str(len(json_response_body))
            }
            response = requests.put(response_url, data=json_response_body, headers=headers)
            self.logger.info("CloudFormation returned status code: " + response.reason)
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def send_success_to_cfn(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            self.logger.info(self.event)
            response_url = self.event.get('ResponseURL')
            if response_url is not None and len(response_url) > 0:
                self.send_status('SUCCESS')
            else:
                self.logger.info("ResponseURL not found")
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def send_failure_to_cfn(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            response_url = self.event.get('ResponseURL')
            if response_url is not None and len(response_url) > 0:
                self.send_status('FAILED')
            else:
                self.logger.info("ResponseURL not found")
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def send_execution_data(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            send = Metrics(self.logger)
            data = {"StateMachineExecutionCount": "1"}
            send.metrics(data)
            return self.event
        except:
            return self.event

    def random_wait(self):
        try:
            self.logger.info("Executing: " + self.__class__.__name__ + "/" + inspect.stack()[0][3])
            # Random wait between 1 to 14 minutes
            _seconds = randint(60, 840)
            time.sleep(_seconds)
            return self.event
        except:
            return self.event
