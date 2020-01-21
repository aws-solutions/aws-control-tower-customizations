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
from lib.decorator import try_except_retry
import boto3
import inspect
import os
ssm_region = os.environ.get('AWS_REGION')

class SSM(object):
    def __init__(self, logger, region=ssm_region, **kwargs):
        self.logger = logger
        if kwargs is not None:
            if kwargs.get('credentials') is None:
                logger.debug("Setting up SSM BOTO3 Client with default credentials")
                self.ssm_client = boto3.client('ssm', region_name=region)
            else:
                logger.debug("Setting up SSM BOTO3 Client with ASSUMED ROLE credentials")
                cred = kwargs.get('credentials')
                self.ssm_client = boto3.client('ssm', region_name=region,
                                               aws_access_key_id=cred.get('AccessKeyId'),
                                               aws_secret_access_key=cred.get('SecretAccessKey'),
                                               aws_session_token=cred.get('SessionToken')
                                               )
        else:
            logger.info("There were no keyworded variables passed.")
            self.ssm_client = boto3.client('ssm', region_name=region)

    def put_parameter(self, name, value, description="This value was stored by Custom Control Tower Solution.",
                      type='String', overwrite=True):
        try:
            response = self.ssm_client.put_parameter(
                Name=name,
                Value=value,
                Description=description,
                Type=type,
                Overwrite=overwrite
            )
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def put_parameter_use_cmk(self, name, value, key_id, description="This value was stored by Custom Control Tower Solution.",
                      type='SecureString', overwrite=True):
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
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def get_parameter(self, name):
        try:
            response = self.ssm_client.get_parameter(
                Name=name,
                WithDecryption=True
            )
            return response.get('Parameter', {}).get('Value')
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def delete_parameter(self, name):
        try:
            response = self.ssm_client.delete_parameter(
                # Name (string)
                Name=name
            )
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
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
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def delete_parameters_by_path(self, name):
        try:
            params_list = self.get_parameters_by_path(name)
            if params_list:
                for param in params_list:
                    self.delete_parameter(param.get('Name'))
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
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
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise