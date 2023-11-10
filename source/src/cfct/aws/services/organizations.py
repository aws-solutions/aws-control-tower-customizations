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

from botocore.exceptions import ClientError

from cfct.aws.utils.boto3_session import Boto3Session
from cfct.utils.retry_decorator import try_except_retry


class Organizations(Boto3Session):
    def __init__(self, logger, **kwargs):
        self.logger = logger
        __service_name = "organizations"
        super().__init__(logger, __service_name, **kwargs)
        self.org_client = super().get_client()
        self.next_token_returned_msg = "Next Token Returned: {}"

    def list_roots(self):
        try:
            response = self.org_client.list_roots()
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)

    def list_organizational_units_for_parent(self, parent_id):
        try:
            response = self.org_client.list_organizational_units_for_parent(ParentId=parent_id)

            ou_list = response.get("OrganizationalUnits", [])
            next_token = response.get("NextToken", None)

            while next_token is not None:
                self.logger.info(self.next_token_returned_msg.format(next_token))
                response = self.org_client.list_organizational_units_for_parent(
                    ParentId=parent_id, NextToken=next_token
                )
                self.logger.info("Extending OU List")
                ou_list.extend(response.get("OrganizationalUnits", []))
                next_token = response.get("NextToken", None)

            return ou_list
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def list_accounts_for_parent(self, parent_id):
        try:
            response = self.org_client.list_accounts_for_parent(ParentId=parent_id)

            account_list = response.get("Accounts", [])
            next_token = response.get("NextToken", None)

            while next_token is not None:
                self.logger.info(self.next_token_returned_msg.format(next_token))
                response = self.org_client.list_accounts_for_parent(
                    ParentId=parent_id, NextToken=next_token
                )
                self.logger.info("Extending Account List")
                account_list.extend(response.get("Accounts", []))
                next_token = response.get("NextToken", None)

            return account_list
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def list_accounts(self, **kwargs):
        try:
            response = self.org_client.list_accounts(**kwargs)
            return response
        except Exception as e:
            self.logger.log_unhandled_exception(e)
            raise

    def get_accounts_in_org(self):
        try:
            response = self.org_client.list_accounts()

            account_list = response.get("Accounts", [])
            next_token = response.get("NextToken", None)

            while next_token is not None:
                self.logger.info(self.next_token_returned_msg.format(next_token))
                response = self.org_client.list_accounts(NextToken=next_token)
                self.logger.info("Extending Account List")
                account_list.extend(response.get("Accounts", []))
                next_token = response.get("NextToken", None)

            return account_list
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def describe_organization(self):
        try:
            response = self.org_client.describe_organization()
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise
