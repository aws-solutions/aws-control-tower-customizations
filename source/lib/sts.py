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
import inspect
from botocore.exceptions import ClientError
from lib.helper import get_sts_region, get_sts_endpoint

sts_client = boto3.client('sts',
                          region_name=get_sts_region(),
                          endpoint_url=get_sts_endpoint())


class STS(object):
    def __init__(self, logger):
        self.logger = logger

    def assume_role(self, role_arn, session_name, duration=900):
        try:
            response = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName=session_name,
                DurationSeconds=duration
            )
            return response['Credentials']
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def assume_role_new_account(self, role_arn, session_name, duration=900):
        try:
            response = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName=session_name,
                DurationSeconds=duration
            )
            return response['Credentials']
        except ClientError as e:
            self.logger.exception(e.response['Error']['Code'])
            if e.response['Error']['Code'] == 'AccessDenied':
                return {'Error': 'AWS STS AssumeRole Failure: Access Denied.'}
            elif e.response['Error']['Code'] == 'RegionDisabledException':
                return {'Error': 'An error occurred (RegionDisabledException) when calling the AssumeRole operation: '
                                 'STS is not activated in this region for this account.'}
            else:
                message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
                self.logger.exception(message)
                raise

    def get_caller_identity(self):
        try:
            response = sts_client.get_caller_identity()
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise
