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
from cfct.utils.list_comparision import compare_lists
from cfct.utils.logger import Logger

logger = Logger("info")

list1 = ["aa", "bb", "cc"]  # add value to list 2
list2 = ["aa", "bb"]  # remove value from list 1
list3 = ["aa", "cc", "dd"]  # remove and add values from list 1
list4 = ["ee"]  # single item list to test replace single account
list5 = ["ff"]


@pytest.mark.unit
def test_add_list():
    assert compare_lists(list2, list1) is False


@pytest.mark.unit
def test_delete_list():
    assert compare_lists(list1, list2) is False


@pytest.mark.unit
def test_add_delete_list():
    assert compare_lists(list1, list3) is False


@pytest.mark.unit
def test_single_item_replacement():
    assert compare_lists(list4, list5) is False


@pytest.mark.unit
def test_no_change_list():
    assert compare_lists(list1, list1) is True
