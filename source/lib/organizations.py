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
from lib.decorator import try_except_retry

org_client = boto3.client('organizations')


class Organizations(object):
    def __init__(self, logger):
        self.logger = logger

    def list_roots(self):
        try:
            response = org_client.list_roots()
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.error(message)
            self.logger.info("Caught exception - returning None")
            return None

    # describe organization
    def describe_org(self):
        try:
            response = org_client.describe_organization()
            return response
        except Exception:
            pass

    # create a new organization
    def create_organization(self, feature_set='ALL'):
        try:
            response = org_client.create_organization(
                FeatureSet=feature_set
            )
            return response
        except Exception as e:
            self.logger.info("The organization already exist in this account. This should not impact the workflow.")
            pass

    def list_organizational_units_for_parent(self, parent_id):
        try:
            response = org_client.list_organizational_units_for_parent(
                ParentId=parent_id
            )

            ou_list = response.get('OrganizationalUnits', [])
            next_token = response.get('NextToken', None)

            while next_token is not None:
                self.logger.info("Next Token Returned: {}".format(next_token))
                response = org_client.list_organizational_units_for_parent(
                    ParentId=parent_id,
                    NextToken=next_token
                )
                self.logger.info("Extending OU List")
                ou_list.extend(response.get('OrganizationalUnits', []))
                next_token = response.get('NextToken', None)

            return ou_list

        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def create_organizational_unit(self, parent_id, name):
        try:
            response = org_client.create_organizational_unit(
                ParentId=parent_id,
                Name=name
            )
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'DuplicateOrganizationalUnitException':
                self.logger.info("Caught exception 'DuplicateOrganizationalUnitException', handling the exception...")
                return {"Error": "DuplicateOrganizationalUnitException"}
            else:
                message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
                self.logger.exception(message)
                raise

    def delete_organization_unit(self, ou_id):
        try:
            org_client.delete_organizational_unit(
                OrganizationalUnitId=ou_id
            )
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def list_parents(self,account_id):
        try:
            response = org_client.list_parents(
                ChildId=account_id
            )
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def list_accounts_for_parent(self, parent_id):
        """
        :param parent_id:
        :return:
        {
            'Accounts': [
                {
                    'Id': 'string',
                    'Arn': 'string',
                    'Email': 'string',
                    'Name': 'string',
                    'Status': 'ACTIVE'|'SUSPENDED',
                    'JoinedMethod': 'INVITED'|'CREATED',
                    'JoinedTimestamp': datetime(2015, 1, 1)
                },
            ],
            'NextToken': 'string'
        }
        """
        try:
            response = org_client.list_accounts_for_parent(
                ParentId=parent_id
            )

            account_list = response.get('Accounts', [])
            next_token = response.get('NextToken', None)

            while next_token is not None:
                self.logger.info("Next Token Returned: {}".format(next_token))
                response = org_client.list_accounts_for_parent(
                    ParentId=parent_id,
                    NextToken=next_token
                )
                self.logger.info("Extending Account List")
                account_list.extend(response.get('Accounts', []))
                next_token = response.get('NextToken', None)

            return account_list

        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def create_account(self, acct_name, email, role_name='AWSControlTowerExecution',
                       billing_access='ALLOW'):
        try:
            response = org_client.create_account(
                Email=email,
                AccountName=acct_name,
                RoleName=role_name,
                IamUserAccessToBilling=billing_access
            )
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'FinalizingOrganizationException':
                self.logger.info("Caught exception 'FinalizingOrganizationException', handling the exception...")
                return {"Error": "FinalizingOrganizationException"}
            else:
                message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
                self.logger.exception(message)
                raise

    def describe_account_status(self, req_id):
        try:
            response = org_client.describe_create_account_status(
                CreateAccountRequestId=req_id
            )
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def move_account(self, acct_id, src_id, dst_id):
        try:
            response = org_client.move_account(
                AccountId=acct_id,
                SourceParentId=src_id,
                DestinationParentId=dst_id
            )
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def list_accounts(self, **kwargs):
        try:
            response = org_client.list_accounts(**kwargs)
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def get_accounts_in_org(self, **kwargs):
        try:
            response = org_client.list_accounts()

            account_list = response.get('Accounts', [])
            next_token = response.get('NextToken', None)

            while next_token is not None:
                self.logger.info("Next Token Returned: {}".format(next_token))
                response = org_client.list_accounts(
                    NextToken=next_token
                )
                self.logger.info("Extending Account List")
                account_list.extend(response.get('Accounts', []))
                next_token = response.get('NextToken', None)

            return account_list
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise


    @try_except_retry(count=4, multiplier=2)
    def describe_account(self, acct_id):
        try:
            response = org_client.describe_account(
                AccountId=acct_id
            )
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise
