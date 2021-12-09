
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

import os
import inspect
from utils.logger import Logger
from aws.services.code_pipeline import CodePipeline

# initialise logger
log_level = 'info' if os.environ.get('LOG_LEVEL') is None \
            else os.environ.get('LOG_LEVEL')
logger = Logger(loglevel=log_level)
init_failed = False


def invoke_code_pipeline(event):
    """Invokes code pipeline execution if there are any control tower
       lifecycle events in the SQS FIFO queue.

    Note:
        Here validates that the event source is aws control tower.
        The filtering of specific control tower lifecycle events is done
        by a CWE rule, which is configured to deliver only
        the matching events to the SQS queue.

    Args:
        event
    Returns:
        response from starting pipeline execution
    """
    msg_count = 0
    for record in event['Records']:
        # Here validates that the event source is aws control tower.
        # The filtering of specific control tower lifecycle events is done
        # by a CWE rule, which is configured to deliver only
        # the matching events to the SQS queue.
        if record['body'] is not None and record['body'].find('"source":"aws.controltower"') >= 0:
            msg_count += 1

    if msg_count > 0:
        logger.info(str(msg_count) +
                    " Control Tower lifecycle event(s) found in the queue."
                    " Start invoking code pipeline...")

        cp = CodePipeline(logger)
        response = cp.start_pipeline_execution(
                    os.environ.get('CODE_PIPELINE_NAME'))
    else:
        logger.info("No lifecycle events in the queue!")

    return response


def lambda_handler(event, context):
    """This lambda is invoked by a SQS FIFO queue as the lambda trigger.
       A CWE rule is defined to deliver only matching AWS control tower
       lifecycle events to the queue. Once the queue receives the events,
       it will trigger the lambda to start code pipeline execution.

    Args:
        event
        context
    """
    try:
        logger.info("<<<<<<<<<< Poll Control Tower lifecyle events from"
                    " SQS queue >>>>>>>>>>")
        logger.info(event)
        logger.debug(context)

        response = invoke_code_pipeline(event)

        logger.info("Response from Code Pipeline: ")
        logger.info(response)
    except Exception as e:
        logger.log_general_exception(
            __file__.split('/')[-1], inspect.stack()[0][3], e)
        raise
