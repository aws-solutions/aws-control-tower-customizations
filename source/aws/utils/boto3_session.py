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
import boto3


class Boto3Session:
    """This class initialize boto3 client for a given AWS service name.

    Example:
        class EC2(Boto3Session):
            def __init__(self, logger, region, **kwargs):
                self.logger = logger
                __service_name = 'ec2'
                kwargs.update({'region': region}) # optional
                super().__init__(logger, __service_name, **kwargs)
                self.ec2_client = super().get_client()
    """
    def __init__(self, logger, service_name, **kwargs):
        """
            Parameters
            ----------
            logger : object
                The logger object
            region : str
                AWS region name. Example: 'us-east-1'
            service_name : str
                AWS service name. Example: 'ec2'
            credentials = dict, optional
                set of temporary AWS security credentials
            endpoint_url : str
                The complete URL to use for the constructed client.
        """
        self.logger = logger
        self.service_name = service_name
        self.credentials = kwargs.get('credentials', None)
        self.region = kwargs.get('region', None)
        self.endpoint_url = kwargs.get('endpoint_url', None)

    def get_client(self):
        """Creates a boto3 low-level service client by name.

        Returns: service client, type: Object
        """
        if self.credentials is None:
            if self.endpoint_url is None:
                return boto3.client(self.service_name, region_name=self.region)
            else:
                return boto3.client(self.service_name, region_name=self.region,
                                    endpoint_url=self.endpoint_url)
        else:
            if self.region is None:
                return boto3.client(self.service_name,
                                    aws_access_key_id=self.credentials
                                    .get('AccessKeyId'),
                                    aws_secret_access_key=self.credentials
                                    .get('SecretAccessKey'),
                                    aws_session_token=self.credentials
                                    .get('SessionToken')
                                    )
            else:
                return boto3.client(self.service_name,
                                    region_name=self.region,
                                    aws_access_key_id=self.credentials
                                    .get('AccessKeyId'),
                                    aws_secret_access_key=self.credentials
                                    .get('SecretAccessKey'),
                                    aws_session_token=self.credentials
                                    .get('SessionToken')
                                    )

    def get_resource(self):
        """Creates a boto3 resource service client object by name

        Returns: resource service client, type: Object
        """
        if self.credentials is None:
            if self.endpoint_url is None:
                return boto3.resource(self.service_name,
                                      region_name=self.region)
            else:
                return boto3.resource(self.service_name,
                                      region_name=self.region,
                                      endpoint_url=self.endpoint_url)
        else:
            if self.region is None:
                return boto3.resource(self.service_name,
                                      aws_access_key_id=self.credentials
                                      .get('AccessKeyId'),
                                      aws_secret_access_key=self.credentials
                                      .get('SecretAccessKey'),
                                      aws_session_token=self.credentials
                                      .get('SessionToken')
                                      )
            else:
                return boto3.resource(self.service_name,
                                      region_name=self.region,
                                      aws_access_key_id=self.credentials
                                      .get('AccessKeyId'),
                                      aws_secret_access_key=self.credentials
                                      .get('SecretAccessKey'),
                                      aws_session_token=self.credentials
                                      .get('SessionToken')
                                      )
