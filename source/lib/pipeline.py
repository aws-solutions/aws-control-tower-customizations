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

#!/bin/python

import boto3
import json
import inspect

class CodePipeline(object):
    def __init__(self, logger):
        self.logger = logger
        self.codepipeline_client = boto3.client('codepipeline')
        self.job_id = None
        self.continuation_token = None
        self.job_data = None

    def put_job_success(self):
        try:
            self.logger.info("Signaling completion to pipeline for job: {}".format(self.job_id))
            self.codepipeline_client.put_job_success_result(jobId=self.job_id)
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def put_job_failure(self, message):
        try:
            if len(message) > 265:
                message = message[0:211] + '... For full details see CloudWatch logs.'
            self.logger.info("Signaling failure to pipeline for job: {} errorMessage: {}".format(self.job_id, message));

            self.codepipeline_client.put_job_failure_result(
                jobId=self.job_id,
                failureDetails={'message': message, 'type': 'JobFailed'}
            )
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def get_artifact_location(self, name):
        artifacts = self.job_data['inputArtifacts']
        for artifact in artifacts:
            if artifact['name'] == name:
                bucket = artifact['location']['s3Location']['bucketName']
                key = artifact['location']['s3Location']['objectKey']
                return bucket, key

        raise Exception('Input artifact named "{0}" not found in event'.format(name))

    def get_credentials(self):
        credentials = {}
        credentials['aws_access_key_id'] = self.job_data['artifactCredentials']['accessKeyId']
        credentials['aws_secret_access_key'] = self.job_data['artifactCredentials']['secretAccessKey']
        credentials['aws_session_token'] = self.job_data['artifactCredentials']['sessionToken']
        return credentials

    def get_user_params(self):
        try:
            # Get the user parameters which contain the stack, artifact and file settings
            user_parameters = self.job_data['actionConfiguration']['configuration']['UserParameters']
            decoded_parameters = json.loads(user_parameters)

            if 'pipeline_stage' not in decoded_parameters:
                raise Exception('Your UserParameters JSON must include the pipeline_stage parameter')

            if 'artifact' not in decoded_parameters:
                raise Exception('Your UserParameters JSON must include the artifact parameter')

            return decoded_parameters
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def continue_job_later(self, message=''):
        try:
            self.logger.debug("Continue Job later...")
            self.logger.info("Signaling continuation to pipeline for job: {} continuationToken: {}".format(self.job_id, self.continuation_token));

            self.codepipeline_client.put_job_success_result(
                jobId=self.job_id,
                continuationToken=self.continuation_token
            )
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def is_continuing_pipeline_task(self):
        if 'continuationToken' not in self.job_data:
            return False
        else:
            return True

    def parse_event(self, event):
        try:
            self.logger.debug("Parse Lambda event information for pipeline Job details")
            self.job_id = event['CodePipeline.job']['id']
            self.job_data = event['CodePipeline.job']['data']
            if self.is_continuing_pipeline_task():
                self.continuation_token = self.job_data['continuationToken']
            else:
                self.continuation_token = self.job_id
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise
