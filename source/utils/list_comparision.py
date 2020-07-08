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

from utils.logger import Logger
logger = Logger('info')

def compare_lists(existing_list: list, new_list: list) -> bool:
    """Compares two list and return boolean flag if they match

    Args:
        existing_list: Input string
            Is there a space in the input string. Default to false.
        new_list:
            Character to replace the target character with. Default to '_'.

    Returns:
        boolean value

    Raises:
    """
    added_values = list(set(new_list) - set(existing_list))
    removed_values = list(set(existing_list) - set(new_list))
    if len(added_values) == 0 and len(removed_values) == 0:
        logger.info("Lists matched.")
        return True
    else:
        logger.info("Lists didn't match.")
        return False


