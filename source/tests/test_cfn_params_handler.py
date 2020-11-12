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
from moto import mock_ssm
from utils.logger import Logger
from manifest.cfn_params_handler import CFNParamsHandler
from aws.services.ssm import SSM

log_level = 'info'
logger = Logger(loglevel=log_level)

cph = CFNParamsHandler(logger)
ssm = SSM(logger)

@mock_ssm
def test_update_params():
    ssm.put_parameter('/key1', 'value1', 'A test parameter', 'String')
    ssm.put_parameter('/key2', 'value2', 'A test parameter', 'String')
    ssm.put_parameter('/key3', 'value3', 'A test parameter', 'String')
    param = [{
                "ParameterKey": "Key",
                "ParameterValue":[
                        "$[alfred_ssm_/key1]",
                        "$[alfred_ssm_/key2]",
                        "$[alfred_ssm_/key3]"
                    ]
            }]
   
    account = 1234567890
    region = 'us-east-1'
    value = cph.update_params(param, account, region)
    assert value == {"Key": ["value1","value2","value3"]}

def test_update_alfred_ssm():
    keyword_ssm = 'alfred_ssm_not_exist_alfred_ssm'
    value_ssm = 'parameter_store_value'
    value_ssm, param_flag = cph._update_alfred_ssm(
                            keyword_ssm, value_ssm, False)
    assert param_flag is True


@mock_ssm
def test_update_alfred_genkeypair():
    ssm.put_parameter('testkeyname', 'testvalue', 'A test parameter', 'String')
    param = {
        "ssm_parameters": [
            {
                "name": "keymaterial",
                "value": "$[keymaterial]"
            },
            {
                "name": "keyfingerprint",
                "value": "$[keyfingerprint]"
            },
            {
                "name": "testkeyname",
                "value": "$[keyname]"
            }
        ]
    }
    account = 1234567890
    region = 'us-east-1'
    value = cph._update_alfred_genkeypair(param, account, region)
    assert value == 'testvalue'


@mock_ssm
def test_update_alfred_genpass():
    ssm.put_parameter('testkeyname', 'testvalue', 'A test parameter', 'String')
    param = {
        "ssm_parameters": [
            {
                "name": "testkeyname",
                "value": "$[password]"
            }
        ]
    }
    keyword = 'alfred_genpass_10'
    value = ''
    value = cph._update_alfred_genpass(keyword, param)
    assert value == '_get_ssm_secure_string_testkeyname'


@mock_ssm
def test_update_alfred_genaz():
    ssm.put_parameter('testkeyname', 'testvalue', 'A test parameter', 'String')
    param = {
        "ssm_parameters": [
            {
                "name": "testkeyname",
                "value": "$[az]"
            }
        ]
    }
    keyword = 'alfred_genaz_1'
    account = 1234567890
    region = 'us-east-1'
    value = ''
    value = cph._update_alfred_genaz(keyword, param, account, region)
    assert value == 'testvalue'


@mock_ssm
def test_random_password():
    ssm.put_parameter('testkeyname', 'testvalue', 'A test parameter', 'String')
    length = 10
    key_password = 'testkeyname'
    alphanum = False
    value = cph.random_password(length, key_password, alphanum)
    assert value == '_get_ssm_secure_string_testkeyname'
