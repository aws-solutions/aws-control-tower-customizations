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
kms_client = boto3.client('kms')


class KMS(object):
    def __init__(self, logger):
        self.logger = logger

    def describe_key(self, alias_name):
        try:
            key_id = 'alias/' + alias_name
            response = kms_client.describe_key(
                KeyId=key_id
            )
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def create_key(self, policy, description="CMK created for Custom Control Tower Resources"):
        try:
            response = kms_client.create_key(
                Policy=policy,
                Description=description,
                KeyUsage='ENCRYPT_DECRYPT',
                Origin='AWS_KMS',
                BypassPolicyLockoutSafetyCheck=True,
                Tags=[
                    {
                        'TagKey': 'AWSSolutions',
                        'TagValue': 'CustomControlTower'
                    },
                ]
            )
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def create_alias(self, alias_name, key_name):
        try:
            response = kms_client.create_alias(
                AliasName=alias_name,
                TargetKeyId=key_name
            )
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def list_aliases(self, marker=None):
        try:
            if marker:
                response = kms_client.list_aliases(Marker=marker)
            else:
                response = kms_client.list_aliases()
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def put_key_policy(self, key_id, policy):
        try:
            response = kms_client.put_key_policy(
                KeyId=key_id,
                Policy=policy,
                PolicyName = 'default', # Per API docs, the only valid value is default.
                BypassPolicyLockoutSafetyCheck=True
            )
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise
        
    def enable_key_rotation(self, key_id):
        try:
            response = self.get_key_rotation_status(key_id)
            
            # Enable auto key rotation only if it hasn't been enabled
            if not response.get('KeyRotationEnabled'):
                 kms_client.enable_key_rotation(KeyId=key_id)
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                        'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise
        
    def get_key_rotation_status(self, key_id):
        try:
            response = kms_client.get_key_rotation_status(
                KeyId=key_id
            )
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                        'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise