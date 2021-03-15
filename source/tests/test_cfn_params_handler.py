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

cph = CFNParamsHandler(logger)


def test_update_alfred_ssm():
    keyword_ssm = 'alfred_ssm_not_exist_alfred_ssm'
    value_ssm = 'parameter_store_value'
    value_ssm, param_flag = cph._update_alfred_ssm(
                            keyword_ssm, value_ssm, False)
    assert param_flag is True
