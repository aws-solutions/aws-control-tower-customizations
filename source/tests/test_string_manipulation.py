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
from utils import string_manipulation


def test_sanitize():
    non_sanitized_string = 'I s@nitize $tring exc*pt_underscore-hypen.'
    sanitized_string_allow_space = 'I s_nitize _tring exc_pt_underscore-hypen.'
    sanitized_string_no_space_replace_hypen = \
        'I-s-nitize--tring-exc-pt_underscore-hypen.'
    assert string_manipulation.sanitize(non_sanitized_string,True) == \
           sanitized_string_allow_space
    assert string_manipulation.sanitize(non_sanitized_string, False,'-') == \
           sanitized_string_no_space_replace_hypen


def test_trim_length():
    actual_sting = "EighteenCharacters"
    eight_char_string = "Eighteen"
    assert string_manipulation\
               .trim_length_from_end(actual_sting, 8) == eight_char_string
    assert string_manipulation\
               .trim_length_from_end(actual_sting, 18) == actual_sting
    assert string_manipulation\
               .trim_length_from_end(actual_sting, 20) == actual_sting


def test_extract_string():
    actual_string = "abcdefgh"
    extract_string = "defgh"
    assert string_manipulation.trim_string_from_front(actual_string, 'abc') == \
           extract_string
