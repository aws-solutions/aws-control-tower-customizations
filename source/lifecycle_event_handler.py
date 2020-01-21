
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
import os
import inspect
from lib.code_pipeline import CodePipeline

# initialise logger
log_level = 'info' if os.environ.get('log_level') is None else os.environ.get('log_level')
logger = Logger(loglevel=log_level)
init_failed = False

# Invoke code pipeline if there are any control tower lifecycly events in the queue
def invoke_code_pipeline(event):
    try:
        msg_count=0
        for record in event['Records']:
            if record['body'] is not None:
                msg_count+=1
           
        if msg_count > 0:      
            logger.info(str(msg_count) + " Control Tower lifecycle events are found in the queue. Start invoking code pipeline...")
         
            cp = CodePipeline(logger)
            response=cp.start_pipeline_execution(os.environ.get('code_pipeline_name'))   
        else:
            logger.info("No lifecycle events in the queue!") 
        
        return response                   
    except Exception as e:
        message = {'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
        logger.exception(message)
        raise
        
def lambda_handler(event, context):
    logger.info("<<<<<<<<<< Poll Control Tower lifecyle events from SQS queue >>>>>>>>>>")
    logger.info(event)
    logger.debug(context)

    response=invoke_code_pipeline(event)
    
    logger.info("Response from Code Pipeline: ")
    logger.info(response)