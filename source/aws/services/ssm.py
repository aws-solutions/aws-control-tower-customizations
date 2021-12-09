##############################################################################
#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.   #
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
from botocore.exceptions import ClientError
from utils.retry_decorator import try_except_retry
from aws.utils.boto3_session import Boto3Session

ssm_region = os.environ.get('AWS_REGION')


class SSM(Boto3Session):
    def __init__(self, logger, region=ssm_region, **kwargs):
        self.logger = logger
        __service_name = 'ssm'
        kwargs.update({'region': region})
        super().__init__(logger, __service_name, **kwargs)
        self.ssm_client = super().get_client()
        self.description = "This value was stored by Custom Control "
        "Tower Solution."

    def put_parameter(self,
                      name,
                      value,
                      description="This value was stored by Custom Control "
                                  "Tower Solution.",
                      type='String',
                      overwrite=True):
        try:
            response = self.ssm_client.put_parameter(
                Name=name,
                Value=value,
                Description=description,
                Type=type,
                Overwrite=overwrite
            )
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def put_parameter_use_cmk(self,
                              name,
                              value,
                              key_id,
                              description="This value was stored by Custom "
                                          "Control Tower Solution.",
                              type='SecureString',
                              overwrite=True):
        try:
            response = self.ssm_client.put_parameter(
                Name=name,
                Value=value,
                Description=description,
                KeyId=key_id,
                Type=type,
                Overwrite=overwrite
            )
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def get_parameter(self, name):
        try:
            response = self.ssm_client.get_parameter(
                Name=name,
                WithDecryption=True
            )
            return response.get('Parameter', {}).get('Value')
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                self.logger.log_unhandled_exception('The SSM Parameter {} was not found'.format(name))
            self.logger.log_unhandled_exception(e)
            raise

    def delete_parameter(self, name):
        try:
            response = self.ssm_client.delete_parameter(
                # Name (string)
                Name=name
            )
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def get_parameters_by_path(self, path):
        try:
            response = self.ssm_client.get_parameters_by_path(
                Path=path if path.startswith('/') else '/'+path,
                Recursive=False,
                WithDecryption=True
            )
            params_list = response.get('Parameters', [])
            next_token = response.get('NextToken', None)

            while next_token is not None:
                response = self.ssm_client.get_parameters_by_path(
                    Path=path if path.startswith('/') else '/' + path,
                    Recursive=False,
                    WithDecryption=True,
                    NextToken=next_token
                )
                params_list.extend(response.get('Parameters', []))
                next_token = response.get('NextToken', None)

            return params_list
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def delete_parameters_by_path(self, name):
        try:
            params_list = self.get_parameters_by_path(name)
            if params_list:
                for param in params_list:
                    self.delete_parameter(param.get('Name'))
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    @try_except_retry()
    def describe_parameters(self, parameter_name, begins_with=False):
        try:
            response = self.ssm_client.describe_parameters(
                ParameterFilters=[
                    {
                        'Key': 'Name',
                        'Option': 'BeginsWith' if begins_with else 'Equals',
                        'Values': [parameter_name]
                    }
                ]
            )
            parameters = response.get('Parameters', [])
            if parameters:
                return parameters[0]
            else:
                return None
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise
