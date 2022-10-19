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

from botocore.exceptions import ClientError
from cfct.aws.utils.boto3_session import Boto3Session


class KMS(Boto3Session):
    """This class makes KMS API calls as needed."""

    def __init__(self, logger, **kwargs):
        self.logger = logger
        __service_name = "kms"
        super().__init__(logger, __service_name, **kwargs)
        self.kms_client = super().get_client()

    def describe_key(self, alias_name):
        try:
            key_id = "alias/" + alias_name
            response = self.kms_client.describe_key(KeyId=key_id)
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def create_key(self, policy, description, tag_key, tag_value):
        try:
            response = self.kms_client.create_key(
                Policy=policy,
                Description=description,
                KeyUsage="ENCRYPT_DECRYPT",
                Origin="AWS_KMS",
                BypassPolicyLockoutSafetyCheck=True,
                Tags=[
                    {"TagKey": tag_key, "TagValue": tag_value},
                ],
            )
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def create_alias(self, alias_name, key_name):
        try:
            response = self.kms_client.create_alias(
                AliasName=alias_name, TargetKeyId=key_name
            )
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def list_aliases(self, marker=None):
        try:
            if marker:
                response = self.kms_client.list_aliases(Marker=marker)
            else:
                response = self.kms_client.list_aliases()
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def put_key_policy(self, key_id, policy):
        try:
            response = self.kms_client.put_key_policy(
                KeyId=key_id,
                Policy=policy,
                # Per API docs, the only valid value is default.
                PolicyName="default",
                BypassPolicyLockoutSafetyCheck=True,
            )
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def enable_key_rotation(self, key_id):
        try:
            response = self.get_key_rotation_status(key_id)

            # Enable auto key rotation only if it hasn't been enabled
            if not response.get("KeyRotationEnabled"):
                self.kms_client.enable_key_rotation(KeyId=key_id)
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def get_key_rotation_status(self, key_id):
        try:
            response = self.kms_client.get_key_rotation_status(KeyId=key_id)
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise
