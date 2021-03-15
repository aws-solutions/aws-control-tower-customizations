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
from utils import os_util
import mock
from utils.logger import Logger
import os


log_level = 'info'
logger = Logger(loglevel=log_level)


@mock.patch('utils.os_util.os')
def test_make_dir(self, tmpdir):
    os_util.make_dir(tmpdir)
    assert os.path.isdir(tmpdir) is True
    os_util.make_dir(tmpdir, logger)
    assert os.path.isdir(tmpdir) is True


@mock.patch('utils.os_util.os')
def test_remove_dir(self, tmpdir):
    os_util.remove_dir(tmpdir)
    assert os.path.isdir(tmpdir) is False
    os_util.remove_dir(tmpdir, logger)
    assert os.path.isdir(tmpdir) is False
