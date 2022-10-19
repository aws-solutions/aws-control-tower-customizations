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
from cfct.state_machine_handler import CloudFormation
from cfct.utils.logger import Logger

logger = Logger("info")

string1 = "xx"
string2 = "yy"
list1 = ["aa", "bb"]
list2 = ["bb", "dd"]
event = {}
cf = CloudFormation(event, logger)


@pytest.mark.unit
def test_add_list_type():
    assert isinstance(cf._add_list(list1, list2), list)


@pytest.mark.unit
def test_delete_list_type():
    assert isinstance(cf._delete_list(list1, list2), list)


@pytest.mark.unit
def test_add_list_string_fail():
    with pytest.raises(ValueError, match=r"Both variables must be list.*"):
        cf._add_list(list1, string1)


@pytest.mark.unit
def test_add_string_list_fail():
    with pytest.raises(ValueError, match=r"Both variables must be list.*"):
        cf._add_list(string1, list1)


@pytest.mark.unit
def test_add_strings_fail():
    with pytest.raises(ValueError, match=r"Both variables must be list.*"):
        cf._add_list(string1, string2)


@pytest.mark.unit
def test_del_list_string_fail():
    with pytest.raises(ValueError, match=r"Both variables must be list.*"):
        cf._delete_list(list1, string1)


@pytest.mark.unit
def test_del_string_list_fail():
    with pytest.raises(ValueError, match=r"Both variables must be list.*"):
        cf._delete_list(string1, list1)


@pytest.mark.unit
def test_del_strings_fail():
    with pytest.raises(ValueError, match=r"Both variables must be list.*"):
        cf._delete_list(string1, string2)
