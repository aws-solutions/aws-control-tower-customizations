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

from lib.ssm import SSM
from lib.sts import STS
from lib.ec2 import EC2
from lib.kms import KMS
from lib.assume_role_helper import AssumeRole
from lib.helper import sanitize
from os import environ
import random
import string
import time
import inspect


class ParamsHandler(object):

    def __init__(self, logger):
        self.logger = logger
        self.ssm = SSM(self.logger)
        self.kms = KMS(self.logger)
        self.assume_role = AssumeRole()

    def _session(self, region, account_id):
        # instantiate EC2 sessions
        return EC2(self.logger, region, credentials=self.assume_role(self.logger, account_id))

    def _extract_string(self, str, search_str):
        return str[len(search_str):]

    def _get_ssm_params(self, ssm_parm_name):
        try:
            return self.ssm.get_parameter(ssm_parm_name)
        except Exception as e:
            raise Exception("Missing SSM parameter value for: {} in the SSM Parameter Store.".format(ssm_parm_name))

    def _get_kms_key_id(self):
        alias_name = environ.get('kms_key_alias_name')
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
        Returns:
            list: availability zone names
        """
        try:
            if key_az:
                self.logger.info("Looking up values in SSM parameter:{}".format(key_az))
                existing_param = self.ssm.describe_parameters(key_az)

                if existing_param:
                    self.logger.info('Found existing SSM parameter, returning exising AZ list.')
                    return self.ssm.get_parameter(key_az)
            if account is not None:
                ec2 = self._session(region, account)
                self.logger.info("Getting list of AZs in region: {} from account: {}".format(region, account))
                return self._get_az(ec2, key_az, qty)
            else:
                self.logger.info("Creating EC2 Session in {} region".format(region))
                ec2 = EC2(self.logger, region)
                return self._get_az(ec2, key_az, qty)
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def _get_az(self, ec2, key_az, qty):
        # Get AZs
        az_list = ec2.describe_availability_zones()
        self.logger.info("_get_azs output: %s" % az_list)
        random_az_list = ','.join(random.sample(az_list, qty))
        description = "Contains random AZs selected by Custom Control Tower Solution"
        if key_az:
            self.ssm.put_parameter(key_az, random_az_list, description)
        return random_az_list

    def create_key_pair(self, account, region, param_key_material=None, param_key_fingerprint=None, param_key_name=None):

        if param_key_name:
            self.logger.info("Looking up values in SSM parameter:{}".format(param_key_name))
            existing_param = self.ssm.describe_parameters(param_key_name)

            if existing_param:
                return self.ssm.get_parameter(param_key_name)

        key_name = sanitize("%s_%s_%s_%s" % ('custom_control_tower', account, region, time.strftime("%Y-%m-%dT%H-%M-%S")))

        try:
            ec2 = self._session(region, account)
            # create EC2 key pair in member account
            self.logger.info("Create key pair in the member account {} in region: {}".format(account, region))
            response = ec2.create_key_pair(key_name)

            # add key material and fingerprint in the SSM Parameter Store
            self.logger.info("Adding Key Material and Fingerprint to SSM PS")
            description = "Contains EC2 key pair asset created by Custom Control Tower Solution: " \
                          "EC2 Key Pair Custom Resource."
            # Get Custom Control Tower KMS Key ID
            key_id = self._get_kms_key_id()
            if param_key_fingerprint:
                self.ssm.put_parameter_use_cmk(param_key_fingerprint, response.get('KeyFingerprint'),
                                               key_id, description)
            if param_key_material:
                self.ssm.put_parameter_use_cmk(param_key_material, response.get('KeyMaterial'),
                                               key_id, description)
            if param_key_name:
                self.ssm.put_parameter(param_key_name, key_name, description)

            return key_name
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def random_password(self, length, key_password=None, alphanum=True):
        """Generates a random string, by default only including letters and numbers

        Args:
            length (int): length of string to generate
            alphanum (bool): [optional] if False it will also include ';:=+!@#%^&*()[]{}' in the character set
        """
        try:
            response = '_get_ssm_secure_string_' + key_password

            if key_password:
                self.logger.info("Looking up values in SSM parameter:{}".format(key_password))
                existing_param = self.ssm.describe_parameters(key_password)

                if existing_param:
                    return response
            additional = ''
            if not alphanum:
                additional = ';:=+!@#%^&*()[]{}'
            chars = string.ascii_uppercase + string.ascii_lowercase + string.digits + additional
            # Making sure the password has two numbers and symbols at the very least
            password = ''.join(random.SystemRandom().choice(chars) for _ in range(length-4)) + \
                       ''.join(random.SystemRandom().choice(string.digits) for _ in range(2)) + \
                       ''.join(random.SystemRandom().choice(additional) for _ in range(2))

            self.logger.info("Adding Random password to SSM PS")
            description = "Contains random password created by Custom Control Tower Solution"

            if key_password:
                key_id = self._get_kms_key_id()
                self.ssm.put_parameter_use_cmk(key_password, password, key_id, description)
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def update_params(self, params_in, account = None, region = None, substitute_ssm_values = True):
        """
        Args:
            params_in (list): Python List of dict of input params e.g.
            [{
                "ParameterKey": "LoggingAccountId",
                "ParameterValue": "$[alfred_ssm_/org/member/logging/account_id]"
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
        try:
            self.logger.info("params in : {}".format(params_in))

            params_out = {}
            for param in params_in:
                key = param.get("ParameterKey")
                value = param.get("ParameterValue")

                if not isinstance(value, list):
                    if value.startswith('$[') and value.endswith(']'):
                        # Apply transformations
                        keyword = value[2:-1]
                        # Check if supported keyword e.g. alfred_ssm_, alfred_genaz_, alfred_getaz_, alfred_genuuid, etcself.
                        if keyword.startswith('alfred_ssm_'):
                            ssm_param_name = self._extract_string(keyword, 'alfred_ssm_')

                            if ssm_param_name:
                                # If this flag is True, it will replace the SSM parameter name i.e. /org/member/ss/directory-name with its
                                # value i.e. example, whereas if its False, it will leave the parameter name as-is
                                if substitute_ssm_values:
                                    value = self._get_ssm_params(ssm_param_name)
                            else:
                                raise Exception("Missing SSM parameter name for: {} in the parameters JSON file.".format(key))
                        elif keyword.startswith('alfred_genkeypair'):
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
                            value = self.create_key_pair(account, region, keymaterial_param_name, keyfingerprint_param_name, keyname_param_name)
                        elif keyword.startswith('alfred_genpass_'):
                            sub_string = self._extract_string(keyword, 'alfred_genpass_')
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
                        elif keyword.startswith('alfred_genaz_'):
                            sub_string = self._extract_string(keyword, 'alfred_genaz_')
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
                            value = self.get_azs_from_member_account(region, no_of_az, account, az_param_name)
                        else:
                            value = keyword

                params_out.update({key: value})

            self.logger.info("params out : {}".format(params_out))
            return params_out
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise
