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

from lib.logger import Logger
from lib.state_machine import StateMachine
from lib.ssm import SSM
from lib.helper import sanitize, convert_s3_url_to_http_url, trim_length, download_remote_file
from lib.helper import transform_params, convert_http_url_to_s3_url, reverse_transform_params
from lib.manifest import Manifest
from lib.cloudformation import StackSet
from lib.organizations import Organizations
from lib.params import ParamsHandler
from lib.metrics import Metrics
from lib.sts import STS
from lib.s3 import S3
import inspect
import sys
import time
import os
import json
import tempfile
import filecmp
from uuid import uuid4

TEMPLATE_KEY_PREFIX = '_custom_control_tower_templates_staging'
MANIFEST_FILE_NAME = 'manifest.yaml'
CAPABILITIES = 'CAPABILITY_NAMED_IAM'


class DeployStackSetStateMachine(object):
    def __init__(self, logger, wait_time, manifest_file_path, sm_arn_stackset, staging_bucket, execution_mode):
        self.state_machine = StateMachine(logger)
        self.ssm = SSM(logger)
        self.s3 = S3(logger)
        self.send = Metrics(logger)
        self.param_handler = ParamsHandler(logger)
        self.logger = logger
        self.manifest_file_path = manifest_file_path
        self.manifest_folder = manifest_file_path[:-len(MANIFEST_FILE_NAME)]
        self.wait_time = wait_time
        self.sm_arn_stackset = sm_arn_stackset
        self.manifest = None
        self.list_sm_exec_arns = []
        self.staging_bucket = staging_bucket
        self.root_id = None
        self.uuid = uuid4()
        self.state_machine_event = {}
        if execution_mode.lower() == 'sequential':
            self.logger.info("Running {} mode".format(execution_mode))
            self.sequential_flag = True
        else:
            self.logger.info("Running {} mode".format(execution_mode))
            self.sequential_flag = False

    def _stage_template(self, relative_template_path):
        try:
            if relative_template_path.lower().startswith('s3'):
                # Convert the S3 URL s3://bucket-name/object to HTTP URL https://s3.amazonaws.com/bucket-name/object
                s3_url = convert_s3_url_to_http_url(relative_template_path)
            else:
                local_file = os.path.join(self.manifest_folder, relative_template_path)
                remote_file = "{}/{}_{}".format(TEMPLATE_KEY_PREFIX, self.uuid, relative_template_path)
                logger.info("Uploading the template file: {} to S3 bucket: {} and key: {}".format(local_file,
                                                                                                  self.staging_bucket,
                                                                                                  remote_file))
                self.s3.upload_file(self.staging_bucket, local_file, remote_file)
                s3_url = "{}{}{}{}".format('https://s3.amazonaws.com/', self.staging_bucket, '/', remote_file)
            return s3_url
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def _load_params(self, relative_parameter_path, account=None, region=None):
        try:
            if relative_parameter_path.lower().startswith('s3'):
                parameter_file = download_remote_file(self.logger, relative_parameter_path)
            else:
                parameter_file = os.path.join(self.manifest_folder, relative_parameter_path)

            logger.info("Parsing the parameter file: {}".format(parameter_file))

            with open(parameter_file, 'r') as content_file:
                parameter_file_content = content_file.read()

            params = json.loads(parameter_file_content)
            if account is not None:
                # Deploying Core resource Stack Set
                # The last parameter is set to False, because we do not want to replace the SSM parameter values yet.
                sm_params = self.param_handler.update_params(params, account, region, False)
            else:
                # Deploying Baseline resource Stack Set
                sm_params = self.param_handler.update_params(params)

            logger.info("Input Parameters for State Machine: {}".format(sm_params))
            return sm_params
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def _create_ssm_input_map(self, ssm_parameters):
        try:
            ssm_input_map = {}

            for ssm_parameter in ssm_parameters:
                key = ssm_parameter.name
                value = ssm_parameter.value
                ssm_value = self.param_handler.update_params(transform_params({key: value}))
                ssm_input_map.update(ssm_value)

            return ssm_input_map

        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def _create_state_machine_input_map(self, input_params, request_type='Create'):
        try:
            self.state_machine_event.update({'RequestType': request_type})
            self.state_machine_event.update({'ResourceProperties': input_params})

        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def _create_stack_set_state_machine_input_map(self, stack_set_name, template_url, parameters,
                                                  account_list, regions_list, ssm_map):
        input_params = {}
        input_params.update({'StackSetName': sanitize(stack_set_name)})
        input_params.update({'TemplateURL': template_url})
        input_params.update({'Parameters': parameters})
        input_params.update({'Capabilities': CAPABILITIES})

        if len(account_list) > 0:
            input_params.update({'AccountList': account_list})
            if len(regions_list) > 0:
                input_params.update({'RegionList': regions_list})
            else:
                input_params.update({'RegionList': [self.manifest.region]})
        else:
            input_params.update({'AccountList': ''})
            input_params.update({'RegionList': ''})

        if ssm_map is not None:
            input_params.update({'SSMParameters': ssm_map})

        self._create_state_machine_input_map(input_params)

    def _populate_ssm_params(self):
        try:
            # The scenario is if you have one core resource that exports output from CFN stack to SSM parameter
            # and then the next core resource reads the SSM parameter as input,
            # then it has to wait for the first core resource to
            # finish; read the SSM parameters and use its value as input for second core resource's input for SM
            # Get the parameters for CFN template from self.state_machine_event
            logger.debug("Populating SSM parameter values for SM input: {}".format(self.state_machine_event))
            params = self.state_machine_event.get('ResourceProperties').get('Parameters', {})
            # First transform it from {name: value} to [{'ParameterKey': name}, {'ParameterValue': value}]
            # then replace the SSM parameter names with its values
            sm_params = self.param_handler.update_params(transform_params(params))
            # Put it back into the self.state_machine_event
            self.state_machine_event.get('ResourceProperties').update({'Parameters': sm_params})
            logger.debug("Done populating SSM parameter values for SM input: {}".format(self.state_machine_event))

        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def _compare_template_and_params(self):
        try:
            stack_name = self.state_machine_event.get('ResourceProperties').get('StackSetName', '')
            flag = False
            if stack_name:
                stack_set = StackSet(self.logger)
                describe_response = stack_set.describe_stack_set(stack_name)
                if describe_response is not None:
                    self.logger.info("Found existing stack set.")

                    self.logger.info("Checking the status of last stack set operation on {}".format(stack_name))
                    response = stack_set.list_stack_set_operations(StackSetName=stack_name,
                                                                   MaxResults=1)

                    if response:
                        if response.get('Summaries'):
                            for instance in response.get('Summaries'):
                                self.logger.info("Status of last stack set operation : {}"
                                                 .format(instance.get('Status')))
                                if instance.get('Status') != 'SUCCEEDED':
                                    self.logger.info("The last stack operation did not succeed. "
                                                     "Triggering Update StackSet for {}".format(stack_name))
                                    return False

                    self.logger.info("Comparing the template of the StackSet: {} with local copy of template"
                                     .format(stack_name))

                    template_http_url = self.state_machine_event.get('ResourceProperties').get('TemplateURL', '')
                    if template_http_url:
                        template_s3_url = convert_http_url_to_s3_url(template_http_url)
                        local_template_file = download_remote_file(self.logger, template_s3_url)
                    else:
                        self.logger.error("TemplateURL in state machine input is empty. Check state_machine_event:{}"
                                          .format(self.state_machine_event))
                        return False

                    cfn_template_file = tempfile.mkstemp()[1]
                    with open(cfn_template_file, "w") as f:
                        f.write(describe_response.get('StackSet').get('TemplateBody'))

                    template_compare = filecmp.cmp(local_template_file, cfn_template_file, False)
                    self.logger.info("Comparing the parameters of the StackSet: {} "
                                     "with local copy of JSON parameters file".format(stack_name))

                    params_compare = True
                    params = self.state_machine_event.get('ResourceProperties').get('Parameters', {})
                    if template_compare:
                        cfn_params = reverse_transform_params(describe_response.get('StackSet').get('Parameters'))
                        for key, value in params.items():
                            if cfn_params.get(key, '') == value:
                                pass
                            else:
                                params_compare = False
                                break

                    self.logger.info("template_compare={}".format(template_compare))
                    self.logger.info("params_compare={}".format(params_compare))
                    if template_compare and params_compare:
                        account_list = self.state_machine_event.get('ResourceProperties').get("AccountList", [])
                        if account_list:
                            self.logger.info("Comparing the Stack Instances Account & Regions for StackSet: {}"
                                             .format(stack_name))
                            expected_region_list = set(self.state_machine_event.get('ResourceProperties').get("RegionList", []))

                            # iterator over accounts in event account list
                            for account in account_list:
                                actual_region_list = set()

                                self.logger.info("### Listing the Stack Instances for StackSet: {} and Account: {} ###"
                                                 .format(stack_name, account))
                                stack_instance_list = stack_set.list_stack_instances_per_account(stack_name, account)

                                self.logger.info(stack_instance_list)

                                if stack_instance_list:
                                    for instance in stack_instance_list:
                                        if instance.get('Status').upper() == 'CURRENT':
                                            actual_region_list.add(instance.get('Region'))
                                        else:
                                            self.logger.info("Found at least one of the Stack Instances in {} state."
                                                             " Triggering Update StackSet for {}"
                                                             .format(instance.get('Status'),
                                                                     stack_name))
                                            return False
                                else:
                                    self.logger.info("Found no stack instances in account: {}, "
                                                     "Updating StackSet: {}".format(account, stack_name))
                                    # # move the account id to index 0
                                    # newindex = 0
                                    # oldindex = self.state_machine_event.get('ResourceProperties').get("AccountList").index(account)
                                    # self.state_machine_event.get('ResourceProperties').get("AccountList").insert(newindex, self.state_machine_event.get('ResourceProperties').get("AccountList").pop(oldindex))
                                    return False

                                if expected_region_list.issubset(actual_region_list):
                                    self.logger.info("Found expected regions : {} in deployed stack instances : {},"
                                                     " so skipping Update StackSet for {}"
                                                     .format(expected_region_list,
                                                             actual_region_list,
                                                             stack_name))
                                    flag = True
                        else:
                            self.logger.info("Found no changes in template & parameters, "
                                             "so skipping Update StackSet for {}".format(stack_name))
                            flag = True
            return flag
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def state_machine_failed(self, status, failed_execution_list):
        error = " StackSet State Machine Execution(s) Failed. Navigate to the AWS Step Functions console and" \
                " review the following State Machine Executions. ARN List: {}".format(failed_execution_list)
        if status == 'FAILED':
            logger.error(100 * '*')
            logger.error(error)
            logger.error(100 * '*')
            sys.exit(1)

    def _run_or_queue_state_machine(self, stackset_name):
        try:
            logger.info("State machine Input: {}".format(self.state_machine_event))
            exec_name = "%s-%s-%s" % (self.state_machine_event.get('RequestType'), trim_length(stackset_name.replace(" ", ""), 50),
                                      time.strftime("%Y-%m-%dT%H-%M-%S"))
            # If Sequential, wait for the SM to be executed before kicking of the next one
            if self.sequential_flag:
                self.logger.info(" > > > > > >  Running Sequential Mode. > > > > > >")
                self._populate_ssm_params()
                if self._compare_template_and_params():
                    return
                else:
                    sm_exec_arn = self.state_machine.trigger_state_machine(self.sm_arn_stackset, self.state_machine_event, exec_name)
                    self.list_sm_exec_arns.append(sm_exec_arn)
                    status, failed_execution_list = self.monitor_state_machines_execution_status()
                    if status == 'FAILED':
                        self.state_machine_failed(status, failed_execution_list)
                    else:
                        self.logger.info("State Machine execution completed. Starting next execution...")
            # Else if Parallel, execute all SM at regular interval of wait_time
            else:
                self.logger.info(" | | | | | |  Running Parallel Mode. | | | | | |")
                # RUNS Parallel, execute all SM at regular interval of wait_time
                self._populate_ssm_params()
                # if the stackset comparision is matches - skip SM execution
                if self._compare_template_and_params():
                    return
                else: # if False execution SM
                    sm_exec_arn = self.state_machine.trigger_state_machine(self.sm_arn_stackset, self.state_machine_event, exec_name)
                time.sleep(int(wait_time))  # Sleeping for sometime
                self.list_sm_exec_arns.append(sm_exec_arn)
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def _deploy_resource(self, resource, account_list):
        try:
            template_full_path = self._stage_template(resource.template_file)
            params = {}
            if resource.parameter_file:
                if len(resource.regions) > 0:
                    params = self._load_params(resource.parameter_file, account_list, resource.regions[0])
                else:
                    params = self._load_params(resource.parameter_file, account_list, self.manifest.region)

            ssm_map = self._create_ssm_input_map(resource.ssm_parameters)

            # Deploying Core resource Stack Set
            stack_name = "CustomControlTower-{}".format(resource.name)
            self._create_stack_set_state_machine_input_map(stack_name, template_full_path,
                                                                      params, account_list, resource.regions, ssm_map)


            self.logger.info(" >>> State Machine Input >>>")
            self.logger.info(self.state_machine_event)

            self._run_or_queue_state_machine(stack_name)
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def _get_root_id(self, org):
        response = org.list_roots()
        self.logger.info("Response: List Roots")
        self.logger.info(response)
        return response['Roots'][0].get('Id')

    def _list_ou_for_parent(self, org, parent_id):
        _ou_list = org.list_organizational_units_for_parent(parent_id)
        self.logger.info("Print Organizational Units List under {}".format(parent_id))
        self.logger.info(_ou_list)
        return _ou_list

    def _get_accounts_in_ou(self, org, ou_id_list):
        _accounts_in_ou = []
        accounts_in_all_ous = []
        ou_id_to_account_map = {}

        for _ou_id in ou_id_list:
            _account_list = org.list_accounts_for_parent(_ou_id)
            for _account in _account_list:
                # filter ACTIVE and CREATED accounts
                if _account.get('Status') == "ACTIVE":
                    # create a list of accounts in OU
                    accounts_in_all_ous.append(_account.get('Id'))
                    _accounts_in_ou.append(_account.get('Id'))

            # create a map of accounts for each ou
            self.logger.info("Creating Key:Value Mapping - OU ID: {} ; Account List: {}"
                             .format(_ou_id, _accounts_in_ou))
            ou_id_to_account_map.update({_ou_id: _accounts_in_ou})
            self.logger.info(ou_id_to_account_map)

            # reset list of accounts in the OU
            _accounts_in_ou = []

        self.logger.info("All accounts in OU List: {}".format(accounts_in_all_ous))
        self.logger.info("OU to Account ID mapping")
        self.logger.info(ou_id_to_account_map)
        return accounts_in_all_ous, ou_id_to_account_map

    def _get_ou_ids(self, org):
        # for each OU get list of account
        # get root id
        root_id = self._get_root_id(org)

        # get OUs under the Org root
        ou_list_at_root_level = self._list_ou_for_parent(org, root_id)

        ou_id_list = []
        _ou_name_to_id_map = {}
        _all_ou_ids = []

        for ou_at_root_level in ou_list_at_root_level:
            # build list of all the OU IDs under Org root
            _all_ou_ids.append(ou_at_root_level.get('Id'))
            # build a list of ou id
            _ou_name_to_id_map.update({ou_at_root_level.get('Name'): ou_at_root_level.get('Id')})

        self.logger.info("Print OU Name to OU ID Map")
        self.logger.info(_ou_name_to_id_map)

        # return:
        # 1. OU IDs of the OUs in the manifest
        # 2. Account IDs in OUs in the manifest
        # 3. Account IDs in all the OUs in the manifest
        return _all_ou_ids, _ou_name_to_id_map

    def get_account_for_name(self, org):
        # get all accounts in the organization
        account_list = org.get_accounts_in_org()
        #self.logger.info("Print Account List: {}".format(account_list))

        _name_to_account_map = {}
        for account in account_list:
            if account.get("Status") == "ACTIVE":
                _name_to_account_map.update({account.get("Name"): account.get("Id")})

        self.logger.info("Print Account Name > Account Mapping")
        self.logger.info(_name_to_account_map)

        return _name_to_account_map

    def get_organization_details(self):
        # > build dict
        # KEY: OU Name (in the manifest)
        # VALUE: OU ID (at root level)
        # > build list
        # all OU IDs under root
        org = Organizations(self.logger)
        all_ou_ids, ou_name_to_id_map = self._get_ou_ids(org)
        # > build list of all active accounts
        # use case: use to validate accounts in the manifest file.
        # > build dict
        # KEY: OU ID (for each OU at root level)
        # VALUE: get list of all active accounts
        # use case: map OU Name to account IDs
        accounts_in_all_ous, ou_id_to_account_map = self._get_accounts_in_ou(org, all_ou_ids)
        # build dict
        # KEY: email
        # VALUE: account id
        # use case: convert email in manifest to account ID for SM event
        name_to_account_map = self.get_account_for_name(org)
        return accounts_in_all_ous, ou_id_to_account_map, ou_name_to_id_map, name_to_account_map

    def start_stackset_sm(self):
        try:
            logger.info("Parsing Core Resources from {} file".format(self.manifest_file_path))
            count = 0

            accounts_in_all_ous, ou_id_to_account_map, ou_name_to_id_map, name_to_account_map = self.get_organization_details()

            for resource in self.manifest.cloudformation_resources:
                self.logger.info(">>>>>>>>> START : {} >>>>>>>>>".format(resource.name))
                # Handle scenario if 'deploy_to_ou' key does not exist in the resource
                try:
                    self.logger.info(resource.deploy_to_ou)
                except:
                    resource.deploy_to_ou = []

                # Handle scenario if 'deploy_to_account' key does not exist in the resource
                try:
                    self.logger.info(resource.deploy_to_account)
                except:
                    resource.deploy_to_account = []

                # find accounts for given ou name
                accounts_in_ou = []
                ou_ids_manifest = []

                # check if OU name list is empty
                if resource.deploy_to_ou:
                    # convert OU Name to OU IDs
                    for ou_name in resource.deploy_to_ou:
                        ou_id = [value for key, value in ou_name_to_id_map.items() if ou_name.lower() in key.lower()]
                        ou_ids_manifest.extend(ou_id)

                    # convert OU IDs to accounts
                    for ou_id, accounts in ou_id_to_account_map.items():
                        if ou_id in ou_ids_manifest:
                            accounts_in_ou.extend(accounts)

                    self.logger.info(">>> Accounts: {} in OUs: {}".format(accounts_in_ou, resource.deploy_to_ou))

                # convert account numbers to string type
                account_list = self._convert_list_values_to_string(resource.deploy_to_account)
                self.logger.info(">>>>>> ACCOUNT LIST")
                self.logger.info(account_list)

                # separate account id and emails
                name_list = []
                new_account_list = []
                self.logger.info(account_list)
                for item in account_list:
                    if item.isdigit() and len(item) == 12:  # if an actual account ID
                        new_account_list.append(item)
                        self.logger.info(new_account_list)
                    else:
                        name_list.append(item)
                        self.logger.info(name_list)

                # check if name list is empty
                if name_list:
                    # convert OU Name to OU IDs
                    for name in name_list:
                        name_account = [value for key, value in name_to_account_map.items() if
                                         name.lower() in key.lower()]
                        self.logger.info("%%%%%%% Name {} -  Account {}".format(name, name_account))
                        new_account_list.extend(name_account)

                # Remove account ids from the manifest that is not in the organization or not active
                sanitized_account_list = list(set(new_account_list).intersection(set(accounts_in_all_ous)))
                self.logger.info("Print Updated Manifest Account List")
                self.logger.info(sanitized_account_list)

                # merge account lists manifest account list and accounts under OUs in the manifest
                sanitized_account_list.extend(accounts_in_ou)
                sanitized_account_list = list(set(sanitized_account_list)) # remove duplicate accounts
                self.logger.info("Print merged account list - accounts in manifest + account under OU in manifest")
                self.logger.info(sanitized_account_list)

                if resource.deploy_method.lower() == 'stack_set':
                    self._deploy_resource(resource, sanitized_account_list)
                else:
                    raise Exception("Unsupported deploy_method: {} found for resource {} and Account: {} in Manifest"
                                    .format(resource.deploy_method, resource.name, sanitized_account_list))
                self.logger.info("<<<<<<<<< FINISH : {} <<<<<<<<<".format(resource.name))

                # Count number of stack sets deployed
                count += 1
            data = {"StackSetCount": str(count)}
            self.send.metrics(data)

            return
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    # return list of strings
    def _convert_list_values_to_string(self, _list):
        return list(map(str, _list))

    # monitor list of state machine executions
    def monitor_state_machines_execution_status(self):
        try:
            if self.list_sm_exec_arns:
                self.logger.info("Starting to monitor the SM Executions: {}".format(self.list_sm_exec_arns))
                final_status = 'RUNNING'

                while final_status == 'RUNNING':
                    for sm_exec_arn in self.list_sm_exec_arns:
                        status = self.state_machine.check_state_machine_status(sm_exec_arn)
                        if status == 'RUNNING':
                            final_status = 'RUNNING'
                            time.sleep(int(wait_time))
                            break
                        else:
                            final_status = 'COMPLETED'

                err_flag = False
                failed_sm_execution_list = []
                for sm_exec_arn in self.list_sm_exec_arns:
                    status = self.state_machine.check_state_machine_status(sm_exec_arn)
                    if status == 'SUCCEEDED':
                        continue
                    else:
                        failed_sm_execution_list.append(sm_exec_arn)
                        err_flag = True
                        continue

                if err_flag:
                    return 'FAILED', failed_sm_execution_list
                else:
                    return 'SUCCEEDED', ''
            else:
                self.logger.info("SM Execution List {} is empty, nothing to monitor.".format(self.list_sm_exec_arns))
                return None, []

        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def trigger_stackset_state_machine(self):
        try:
            self.manifest = Manifest(self.manifest_file_path)
            self.start_stackset_sm()
            return
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise


if __name__ == '__main__':
    if len(sys.argv) > 6:
        log_level = sys.argv[1]
        wait_time = sys.argv[2]
        manifest_file_path = sys.argv[3]
        sm_arn_stackset = sys.argv[4]
        staging_bucket = sys.argv[5]
        exec_mode = sys.argv[6]

        logger = Logger(loglevel=log_level)
        deploy_stackset = DeployStackSetStateMachine(logger, wait_time, manifest_file_path,
                                                     sm_arn_stackset, staging_bucket, exec_mode)

        deploy_stackset.trigger_stackset_state_machine()
        if exec_mode.lower() != 'sequential':
            status, failed_execution_list = deploy_stackset.monitor_state_machines_execution_status()
            deploy_stackset.state_machine_failed(status, failed_execution_list)

    else:
        print('No arguments provided. ')
        print('Example: trigger_stackset_sm.py <LOG-LEVEL> <WAIT_TIME> '
              '<MANIFEST-FILE-PATH> <SM_ARN_STACKSET> <STAGING_BUCKET> <EXECUTION-MODE>')
        sys.exit(2)
