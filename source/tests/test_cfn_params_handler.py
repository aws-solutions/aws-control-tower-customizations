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
from moto import mock_ssm
from utils.logger import Logger
from manifest.cfn_params_handler import CFNParamsHandler
from aws.services.ssm import SSM

log_level = 'info'
logger = Logger(loglevel=log_level)


def test_update_alfred_ssm():
    keyword_ssm = 'alfred_ssm_not_exist_alfred_ssm'
    value_ssm = 'parameter_store_value'
    cph = CFNParamsHandler(logger)
    value_ssm, param_flag = cph._update_alfred_ssm(
        keyword_ssm, value_ssm, False)
    assert param_flag is True


@mock_ssm
def test_update_params():
    logger.info("-- Put new parameter keys in mock environment")
    ssm = SSM(logger)
    ssm.put_parameter('/key1', 'value1', 'Test parameter 1', 'String')
    ssm.put_parameter('/key2', 'value2', 'Test parameter 2', 'String')
    ssm.put_parameter('/key3', 'value3', 'Test parameter 3', 'String')

    logger.info("-- Get parameter keys using alfred_ssm")
    multiple_params = [{
        "ParameterKey": "Key1",
        "ParameterValue": [
            "$[alfred_ssm_/key1]",
            "$[alfred_ssm_/key2]",
            "$[alfred_ssm_/key3]"
        ]
    }]
    cph = CFNParamsHandler(logger)
    values = cph.update_params(multiple_params)
    assert values == {"Key1": ["value1", "value2", "value3"]}

    single_param = [{
        "ParameterKey": "Key2",
        "ParameterValue": "$[alfred_ssm_/key1]"
    }]
    value = cph.update_params(single_param)
    assert value == {"Key2": "value1"}
