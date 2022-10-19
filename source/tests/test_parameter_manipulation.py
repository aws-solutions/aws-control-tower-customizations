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
import pytest
from cfct.utils import parameter_manipulation

param = {"key": "value", "key1": "value1"}
trans_params = [
    {"ParameterKey": "key", "ParameterValue": "value"},
    {"ParameterKey": "key1", "ParameterValue": "value1"},
]


@pytest.mark.unit
def test_transform_params():
    out_params = parameter_manipulation.transform_params(param)
    for idx in range(len(out_params)):
        assert out_params[idx]["ParameterKey"] == trans_params[idx]["ParameterKey"]
        assert out_params[idx]["ParameterValue"] == trans_params[idx]["ParameterValue"]


@pytest.mark.unit
def test_reverse_transform_params():
    rev_param = parameter_manipulation.reverse_transform_params(trans_params)
    for key in rev_param.keys():
        assert rev_param[key] == param[key]
