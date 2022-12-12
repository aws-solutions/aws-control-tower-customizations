###############################################################################
#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.    #
#                                                                             #
#  Licensed under the Apache License, Version 2.0 (the "License").            #
#  You may not use this file except in compliance with the License.
#  A copy of the License is located at                                        #
#                                                                             #
#      http://www.apache.org/licenses/LICENSE-2.0                             #
#                                                                             #
#  or in the "license" file accompanying this file. This file is distributed  #
#  on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express #
#  or implied. See the License for the specific language governing permissions#
#  and limitations under the License.                                         #
###############################################################################

import filecmp
import os
import tempfile
import time
from uuid import uuid4

from botocore.exceptions import ClientError
from cfct.aws.services.cloudformation import StackSet
from cfct.aws.services.s3 import S3
from cfct.aws.services.state_machine import StateMachine
from cfct.aws.utils.url_conversion import parse_bucket_key_names
from cfct.exceptions import StackSetHasFailedInstances
from cfct.manifest.cfn_params_handler import CFNParamsHandler
from cfct.metrics.solution_metrics import SolutionMetrics
from cfct.utils.list_comparision import compare_lists
from cfct.utils.parameter_manipulation import reverse_transform_params, transform_params
from cfct.utils.string_manipulation import trim_length_from_end


class SMExecutionManager:
    def __init__(self, logger, sm_input_list, enforce_successful_stack_instances=False):
        self.logger = logger
        self.sm_input_list = sm_input_list
        self.list_sm_exec_arns = []
        self.solution_metrics = SolutionMetrics(logger)
        self.param_handler = CFNParamsHandler(logger)
        self.state_machine = StateMachine(logger)
        self.stack_set = StackSet(logger)
        self.wait_time = os.environ.get("WAIT_TIME")
        self.execution_mode = os.environ.get("EXECUTION_MODE")
        self.enforce_successful_stack_instances = enforce_successful_stack_instances

    def launch_executions(self):
        self.logger.info("%%% Launching State Machine Execution %%%")
        if self.execution_mode.upper() == "PARALLEL":
            self.logger.info(" | | | | |  Running Parallel Mode. | | | | |")
            return self.run_execution_parallel_mode()

        elif self.execution_mode.upper() == "SEQUENTIAL":
            self.logger.info(" > > > > >  Running Sequential Mode. > > > > >")
            return self.run_execution_sequential_mode()
        else:
            raise ValueError("Invalid execution mode: {}".format(self.execution_mode))

    def run_execution_sequential_mode(self):
        status, failed_execution_list = None, []
        # start executions at given intervals
        for sm_input in self.sm_input_list:
            updated_sm_input = self.populate_ssm_params(sm_input)
            stack_set_name = sm_input.get("ResourceProperties").get("StackSetName", "")
            is_deletion = sm_input.get("RequestType").lower() == "Delete".lower()
            if is_deletion:
                start_execution_flag = True
            else:
                (
                    template_matched,
                    parameters_matched,
                    stack_set_exist,
                ) = self.compare_template_and_params(sm_input, stack_set_name)

                self.logger.info(
                    "Stack Set Name: {} | "
                    "Same Template?: {} | "
                    "Same Parameters?: {}".format(
                        stack_set_name, template_matched, parameters_matched
                    )
                )

                stackset_unchanged = all(
                    [template_matched, parameters_matched, stack_set_exist]
                )
                if stackset_unchanged:
                    start_execution_flag = self.compare_stack_instances(
                        sm_input, stack_set_name
                    )
                    # template and parameter does not require update
                    updated_sm_input.update({"SkipUpdateStackSet": "yes"})
                else:
                    # the template or parameters needs to be updated
                    # start SM execution
                    start_execution_flag = True

            if start_execution_flag:

                sm_exec_name = self.get_sm_exec_name(updated_sm_input)
                sm_exec_arn = self.setup_execution(updated_sm_input, sm_exec_name)
                self.list_sm_exec_arns.append(sm_exec_arn)

                # In sequential mode, monitor 1 execution at a time
                (
                    status,
                    failed_execution_list,
                ) = self.monitor_state_machines_execution_status(
                    sm_execution_arns=[sm_exec_arn], retry_wait_time=self.wait_time
                )

                if status == "FAILED":
                    return status, failed_execution_list

                if self.enforce_successful_stack_instances:
                    try:
                        self.enforce_stack_set_deployment_successful(stack_set_name)
                    except ClientError as error:
                        if (
                            is_deletion
                            and error.response["Error"]["Code"]
                            == "StackSetNotFoundException"
                        ):
                            pass
                        else:
                            raise error

                else:
                    self.logger.info(
                        "State Machine execution completed. "
                        "Starting next execution..."
                    )
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
        status, failed_execution_list = self.monitor_state_machines_execution_status(
            sm_execution_arns=self.list_sm_exec_arns, retry_wait_time=self.wait_time
        )
        return status, failed_execution_list

    @staticmethod
    def get_sm_exec_name(sm_input):
        if os.environ.get("STAGE_NAME").upper() == "SCP":
            return sm_input.get("ResourceProperties").get("PolicyDocument").get("Name")
        elif os.environ.get("STAGE_NAME").upper() == "STACKSET":
            return sm_input.get("ResourceProperties").get("StackSetName")
        else:
            return str(uuid4())  # return random string

    def setup_execution(self, sm_input, name):
        self.logger.info("State machine Input: {}".format(sm_input))

        # set execution name
        exec_name = "%s-%s-%s" % (
            sm_input.get("RequestType"),
            trim_length_from_end(name.replace(" ", ""), 50),
            time.strftime("%Y-%m-%dT%H-%M-%S"),
        )

        # execute all SM at regular interval of wait_time
        return self.state_machine.start_execution(
            os.environ.get("SM_ARN"), sm_input, exec_name
        )

    def populate_ssm_params(self, sm_input):
        """The scenario is if you have one CFN resource that exports output
        from CFN stack to SSM parameter and then the next CFN resource
        reads the SSM parameter as input, then it has to wait for the first
        CFN resource to finish; read the SSM parameters and use its value
        as input for second CFN resource's input for SM. Get the parameters
        for CFN template from sm_input
        """
        self.logger.info(
            "Populating SSM parameter values for SM input: {}".format(sm_input)
        )
        params = sm_input.get("ResourceProperties").get("Parameters", {})
        # First transform it from {name: value} to [{'ParameterKey': name},
        # {'ParameterValue': value}]
        # then replace the SSM parameter names with its values
        sm_params = self.param_handler.update_params(transform_params(params))
        # Put it back into the self.state_machine_event
        sm_input.get("ResourceProperties").update({"Parameters": sm_params})
        self.logger.info(
            "Done populating SSM parameter values for SM input:" " {}".format(sm_input)
        )
        return sm_input

    def compare_template_and_params(self, sm_input, stack_name):

        self.logger.info("Comparing the templates and parameters.")
        # Assume that the stack exists, but is not the same state
        stack_set_exist = True
        template_compare, params_compare = False, False
        if stack_name:
            describe_response = self.stack_set.describe_stack_set(stack_name)
            self.logger.info(
                "Print Describe Stack Set Response: {}".format(describe_response)
            )
            if describe_response is not None:
                self.logger.info("Found existing stack set.")

                # Check that the last status was successful
                if self.get_stack_set_operation_status(stack_name):
                    self.logger.info("Continuing...")
                else:
                    # StackSet status was not success
                    return template_compare, params_compare, stack_set_exist

                # Compare template copy - START
                self.logger.info(
                    "Comparing the template of the StackSet:"
                    " {} with local copy of template".format(stack_name)
                )

                template_http_url = sm_input.get("ResourceProperties").get(
                    "TemplateURL", ""
                )
                if template_http_url:
                    bucket_name, key_name, region = parse_bucket_key_names(
                        template_http_url
                    )
                    local_template_file = tempfile.mkstemp()[1]

                    s3_endpoint_url = "https://s3.%s.amazonaws.com" % region
                    s3 = S3(self.logger, region=region, endpoint_url=s3_endpoint_url)
                    s3.download_file(bucket_name, key_name, local_template_file)
                else:
                    self.logger.error(
                        "TemplateURL in state machine input "
                        "is empty. Check state_machine_event"
                        ":{}".format(sm_input)
                    )
                    return template_compare, params_compare, stack_set_exist

                cfn_template_file = tempfile.mkstemp()[1]
                with open(cfn_template_file, "w") as f:
                    f.write(describe_response.get("StackSet").get("TemplateBody"))
                # cmp function return true of the contents are same
                template_compare = filecmp.cmp(
                    local_template_file, cfn_template_file, False
                )
                self.logger.info(
                    "Comparing the parameters of the StackSet"
                    ": {} with local copy of JSON parameters"
                    " file".format(stack_name)
                )

                params_compare = True
                params = sm_input.get("ResourceProperties").get("Parameters", {})
                # template are same - compare parameters (skip if template
                # are not same)
                if template_compare:
                    cfn_params = reverse_transform_params(
                        describe_response.get("StackSet").get("Parameters")
                    )
                    for key, value in params.items():
                        if cfn_params.get(key, "") != value:
                            params_compare = False
                            break

                self.logger.info(
                    "template_compare={}; params_compare={}".format(
                        template_compare, params_compare
                    )
                )
            else:
                # Stack set did not exist
                self.logger.info(
                    "Stack Set does not exist. " "Creating a new stack set ...."
                )
                template_compare, params_compare = True, True
                stack_set_exist = False

        return template_compare, params_compare, stack_set_exist

    def get_stack_set_operation_status(self, stack_name):
        self.logger.info(
            "Checking the status of last stack set "
            "operation on {}".format(stack_name)
        )
        response = self.stack_set.list_stack_set_operations(
            StackSetName=stack_name, MaxResults=1
        )
        if response and response.get("Summaries"):
            for instance in response.get("Summaries"):
                self.logger.info(
                    "Status of last stack set "
                    "operation : {}".format(instance.get("Status"))
                )
                if instance.get("Status") != "SUCCEEDED":
                    self.logger.info(
                        "The last stack operation"
                        " did not succeed. "
                        "Triggering "
                        " Update StackSet for {}".format(stack_name)
                    )
                    return False
        return True

    def compare_stack_instances(self, sm_input: dict, stack_name: str) -> bool:
        """
            Compares deployed stack instances with expected accounts
            & regions for a given StackSet
        :param sm_input: state machine input
        :param stack_name: stack set name
        :return: boolean
        # True: if the SM execution needs to make CRUD operations
         on the StackSet
        # False: if no changes to stack instances are required
        """
        self.logger.info(
            "Comparing deployed stack instances with "
            "expected accounts & regions for "
            "StackSet: {}".format(stack_name)
        )
        expected_account_list = sm_input.get("ResourceProperties").get(
            "AccountList", []
        )
        expected_region_list = sm_input.get("ResourceProperties").get("RegionList", [])

        (
            actual_account_list,
            actual_region_list,
        ) = self.stack_set.get_accounts_and_regions_per_stack_set(stack_name)

        self.logger.info(
            "*** Stack instances expected to be deployed " "in following accounts. ***"
        )
        self.logger.info(expected_account_list)
        self.logger.info(
            "*** Stack instances actually deployed " "in following accounts. ***"
        )
        self.logger.info(actual_account_list)
        self.logger.info(
            "*** Stack instances expected to be deployed " "in following regions. ***"
        )
        self.logger.info(expected_region_list)
        self.logger.info(
            "*** Stack instances actually deployed " "in following regions. ***"
        )
        self.logger.info(actual_region_list)

        self.logger.info("*** Comparing account lists ***")
        accounts_matched = compare_lists(actual_account_list, expected_account_list)
        self.logger.info("*** Comparing region lists ***")
        regions_matched = compare_lists(
            actual_region_list,
            expected_region_list,
        )
        if accounts_matched and regions_matched:
            self.logger.info("No need to add or remove stack instances.")
            return False
        else:
            self.logger.info("Stack instance(s) creation or deletion needed.")
            return True

    def monitor_state_machines_execution_status(
        self, sm_execution_arns: list, retry_wait_time: int
    ):

        # Assume we succeed until a failure is observed
        overall_status = "SUCCEEDED"
        failed_executions = []

        for exec_arn in sm_execution_arns:
            # Check-sleep cycle until the execution finishes
            exec_status = self.state_machine.check_state_machine_status(exec_arn)
            while exec_status == "RUNNING":
                time.sleep(int(retry_wait_time))
                exec_status = self.state_machine.check_state_machine_status(exec_arn)

            if exec_status == "SUCCEEDED":
                continue
            else:
                # One observed failure -> report overall failure
                overall_status = "FAILED"
                failed_executions.append(exec_arn)

        return overall_status, failed_executions

    def enforce_stack_set_deployment_successful(self, stack_set_name: str) -> None:
        failed_detailed_statuses = ["CANCELLED", "FAILED", "INOPERABLE"]
        list_filters = [
            {"Name": "DETAILED_STATUS", "Values": status}
            for status in failed_detailed_statuses
        ]
        # Note that we don't paginate because if this API returns any elements, failed instances exist.
        for list_filter in list_filters:
            response = self.stack_set.cfn_client.list_stack_instances(
                StackSetName=stack_set_name, Filters=[list_filter]
            )
            if response.get("Summaries", []):
                raise StackSetHasFailedInstances(
                    stack_set_name=stack_set_name,
                    failed_stack_set_instances=response["Summaries"],
                )
        return None
