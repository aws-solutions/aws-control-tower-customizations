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

import time
import random
from os import environ
from cfct.aws.services.ssm import SSM
from cfct.aws.services.ec2 import EC2
from cfct.aws.services.kms import KMS
from cfct.aws.services.sts import AssumeRole
from cfct.utils.string_manipulation import sanitize, trim_string_from_front, \
    convert_string_to_list
from cfct.utils.password_generator import random_pwd_generator


class CFNParamsHandler(object):
    """This class goes through the cfn parameters passed by users to
       state machines and SSM parameters to get the correct parameter
       , create parameter value and update SSM parameters as applicable.
       For example, if a cfn parameter is passed, save it in
       SSM parameter store.
    """
    def __init__(self, logger):
        self.logger = logger
        self.ssm = SSM(self.logger)
        self.kms = KMS(self.logger)
        self.assume_role = AssumeRole()

    def _session(self, region, account_id=None):
        # instantiate EC2 session
        account_id = account_id[0] if \
            isinstance(account_id, list) else account_id
        if account_id is None:
            return EC2(self.logger, region)
        else:
            return EC2(self.logger,
                       region,
                       credentials=self.assume_role(self.logger,
                                                    account_id))

    def _get_ssm_params(self, ssm_parm_name):
        return self.ssm.get_parameter(ssm_parm_name)

    def _get_kms_key_id(self):
        alias_name = environ.get('KMS_KEY_ALIAS_NAME')
        response = self.kms.describe_key(alias_name)
        self.logger.debug(response)
        key_id = response.get('KeyMetadata', {}).get('KeyId')
        return key_id

    def get_azs_from_member_account(self, region, qty, account, key_az=None):
        """gets a predefined quantity of (random) az's from a specified region

        Args:
            region (str): region name
            qty: quantity of az's to return
            account: account id of the member account
            key_az (str): ssm parameter store key where existing
            AZ list is stored
        Returns:
            list: availability zone names
        """
        if key_az:
            self.logger.info("Looking up values in SSM parameter:{}"
                             .format(key_az))
            existing_param = self.ssm.describe_parameters(key_az)

            if existing_param:
                self.logger.info('Found existing SSM parameter, returning'
                                 ' existing AZ list.')
                return self.ssm.get_parameter(key_az)
        if account is not None:
            # fetch account from list for cross account assume role workflow
            # the account id is arbitrary in this case as we need to get the
            # AZ list for a given region in any account.
            acct = account[0] if isinstance(account, list) else account
            ec2 = self._session(region, acct)
            self.logger.info("Getting list of AZs in region: {} from"
                             " account: {}".format(region, acct))
            return self._get_az(ec2, key_az, qty)
        else:
            self.logger.info("Creating EC2 Session in {} region"
                             .format(region))
            ec2 = EC2(self.logger, region)
            return self._get_az(ec2, key_az, qty)

    def _get_az(self, ec2, key_az, qty):
        # Get AZs
        az_list = ec2.describe_availability_zones()
        self.logger.info("_get_azs output: %s" % az_list)
        random_az_list = ','.join(random.sample(az_list, qty))
        description = "Contains random AZs selected by Custom Control Tower" \
                      "Solution"
        if key_az:
            self.ssm.put_parameter(key_az, random_az_list, description)
        return random_az_list

    def _create_key_pair(self, account, region, param_key_material=None,
                         param_key_fingerprint=None, param_key_name=None):
        """Creates an ec2 key pair if it does not exist already.

        Args:
            account:
            region:
            param_key_material: key material used to encrypt and decrypt data.
                                Default to None
            param_key_fingerprint: key finger print. Default to None
            param_key_name: key name. A key name will be automatically created
                            if there is none. Default to None
        Returns:
            key name
        """
        if param_key_name:
            self.logger.info("Looking up values in SSM parameter:{}"
                             .format(param_key_name))
            existing_param = self.ssm.describe_parameters(param_key_name)

            if existing_param:
                return self.ssm.get_parameter(param_key_name)

        key_name = sanitize("%s_%s_%s_%s" % ('custom_control_tower', account,
                                             region,
                                             time.strftime("%Y-%m-%dT%H-%M-%S")
                                             ))

        ec2 = self._session(region, account)
        # create EC2 key pair in member account
        self.logger.info("Create key pair in the member account {} in"
                         " region: {}".format(account, region))
        response = ec2.create_key_pair(key_name)

        # add key material and fingerprint in the SSM Parameter Store
        self.logger.info("Adding Key Material and Fingerprint to SSM PS")
        description = "Contains EC2 key pair asset created by Custom " \
                      "Control Tower Solution: " \
                      "EC2 Key Pair Custom Resource."
        # Get Custom Control Tower KMS Key ID
        key_id = self._get_kms_key_id()
        if param_key_fingerprint:
            self.ssm.put_parameter_use_cmk(param_key_fingerprint, response
                                           .get('KeyFingerprint'),
                                           key_id, description)
        if param_key_material:
            self.ssm.put_parameter_use_cmk(param_key_material, response
                                           .get('KeyMaterial'),
                                           key_id, description)
        if param_key_name:
            self.ssm.put_parameter(param_key_name, key_name, description)

        return key_name

    def random_password(self, length, key_password=None, alphanum=True):
        """Generates a random string, by default only including letters
            and numbers

        Args:
            length (int): length of string to generate
            key_password (str): ssm parameter store key where existing
            password is stored
            alphanum (bool): [optional] if False it will also include
                             ';:=+!@#%^&*()[]{}' in the character set
        """
        response = '_get_ssm_secure_string_' + key_password
        param_exists = False
        if key_password:
            self.logger.info("Looking up values in SSM parameter:{}"
                             .format(key_password))
            existing_param = self.ssm.describe_parameters(key_password)

            if existing_param:
                param_exists = True

        if not param_exists:
            additional = ''
            if not alphanum:
                additional = ';:=+!@#%^&*()[]{}'
            password = random_pwd_generator(length, additional)

            self.logger.info("Adding Random password to SSM Parameter Store")
            description = "Contains random password created by Custom Control"\
                          " Tower Solution"

            if key_password:
                key_id = self._get_kms_key_id()
                self.ssm.put_parameter_use_cmk(key_password, password, key_id,
                                               description)
        return response

    def update_params(self, params_in: list, account=None, region=None,
                      substitute_ssm_values=True):
        """Updates SSM parameters
        Args:
            params_in (list): Python List of dict of input params e.g.
            [{
                "ParameterKey": "LoggingAccountId",
                "ParameterValue":
                    "$[alfred_ssm_/org/member/logging/account_id]"
            },{
                "ParameterKey": "foo",
                "ParameterValue": "bar"
            }]

        Return:
            params_out (dict): Python dict of output params e.g.
            {
                "LoggingAccountId": "${AWS::AccountId}",
                "foo": "bar"
            }
        """
        self.logger.info("params in : {}".format(params_in))

        params_out = {}
        for param in params_in:
            key = param.get("ParameterKey")
            value = param.get("ParameterValue")
            separator = ','
            value = value if separator not in value else \
                convert_string_to_list(value, separator)

            if not isinstance(value, list):
                value = self._process_alfred_helper(param, key, value, account,
                                                    region,
                                                    substitute_ssm_values)
            else:
                new_value_list = []
                for nested_value in value:
                    new_value_list.append(
                        self._process_alfred_helper(param, key, nested_value,
                                                    account, region,
                                                    substitute_ssm_values))
                value = new_value_list

            params_out.update({key: value})

        self.logger.info("params out : {}".format(params_out))
        return params_out

    def _process_alfred_helper(self, param, key, value, account=None,
                               region=None, substitute_ssm_values=True):
        """Parses and processes alfred helpers
           'alfred_ '
        Args:
            param: dict. input param
            key: input param key
            value: input param value (or nested value)
            account: string
            region: string
            substitute_ssm_values: boolean. default to true

        Return:
            value of the processed input param value
        """
        if value.startswith("$[") and value.endswith("]"):
            # Apply transformations
            keyword = value[2:-1]
            # Check if supported keyword e.g. alfred_ssm_,
            # alfred_genaz_, alfred_getaz_, alfred_genuuid, etc.
            if keyword.startswith("alfred_ssm_"):
                value, param_flag = self._update_alfred_ssm(
                    keyword, value, substitute_ssm_values
                )
                if param_flag is False:
                    raise KeyError(
                        "Missing SSM parameter name for:"
                        " {} in the parameters JSON file.".format(key)
                    )
            elif keyword.startswith("alfred_genkeypair"):
                value = self._update_alfred_genkeypair(param, account, region)
            elif keyword.startswith("alfred_genpass_"):
                value = self._update_alfred_genpass(keyword, param)
            elif keyword.startswith("alfred_genaz_"):
                value = self._update_alfred_genaz(keyword, param, account, region)
            else:
                value = keyword
        return value

    def _update_alfred_ssm(self, keyword, value, substitute_ssm_values):
        """Gets the value of the SSM parameter whose name starts with
           'alfred_ssm_ '
        Args:
            keyword: string. trimmed parameter value without
                     unwanted leading and trailing characters
            value: parameter value
            substitute_ssm_values: boolean. default to true

        Return:
            value of the SSM parameter
        """
        ssm_param_name = trim_string_from_front(keyword, 'alfred_ssm_')
        param_flag = True

        if ssm_param_name:
            # If this flag is True, it will replace the SSM parameter name
            # i.e. /org/member/ss/directory-name with its value i.e. example,
            # whereas if it is False, it will leave the parameter name as-is.
            if substitute_ssm_values:
                value = self._get_ssm_params(ssm_param_name)
        else:
            param_flag = False
        self.logger.debug(f"value: {value}; param_flag:{param_flag}")
        return value, param_flag

    def _update_alfred_genkeypair(self, param, account, region):
        """Gets the ec2 key pair name if SSM parameter name starts with
           'alfred_genkeypair '
        Args:
            value: string. parameter value
            param: one parameter in list
            account: string
            region: string

        Return:
            ec2 key pair name
        """
        keymaterial_param_name = None
        keyfingerprint_param_name = None
        keyname_param_name = None
        ssm_parameters = param.get('ssm_parameters', [])
        if type(ssm_parameters) is list:
            for ssm_parameter in ssm_parameters:
                val = ssm_parameter.get('value')[2:-1]
                if val.lower() == 'keymaterial':
                    keymaterial_param_name = ssm_parameter.get('name')
                elif val.lower() == 'keyfingerprint':
                    keyfingerprint_param_name = ssm_parameter.get('name')
                elif val.lower() == 'keyname':
                    keyname_param_name = ssm_parameter.get('name')
        value = self._create_key_pair(account, region,
                                      keymaterial_param_name,
                                      keyfingerprint_param_name,
                                      keyname_param_name)
        return value

    def _update_alfred_genpass(self, keyword, param):
        """Creates a random password if SSM parameter name starts with
           'alfred_genpass_ '
        Args:
            keyword: string. trimmed parameter value without
                     unwanted leading and trailing characters
            value: string. parameter value
            param: one parameter in list

        Return:
            generated random password
        """
        sub_string = trim_string_from_front(keyword, 'alfred_genpass_')
        if sub_string:
            pw_length = int(sub_string)
        else:
            pw_length = 8

        password_param_name = None
        ssm_parameters = param.get('ssm_parameters', [])
        if type(ssm_parameters) is list:
            for ssm_parameter in ssm_parameters:
                val = ssm_parameter.get('value')[2:-1]
                if val.lower() == 'password':
                    password_param_name = ssm_parameter.get('name')
        value = self.random_password(pw_length, password_param_name, False)
        return value

    def _update_alfred_genaz(self, keyword, param, account, region):
        """gets a predefined list of (random) az's from a specified region
           if SSM parameter name starts with 'alfred_genaz '
        Args:
            keyword: string. trimmed parameter value without
                     unwanted leading and trailing characters
            value: string. parameter value
            param: one parameter in list
            account: string
            region: string

        Return:
            list of random az's
        """
        sub_string = trim_string_from_front(keyword, 'alfred_genaz_')
        if sub_string:
            no_of_az = int(sub_string)
        else:
            no_of_az = 2

        az_param_name = None
        ssm_parameters = param.get('ssm_parameters', [])
        if type(ssm_parameters) is list:
            for ssm_parameter in ssm_parameters:
                val = ssm_parameter.get('value')[2:-1]
                if val.lower() == 'az':
                    az_param_name = ssm_parameter.get('name')
        value = self.get_azs_from_member_account(
            region, no_of_az, account, az_param_name)
        return value
