###############################################################################
#  Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.    #
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

import string
import random


def random_pwd_generator(length, additional_str=''):
    """Generate random password.

    Args:
        length: length of the password
        additional_str: Optional. Input additonal string that is allowed in
                        the password. Default to '' empty string.
    Returns:
        password
    """
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits \
        + additional_str
    # Making sure the password has two numbers and symbols at the very least
    password = ''.join(random.SystemRandom().choice(chars)
                       for _ in range(length-4)) + \
               ''.join(random.SystemRandom().choice(string.digits)
                       for _ in range(2)) + \
               ''.join(random.SystemRandom().choice(additional_str)
                       for _ in range(2))
    return password
