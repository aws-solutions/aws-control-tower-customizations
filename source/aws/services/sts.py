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

# !/bin/python

from os import environ
from botocore.exceptions import ClientError
from aws.utils.boto3_session import Boto3Session
from aws.utils.get_partition import get_partition


class AssumeRole(object):
    def __call__(self, logger, account):
        try:
            sts = STS(logger)
            # assume role
            session_name = "custom-control-tower-session"
            partition = get_partition()
            role_arn = "%s%s%s%s%s%s" % ("arn:",
                                         partition,
                                         ":iam::",
                                         str(account),
                                         ":role/",
                                         environ.get('EXECUTION_ROLE_NAME'))
            credentials = sts.assume_role(role_arn, session_name)
            return credentials
        except ClientError as e:
            logger.log_unhandled_exception(e)
            raise


class STS(Boto3Session):
    def __init__(self, logger, **kwargs):
        self.logger = logger
        __service_name = 'sts'
        kwargs.update({'region': self.get_sts_region})
        kwargs.update({'endpoint_url': self.get_sts_endpoint()})
        super().__init__(logger, __service_name, **kwargs)
        self.sts_client = super().get_client()

    @property
    def get_sts_region(self):
        return environ.get('AWS_REGION')

    @staticmethod
    def get_sts_endpoint():
        return "https://sts.%s.amazonaws.com" % environ.get('AWS_REGION')

    def assume_role(self, role_arn, session_name, duration=900):
        try:
            response = self.sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName=session_name,
                DurationSeconds=duration
            )
            return response['Credentials']
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def get_caller_identity(self):
        try:
            response = self.sts_client.get_caller_identity()
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise
