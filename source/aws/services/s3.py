##############################################################################
#  Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.   #
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

import tempfile
from botocore.exceptions import ClientError
from aws.utils.boto3_session import Boto3Session


class S3(Boto3Session):
    def __init__(self, logger, **kwargs):
        self.logger = logger
        __service_name = 's3'
        super().__init__(logger, __service_name, **kwargs)
        self.s3_client = super().get_client()
        self.s3_resource = super().get_resource()

    def get_bucket_policy(self, bucket_name):
        try:
            response = self.s3_client.get_bucket_policy(
                Bucket=bucket_name
            )
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def put_bucket_policy(self, bucket_name, bucket_policy):
        try:
            response = self.s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=bucket_policy
            )
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def upload_file(self, bucket_name, local_file_location,
                    remote_file_location):
        try:
            self.s3_resource.Bucket(bucket_name).upload_file(
                local_file_location, remote_file_location)
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def download_file(self, bucket_name, remote_file_location,
                      local_file_location):
        try:
            self.s3_resource.Bucket(bucket_name).download_file(
                remote_file_location, local_file_location)
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def put_bucket_encryption(self, bucket_name, key_id):
        try:
            self.s3_client.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'aws:kms',
                                'KMSMasterKeyID': key_id
                            }
                        },
                    ]
                }
            )

        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def list_buckets(self):
        self.logger.info(self.s3_client.list_buckets())

    def download_remote_file(self, remote_s3_path):
        try:
            _file = tempfile.mkstemp()[1]
            t = remote_s3_path.split("/", 3)  # s3://bucket-name/key
            remote_bucket = t[2]  # Bucket name
            remote_key = t[3]  # Key
            self.logger.info("Downloading {}/{} from S3 to {}".format(
                remote_bucket, remote_key, _file))
            self.s3_client.download_file(remote_bucket, remote_key, _file)
            return _file
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise
