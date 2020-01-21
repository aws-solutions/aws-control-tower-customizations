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
import json
import inspect
from botocore.exceptions import ClientError

class ServiceControlPolicy(object):
    def __init__(self, logger):
        self.logger = logger
        self.org_client = boto3.client('organizations')

    def list_policies(self, max_items=100, page_size=20):
        try:
            paginator = self.org_client.get_paginator('list_policies')
            response_iterator = paginator.paginate(
                Filter='SERVICE_CONTROL_POLICY',
                PaginationConfig={
                    'MaxItems': max_items,
                    'PageSize': page_size
                }
            )
            return response_iterator
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def list_policies_for_target(self, target_id, max_items=100, page_size=20):
        try:
            paginator = self.org_client.get_paginator('list_policies_for_target')
            response_iterator = paginator.paginate(
                TargetId=target_id,
                Filter='SERVICE_CONTROL_POLICY',
                PaginationConfig={
                    'MaxItems': max_items,
                    'PageSize': page_size
                }
            )
            return response_iterator
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def list_targets_for_policy(self, policy_id, max_items=100, page_size=20):
        try:
            paginator = self.org_client.get_paginator('list_targets_for_policy')
            response_iterator = paginator.paginate(
                PolicyId=policy_id,
                PaginationConfig={
                    'MaxItems': max_items,
                    'PageSize': page_size
                }
            )
            return response_iterator
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def create_policy(self, name, description, content):
        try:
            response = self.org_client.create_policy(
                Content=content,
                Description=description,
                Name=name,
                Type='SERVICE_CONTROL_POLICY'
            )
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def update_policy(self, policy_id, name, description, content):
        try:
            response = self.org_client.update_policy(
                PolicyId=policy_id,
                Name=name,
                Description=description,
                Content=content
            )
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def delete_policy(self, policy_id):
        try:
            self.org_client.delete_policy(
                PolicyId=policy_id
            )
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def attach_policy(self, policy_id, target_id):
        try:
            self.org_client.attach_policy(
                PolicyId=policy_id,
                TargetId=target_id
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'DuplicatePolicyAttachmentException':
                self.logger.exception("Caught exception 'DuplicatePolicyAttachmentException', taking no action...")
                return
            else:
                message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
                self.logger.exception(message)
                raise

    def detach_policy(self, policy_id, target_id):
        try:
            self.org_client.detach_policy(
                PolicyId=policy_id,
                TargetId=target_id
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'PolicyNotAttachedException':
                self.logger.exception("Caught exception 'PolicyNotAttachedException', taking no action...")
                return
            else:
                message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
                self.logger.exception(message)
                raise

        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def enable_policy_type(self, root_id):
        try:
            self.org_client.enable_policy_type(
                RootId=root_id,
                PolicyType='SERVICE_CONTROL_POLICY'
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'PolicyTypeAlreadyEnabledException':
                pass
            else:
                raise
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise
