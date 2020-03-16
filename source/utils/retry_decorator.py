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

import time
from random import randint
from functools import wraps
from utils.logger import Logger

# initialise logger
logger = Logger(loglevel='info')


def try_except_retry(count=3, multiplier=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _count = count
            _seconds = randint(5,10)
            while _count >= 1:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.warning("{}, Trying again in {} seconds".format(e, _seconds))
                    time.sleep(_seconds)
                    _count -= 1
                    _seconds *= multiplier
                    if _count == 0:
                        logger.error("Retry attempts failed, raising the exception.")
                        raise
            return func(*args, **kwargs)
        return wrapper
    return decorator
