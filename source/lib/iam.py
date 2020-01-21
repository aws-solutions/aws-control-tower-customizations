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

class IAM(object):

    def __init__(self, logger, region, **kwargs):
        self.logger = logger
        if kwargs is not None:
            if kwargs.get('credentials') is None:
                logger.debug("Setting up IAM BOTO3 Client with default credentials")
                self.iam_client = boto3.client('iam', region_name=region)
            else:
                logger.debug("Setting up IAM BOTO3 Client with ASSUMED ROLE credentials")
                cred = kwargs.get('credentials')
                self.iam_client = boto3.client('iam', region_name=region,
                                               aws_access_key_id=cred.get('AccessKeyId'),
                                               aws_secret_access_key=cred.get('SecretAccessKey'),
                                               aws_session_token=cred.get('SessionToken')
                                               )
        else:
            logger.info("There were no keyworded variables passed.")
            self.iam_client = boto3.client('iam', region_name=region)

    def update_assume_role_policy(self, role_name, policy):
        try:
            self.iam_client.update_assume_role_policy(
                RoleName=role_name,
                PolicyDocument=policy
            )
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

