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

import re


def sanitize(name, space_allowed=False, replace_with_character="_"):
    """Sanitizes input string.

    Replaces any character other than [a-zA-Z0-9._-] in a string
    with a specified character (default '_').

    Args:
        name: Input string
        space_allowed (optional):
            Is there a space in the input string. Default to false.
        replace_with_character (optional):
            Character to replace the target character with. Default to '_'.

    Returns:
        Sanitized string

    Raises:
    """
    if space_allowed:
        sanitized_name = re.sub(r"([^\sa-zA-Z0-9._-])", replace_with_character, name)
    else:
        sanitized_name = re.sub(r"([^a-zA-Z0-9._-])", replace_with_character, name)
    return sanitized_name


def trim_length_from_end(string, length):
    """Trims the length of the given string to the given length

    :param string:
    :param length:
    :return: trimmed string to the length provided
    """
    if len(string) > length:
        return string[:length]
    else:
        return string


def trim_string_from_front(string, remove_starts_with_string):
    """Remove string provided in the search_string
    and returns remainder of the string.
    :param string:
    :param remove_starts_with_string:
    :return: trimmed string
    """
    if string.startswith(remove_starts_with_string):
        return string[len(remove_starts_with_string) :]
    else:
        raise ValueError(
            "The beginning of the string does " "not match the string to be trimmed."
        )


def extract_string(search_str):
    return str[len(search_str) :]


def convert_list_values_to_string(_list):
    return list(map(str, _list))


def convert_string_to_list(_string, separator=","):
    """
    splits the string with give separator and remove whitespaces
    """
    return [x.strip() for x in _string.split(separator)]


def strip_list_items(array):
    return [item.strip() for item in array]


def remove_empty_strings(array):
    return [x for x in array if x != ""]


def list_sanitizer(array):
    stripped_array = strip_list_items(array)
    return remove_empty_strings(stripped_array)


def empty_separator_handler(delimiter, nested_ou_name):
    if delimiter == "":
        nested_ou_name_list = [nested_ou_name]
    else:
        nested_ou_name_list = nested_ou_name.split(delimiter)
    return nested_ou_name_list
