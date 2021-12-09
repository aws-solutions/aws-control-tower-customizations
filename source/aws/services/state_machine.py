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

import boto3
import json
from botocore.exceptions import ClientError
from utils.string_manipulation import sanitize
from aws.utils.boto3_session import Boto3Session


class StateMachine(Boto3Session):
    def __init__(self, logger, **kwargs):
        self.logger = logger
        __service_name = 'stepfunctions'
        super().__init__(logger, __service_name, **kwargs)
        self.state_machine_client = super().get_client()

    def start_execution(self, state_machine_arn, input, name):
        try:
            self.logger.info("Starting execution of state machine: {} with "
                             "input: {}".format(state_machine_arn, input))
            response = self.state_machine_client.start_execution(
                stateMachineArn=state_machine_arn,
                input=json.dumps(input),
                name=sanitize(name)
            )
            self.logger.info("State machine Execution ARN: {}"
                             .format(response['executionArn']))
            return response.get('executionArn')
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def check_state_machine_status(self, execution_arn):
        try:
            self.logger.info("Checking execution of state machine: {}"
                             .format(execution_arn))
            response = self.state_machine_client.describe_execution(
                executionArn=execution_arn
            )
            self.logger.info("State machine Execution Status: {}"
                             .format(response['status']))
            if response['status'] == 'RUNNING':
                return 'RUNNING'
            elif response['status'] == 'SUCCEEDED':
                return 'SUCCEEDED'
            else:
                return 'FAILED'
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise
