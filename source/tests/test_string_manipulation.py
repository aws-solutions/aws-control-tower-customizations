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
import pytest
from cfct.utils import string_manipulation


@pytest.mark.unit
def test_sanitize():
    non_sanitized_string = "I s@nitize $tring exc*pt_underscore-hypen."
    sanitized_string_allow_space = "I s_nitize _tring exc_pt_underscore-hypen."
    sanitized_string_no_space_replace_hypen = (
        "I-s-nitize--tring-exc-pt_underscore-hypen."
    )
    assert (
        string_manipulation.sanitize(non_sanitized_string, True)
        == sanitized_string_allow_space
    )
    assert (
        string_manipulation.sanitize(non_sanitized_string, False, "-")
        == sanitized_string_no_space_replace_hypen
    )


@pytest.mark.unit
def test_trim_length():
    actual_sting = "EighteenCharacters"
    eight_char_string = "Eighteen"
    assert (
        string_manipulation.trim_length_from_end(actual_sting, 8) == eight_char_string
    )
    assert string_manipulation.trim_length_from_end(actual_sting, 18) == actual_sting
    assert string_manipulation.trim_length_from_end(actual_sting, 20) == actual_sting


@pytest.mark.unit
def test_extract_string():
    actual_string = "abcdefgh"
    extract_string = "defgh"
    assert (
        string_manipulation.trim_string_from_front(actual_string, "abc")
        == extract_string
    )


@pytest.mark.unit
def test_convert_list_values_to_string():
    list_of_numbers = [11, 22, 33, 44]
    list_of_strings = string_manipulation.convert_list_values_to_string(list_of_numbers)
    for string in list_of_strings:
        assert isinstance(string, str)


@pytest.mark.unit
def test_convert_string_to_list_default_separator():
    separator = ","
    value = "a, b"
    list_1 = (
        value
        if separator not in value
        else string_manipulation.convert_string_to_list(value, separator)
    )
    assert isinstance(list_1, list)
    assert list_1[0] == "a"
    assert list_1[1] == "b"


@pytest.mark.unit
def test_convert_string_to_list_no_separator():
    separator = ","
    value = "a"
    string = (
        value
        if separator not in value
        else string_manipulation.convert_string_to_list(value, separator)
    )
    assert isinstance(string, str)
    assert string == "a"


@pytest.mark.unit
def test_convert_string_to_list_custom_separator():
    separator = ";"
    value = "a; b"
    list_1 = list_1 = (
        value
        if separator not in value
        else string_manipulation.convert_string_to_list(value, separator)
    )
    assert isinstance(list_1, list)
    assert list_1[0] == "a"
    assert list_1[1] == "b"


@pytest.mark.unit
def test_strip_list_items():
    arr = [" a", "  b", "c "]
    assert string_manipulation.strip_list_items(arr) == ["a", "b", "c"]


@pytest.mark.unit
def test_remove_empty_strings():
    arr = ["a", "b", "", "c"]
    assert string_manipulation.remove_empty_strings(arr) == ["a", "b", "c"]


@pytest.mark.unit
def test_list_sanitizer():
    arr = ["  a", "b  ", "", "   c"]
    assert string_manipulation.list_sanitizer(arr) == ["a", "b", "c"]


@pytest.mark.unit
def test_empty_separator_handler():
    delimiter = ":"
    nested_ou_name_list = "testou1:testou2:testou3"
    assert string_manipulation.empty_separator_handler(
        delimiter, nested_ou_name_list
    ) == ["testou1", "testou2", "testou3"]
