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

import os
import shutil


def make_dir(directory, logger=None):
    """Creates a directory if it doesn't exist.
       print message for command line use or else
       write messege to logger as applicable.

    Args:
        directory: string. directory name
        logger: instance of logger class. default none. optional
    """
    # if exist skip else create dir
    try:
        os.stat(directory)
        if logger is None:
            print("\n Directory {} already exist... skipping".format(directory))
        else:
            logger.info("Directory {} already exist... skipping".format(directory))
    except OSError:
        if logger is None:
            print("\n Directory {} not found, creating now...".format(directory))
        else:
            logger.info("Directory {} not found, creating now...".format(directory))
        os.makedirs(directory)


def remove_dir(directory, logger=None):
    """Creates a directory if it doesn't exist.
       print message for command line use or else
       write messege to logger as applicable.

    Args:
        directory: string. directory name
        logger: instance of logger class. default none. optional
    """
    # if exist skip else create dir
    try:
        os.stat(directory)
        if logger is None:
            print(
                "\n Directory {} already exist, deleting open-source"
                " directory".format(directory)
            )
        else:
            logger.info(
                "\n Directory {} already exist, deleting open-source"
                " directory".format(directory)
            )
        shutil.rmtree(directory)
    except OSError:
        if logger is None:
            print("\n Directory {} not found... nothing to delete".format(directory))
        else:
            logger.info("Directory {} not found... nothing to delete".format(directory))
