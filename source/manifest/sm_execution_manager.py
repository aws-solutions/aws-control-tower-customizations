import os
import time
import tempfile
import filecmp
from uuid import uuid4
from aws.services.s3 import S3
from aws.services.state_machine import StateMachine
from aws.services.cloudformation import StackSet
from utils.string_manipulation import trim_length
from aws.utils.url_conversion import convert_http_url_to_s3_url
from utils.parameter_manipulation import transform_params, \
    reverse_transform_params
from metrics.solution_metrics import SolutionMetrics
from manifest.cfn_params_handler import CFNParamsHandler


class SMExecutionManager:
    def __init__(self, logger, sm_input_list):
        self.logger = logger
        self.sm_input_list = sm_input_list
        self.list_sm_exec_arns = []
        self.s3 = S3(logger)
        self.solution_metrics = SolutionMetrics(logger)
        self.param_handler = CFNParamsHandler(logger)
        self.state_machine = StateMachine(logger)
        self.stack_set = StackSet(logger)
        self.wait_time = os.environ.get('WAIT_TIME')
        self.execution_mode = os.environ.get('EXECUTION_MODE')

    def launch_executions(self):
        self.logger.info("%%% Launching State Machine Execution %%%")
        if self.execution_mode.upper() == 'PARALLEL':
            self.logger.info(" | | | | |  Running Parallel Mode. | | | | |")
            return self.run_execution_parallel_mode()

        elif self.execution_mode.upper() == 'SEQUENTIAL':
            self.logger.info(" > > > > >  Running Sequential Mode. > > > > >")
            return self.run_execution_sequential_mode()
        else:
            raise Exception("Invalid execution mode: {}"
                            .format(self.execution_mode))

    def run_execution_sequential_mode(self):
        status, failed_execution_list = None, []
        # start executions at given intervals
        for sm_input in self.sm_input_list:
            updated_sm_input = self.populate_ssm_params(sm_input)
            stack_set_name = sm_input.get('ResourceProperties')\
                .get('StackSetName', '')

            self.logger.info("stack_set_name: {}".format(stack_set_name))
            self.logger.info("sm_input: {}".format(sm_input))

            template_matched, parameters_matched = \
                self.compare_template_and_params(sm_input, stack_set_name)

            self.logger.info("FLAGS: {} |  {}".format(template_matched,
                                                      parameters_matched))
            if template_matched and parameters_matched:
                if self.check_stack_instances_per_account(sm_input,
                                                          stack_set_name):
                    continue

            sm_exec_name = self.get_sm_exec_name(updated_sm_input)

            sm_exec_arn = self.setup_execution(updated_sm_input,
                                               sm_exec_name)
            self.list_sm_exec_arns.append(sm_exec_arn)

            status, failed_execution_list = \
                self.monitor_state_machines_execution_status()
            if status == 'FAILED':
                return status, failed_execution_list
            else:
                self.logger.info("State Machine execution completed. "
                                 "Starting next execution...")
        else:
            self.logger.info("All State Machine executions completed.")
        return status, failed_execution_list

    def run_execution_parallel_mode(self):
        # start executions at given intervals
        for sm_input in self.sm_input_list:
            sm_exec_name = self.get_sm_exec_name(sm_input)
            sm_exec_arn = self.setup_execution(sm_input, sm_exec_name)
            self.list_sm_exec_arns.append(sm_exec_arn)
            time.sleep(int(self.wait_time))
        # monitor execution status
        status, failed_execution_list = \
            self.monitor_state_machines_execution_status()
        return status, failed_execution_list

    @staticmethod
    def get_sm_exec_name(sm_input):
        if os.environ.get('STAGE_NAME').upper() == 'SCP':
            return sm_input.get('ResourceProperties')\
                .get('PolicyDocument').get('Name')
        elif os.environ.get('STAGE_NAME').upper() == 'STACKSET':
            return sm_input.get('ResourceProperties').get('StackSetName')
        else:
            return uuid4()  # return random string

    def setup_execution(self, sm_input, name):
        self.logger.info("State machine Input: {}".format(sm_input))

        # set execution name
        exec_name = "%s-%s-%s" % (sm_input.get('RequestType'),
                                  trim_length(name.replace(" ", ""), 50),
                                  time.strftime("%Y-%m-%dT%H-%M-%S"))

        # execute all SM at regular interval of wait_time
        return self.state_machine.start_execution(os.environ.get('SM_ARN'),
                                                  sm_input,
                                                  exec_name)

    def populate_ssm_params(self, sm_input):
        """The scenario is if you have one CFN resource that exports output
         from CFN stack to SSM parameter and then the next CFN resource
         reads the SSM parameter as input, then it has to wait for the first
         CFN resource to finish; read the SSM parameters and use its value
         as input for second CFN resource's input for SM. Get the parameters
         for CFN template from sm_input
        """
        self.logger.info("Populating SSM parameter values for SM input: {}"
                         .format(sm_input))
        params = sm_input.get('ResourceProperties')\
            .get('Parameters', {})
        # First transform it from {name: value} to [{'ParameterKey': name},
        # {'ParameterValue': value}]
        # then replace the SSM parameter names with its values
        sm_params = self.param_handler.update_params(transform_params(params))
        # Put it back into the self.state_machine_event
        sm_input.get('ResourceProperties').update({'Parameters': sm_params})
        self.logger.info("Done populating SSM parameter values for SM input:"
                         " {}".format(sm_input))
        return sm_input

    def compare_template_and_params(self, sm_input, stack_name):
        template_compare, params_compare = False, False
        if stack_name:
            describe_response = self.stack_set\
                .describe_stack_set(stack_name)

            self.logger.info("describe_stack_set response:")
            self.logger.info(describe_response)

            if describe_response is not None:
                self.logger.info("Found existing stack set.")

                operation_status_flag = self.get_stack_set_operation_status(
                    stack_name)

                if operation_status_flag:
                    self.logger.info("Continuing...")
                else:
                    return operation_status_flag, False

                # Compare template copy - START
                self.logger.info("Comparing the template of the StackSet:"
                                 " {} with local copy of template"
                                 .format(stack_name))

                template_http_url = sm_input.get('ResourceProperties')\
                    .get('TemplateURL', '')
                if template_http_url:
                    template_s3_url = convert_http_url_to_s3_url(
                        template_http_url
                    )
                    local_template_file = self.s3.download_remote_file(
                        template_s3_url
                    )
                else:
                    self.logger.error("TemplateURL in state machine input "
                                      "is empty. Check state_machine_event"
                                      ":{}".format(sm_input))
                    return False, False

                cfn_template_file = tempfile.mkstemp()[1]
                with open(cfn_template_file, "w") as f:
                    f.write(describe_response.get('StackSet')
                            .get('TemplateBody'))
                # cmp function return true of the contents are same
                template_compare = filecmp.cmp(local_template_file,
                                               cfn_template_file,
                                               False)
                self.logger.info("Comparing the parameters of the StackSet"
                                 ": {} with local copy of JSON parameters"
                                 " file".format(stack_name))

                params_compare = True
                params = sm_input.get('ResourceProperties')\
                    .get('Parameters', {})
                # template are same - compare parameters (skip if template
                # are not same)
                if template_compare:
                    cfn_params = reverse_transform_params(describe_response
                                                          .get('StackSet')
                                                          .get('Parameters')
                                                          )
                    for key, value in params.items():
                        if cfn_params.get(key, '') == value:
                            pass
                        else:
                            params_compare = False
                            break

                self.logger.info("template_compare={}; params_compare={}"
                                 .format(template_compare, params_compare))

        return template_compare, params_compare

    def get_stack_set_operation_status(self, stack_name):
        self.logger.info("Checking the status of last stack set "
                         "operation on {}".format(stack_name))
        response = self.stack_set. \
            list_stack_set_operations(StackSetName=stack_name,
                                      MaxResults=1)
        if response:
            if response.get('Summaries'):
                for instance in response.get('Summaries'):
                    self.logger.info("Status of last stack set "
                                     "operation : {}"
                                     .format(instance
                                             .get('Status')))
                    if instance.get('Status') != 'SUCCEEDED':
                        self.logger.info("The last stack operation"
                                         " did not succeed. "
                                         "Triggering "
                                         " Update StackSet for {}"
                                         .format(stack_name))
                        return False
                return True

    def check_stack_instances_per_account(self, sm_input, stack_name):
        flag = False
        account_list = sm_input.get('ResourceProperties') \
            .get("AccountList", [])
        if account_list:
            self.logger.info("Comparing the Stack Instances "
                             "Account & Regions for "
                             "StackSet: {}".format(stack_name))
            expected_region_list = set(sm_input
                                       .get('ResourceProperties')
                                       .get("RegionList", []))

            # iterator over accounts in event account list
            for account in account_list:
                actual_region_list = set()

                self.logger.info("### Listing the Stack "
                                 "Instances for StackSet: {}"
                                 " and Account: {} ###"
                                 .format(stack_name, account))
                stack_instance_list = self.stack_set. \
                    list_stack_instances_per_account(stack_name,
                                                     account)

                self.logger.info(stack_instance_list)

                if stack_instance_list:
                    for instance in stack_instance_list:
                        if instance.get('Status') \
                                .upper() == 'CURRENT':
                            actual_region_list \
                                .add(instance.get('Region'))
                        else:
                            self.logger.info("Found at least one of"
                                             " the Stack Instances"
                                             " in {} state."
                                             " Triggering Update"
                                             " StackSet for {}"
                                             .format(instance
                                                     .get('Status'),
                                                     stack_name))
                            return False
                else:
                    self.logger.info("Found no stack instances in"
                                     " account: {},Updating "
                                     "StackSet: {}"
                                     .format(account, stack_name))
                    return False

                if expected_region_list. \
                        issubset(actual_region_list):
                    self.logger.info("Found expected regions : {} "
                                     "in deployed stack instances :"
                                     " {}, so skipping Update  "
                                     "StackSet for {}"
                                     .format(expected_region_list,
                                             actual_region_list,
                                             stack_name))
                    flag = True
        else:
            self.logger.info("Found no changes in template "
                             "& parameters, so skipping Update  "
                             "StackSet for {}".format(stack_name))
            flag = True
        return flag

    def monitor_state_machines_execution_status(self):
        if self.list_sm_exec_arns:
            final_status = 'RUNNING'

            while final_status == 'RUNNING':
                for sm_exec_arn in self.list_sm_exec_arns:
                    status = self.state_machine.check_state_machine_status(
                        sm_exec_arn)
                    if status == 'RUNNING':
                        final_status = 'RUNNING'
                        time.sleep(int(self.wait_time))
                        break
                    else:
                        final_status = 'COMPLETED'

            err_flag = False
            failed_sm_execution_list = []
            for sm_exec_arn in self.list_sm_exec_arns:
                status = self.state_machine.check_state_machine_status(
                    sm_exec_arn)
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
            self.logger.info("SM Execution List {} is empty, nothing to "
                             "monitor.".format(self.list_sm_exec_arns))
            return None, []
