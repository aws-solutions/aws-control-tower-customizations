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
import os
from aws.services.s3 import S3
from aws.utils.url_conversion import convert_s3_url_to_http_url


class StageFile(S3):
    """This class uploads the file to S3 for staging.

    Example:
        boto_3 = Boto3Session(logger, region, service_name, **kwargs)
        client = boto_3.get_client()
    """
    def __init__(self, logger, relative_file_path):
        """
            Parameters
            ----------
            logger : object
                The logger object
            relative_file_path : str
                Relative Path of the file.
        """
        self.logger = logger
        self.relative_file_path = relative_file_path
        super().__init__(logger)

    def get_staged_file(self):
        """Returns S3 URL for the local file

        :return: S3 URL, type: String
        """

        if self.relative_file_path.lower().startswith('s3'):
            return self.convert_url()
        else:
            return self.stage_file()

    def convert_url(self):
        """Convert the S3 URL s3://bucket-name/object
        to HTTP URL https://s3.amazonaws.com/bucket-name/object
        """
        return convert_s3_url_to_http_url(self.relative_file_path)

    def stage_file(self):
        """Uploads local file to S3 bucket and returns S3 URL
           for the local file.

        :return: S3 URL, type: String
        """
        local_file = os.path.join(os.environ.get('MANIFEST_FOLDER'),
                                  self.relative_file_path)
        remote_file = "{}/{}".format(os.environ.get('TEMPLATE_KEY_PREFIX'),
                                     self.relative_file_path)
        self.logger.info("Uploading the template file: {} to S3 bucket: {}  "
                         "and key: {}".format(local_file,
                                              os.environ.get('STAGING_BUCKET'),
                                              remote_file))
        super().upload_file(os.environ.get('STAGING_BUCKET'),
                            local_file,
                            remote_file)
        s3_url = "{}{}/{}".format('https://s3.amazonaws.com/',
                                  os.environ.get('STAGING_BUCKET'),
                                  remote_file)
        return s3_url
