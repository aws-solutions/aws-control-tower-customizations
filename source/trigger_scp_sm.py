
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
from lib.helper import sanitize, convert_s3_url_to_http_url, trim_length
from lib.manifest import Manifest
from lib.params import ParamsHandler
from lib.metrics import Metrics
from lib.s3 import S3
import inspect
import sys
import time
import os

TEMPLATE_KEY_PREFIX = '_custom_control_tower_templates_staging'
MANIFEST_FILE_NAME = 'manifest.yaml'


class LaunchSCP(object):
    def __init__(self, logger, wait_time, manifest_file_path, sm_arn_scp, staging_bucket):
        self.state_machine = StateMachine(logger)
        self.s3 = S3(logger)
        self.send = Metrics(logger)
        self.param_handler = ParamsHandler(logger)
        self.logger = logger
        self.manifest_file_path = manifest_file_path
        self.manifest_folder = manifest_file_path[:-len(MANIFEST_FILE_NAME)]
        self.wait_time = wait_time
        self.sm_arn_scp = sm_arn_scp
        self.manifest = None
        self.list_sm_exec_arns = []
        self.nested_ou_delimiter = ""
        self.staging_bucket = staging_bucket
        self.root_id = None
  
    def _create_service_control_policy_state_machine_input_map(self, policy_name, policy_full_path, policy_desc='', ou_list=[]):
        input_params = {}
        policy_doc = {}
        policy_doc.update({'Name': sanitize(policy_name)})
        policy_doc.update({'Description': policy_desc})
        policy_doc.update({'PolicyURL': policy_full_path})
        input_params.update({'PolicyDocument': policy_doc})
        input_params.update({'AccountId': ''})
        input_params.update({'PolicyList': []})
        input_params.update({'Operation': ''})
        input_params.update({'OUList': ou_list})
        input_params.update({'OUNameDelimiter': self.nested_ou_delimiter})
        return self._create_state_machine_input_map(input_params)
    
    def _create_state_machine_input_map(self, input_params, request_type='Create'):
        request = {}
        request.update({'RequestType': request_type})
        request.update({'ResourceProperties': input_params})

        return request
        
    def _stage_template(self, relative_template_path):
        if relative_template_path.lower().startswith('s3'):
            # Convert the S3 URL s3://bucket-name/object
            # to HTTP URL https://s3.amazonaws.com/bucket-name/object
            s3_url = convert_s3_url_to_http_url(relative_template_path)
        else:
            local_file = os.path.join(self.manifest_folder, relative_template_path)
            # remote_file = "{}/{}_{}".format(TEMPLATE_KEY_PREFIX, self.token, relative_template_path[relative_template_path.rfind('/')+1:])
            remote_file = "{}/{}".format(TEMPLATE_KEY_PREFIX, relative_template_path)
            logger.info("Uploading the template file: {} to S3 bucket: {} and key: {}".format(local_file, self.staging_bucket, remote_file))
            self.s3.upload_file(self.staging_bucket, local_file, remote_file)
            s3_url = "{}{}{}{}".format('https://s3.amazonaws.com/', self.staging_bucket, '/', remote_file)
        return s3_url
    
    def _run_or_queue_state_machine(self, sm_input, sm_arn, sm_name):
        logger.info("State machine Input: {}".format(sm_input))
        exec_name = "%s-%s-%s" % (sm_input.get('RequestType'), trim_length(sm_name.replace(" ", ""), 50),
                                  time.strftime("%Y-%m-%dT%H-%M-%S"))
    
        # execute all SM at regular interval of wait_time
        sm_exec_arn = self.state_machine.trigger_state_machine(sm_arn, sm_input, exec_name)
        time.sleep(int(wait_time))  # Sleeping for sometime
        self.list_sm_exec_arns.append(sm_exec_arn)

    def trigger_service_control_policy_state_machine(self):
        try:
            self.manifest = Manifest(self.manifest_file_path)
            self.start_service_control_policy_sm()
            return
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise
          
    def monitor_state_machines_execution_status(self):
        try:
            if self.list_sm_exec_arns:
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
 
    def start_service_control_policy_sm(self):
        try:
            logger.info("Processing SCPs from {} file".format(self.manifest_file_path))
            count = 0

            for policy in self.manifest.organization_policies:
                # Generate the list of OUs to attach this SCP to
                ou_list = []
                attach_ou_list = set(policy.apply_to_accounts_in_ou)

                for ou in attach_ou_list:
                    ou_list.append((ou, 'Attach'))

                policy_full_path = self._stage_template(policy.policy_file)
                sm_input = self._create_service_control_policy_state_machine_input_map(policy.name, policy_full_path,
                                                                                       policy.description, ou_list)
                self._run_or_queue_state_machine(sm_input, sm_arn_scp, policy.name)
               
                # Count number of SCPs
                count += 1

            data = {"SCPPolicyCount": str(count)}
            self.send.metrics(data)
            
            # Exit where there are no organization policies
            if count == 0:
                logger.info("No organization policies are found.")
                sys.exit(0)
            return
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise


if __name__ == '__main__':
    if len(sys.argv) > 5:
        log_level = sys.argv[1]
        wait_time = sys.argv[2]
        manifest_file_path = sys.argv[3]
        sm_arn_scp = sys.argv[4]
        staging_bucket = sys.argv[5]

        logger = Logger(loglevel=log_level)
        scp_run = LaunchSCP(logger, wait_time, manifest_file_path, sm_arn_scp, staging_bucket)
        scp_run.trigger_service_control_policy_state_machine()
        print("sm executed!")
        status, failed_execution_list = scp_run.monitor_state_machines_execution_status()
        error = " Service Control Policy State Machine Execution(s) Failed. Navigate to the AWS Step Functions console and" \
                " review the following State Machine Executions. ARN List: {}".format(failed_execution_list)

        if status == 'FAILED':
            logger.error(100 * '*')
            logger.error(error)
            logger.error(100 * '*')
            sys.exit(1)

    else:
        print('No arguments provided. ')
        print('Example: trigger_scp_sm.py <LOG-LEVEL> <WAIT_TIME> <MANIFEST-FILE-PATH> <SM_ARN_SCP> <STAGING_BUCKET>')
        sys.exit(2)
