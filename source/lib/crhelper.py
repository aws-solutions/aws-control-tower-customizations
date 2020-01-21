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

import threading
import requests
import json


def send(event, context, responseStatus, responseData, physicalResourceId,
         logger, reason=None):

    responseUrl = event['ResponseURL']
    logger.debug("CFN response URL: " + responseUrl)

    responseBody = {}
    responseBody['Status'] = responseStatus
    msg = 'See details in CloudWatch Log Stream: ' + context.log_stream_name
    if not reason:
        responseBody['Reason'] = msg
    else:
        responseBody['Reason'] = str(reason)[0:255] + '... ' + msg
    responseBody['PhysicalResourceId'] = physicalResourceId or context.log_stream_name
    responseBody['StackId'] = event['StackId']
    responseBody['RequestId'] = event['RequestId']
    responseBody['LogicalResourceId'] = event['LogicalResourceId']
    if responseData and responseData != {} and responseData != [] and isinstance(responseData, dict):
        responseBody['Data'] = responseData

    logger.debug("<<<<<<< Response body >>>>>>>>>>")
    logger.debug(responseBody)
    json_responseBody = json.dumps(responseBody)

    headers = {
        'content-type': '',
        'content-length': str(len(json_responseBody))
    }

    try:
        if responseUrl == 'http://pre-signed-S3-url-for-response':
            logger.info("CloudFormation returned status code: THIS IS A TEST OUTSIDE OF CLOUDFORMATION")
            pass
        else:
            response = requests.put(responseUrl,
                                    data=json_responseBody,
                                    headers=headers)
            logger.info("CloudFormation returned status code: " + response.reason)
    except Exception as e:
        logger.error("send(..) failed executing requests.put(..): " + str(e))
        raise


# Function that executes just before lambda excecution times out
def timeout(event, context, logger):
    logger.error("Execution is about to time out, sending failure message")
    send(event, context, "FAILED", None, None, reason="Execution timed out",
         logger=logger)


# Handler function
def cfn_handler(event, context, create, update, delete, logger, init_failed):

    logger.info("Lambda RequestId: %s CloudFormation RequestId: %s" % (context.aws_request_id, event['RequestId']))

    # Define an object to place any response information you would like to send
    # back to CloudFormation (these keys can then be used by Fn::GetAttr)
    responseData = {}

    # Define a physicalId for the resource, if the event is an update and the
    # returned phyiscalid changes, cloudformation will then issue a delete
    # against the old id
    physicalResourceId = None

    logger.debug("EVENT: " + str(event))
    # handle init failures
    if init_failed:
        send(event, context, "FAILED", responseData, physicalResourceId, logger, reason="Initialization Failed")
        raise Exception("Initialization Failed")

    # Setup timer to catch timeouts
    t = threading.Timer((context.get_remaining_time_in_millis()/1000.00)-0.5, timeout, args=[event, context, logger])
    t.start()

    try:
        # Execute custom resource handlers
        logger.info("Received a %s Request" % event['RequestType'])
        if event['RequestType'] == 'Create':
            physicalResourceId, responseData = create(event, context)
        elif event['RequestType'] == 'Update':
            physicalResourceId, responseData = update(event, context)
        elif event['RequestType'] == 'Delete':
            delete(event, context)

        # Send response back to CloudFormation
        logger.info("Completed successfully, sending response to cfn")
        send(event, context, "SUCCESS", responseData, physicalResourceId, logger=logger)

    # Catch any exceptions, log the stacktrace, send a failure back to
    # CloudFormation and then raise an exception
    except Exception as e:
        logger.error(e, exc_info=True)
        send(event, context, "FAILED", responseData, physicalResourceId, reason=e, logger=logger)
    finally:
        t.cancel()
