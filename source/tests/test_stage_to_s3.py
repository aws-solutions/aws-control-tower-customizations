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

from cfct.manifest.stage_to_s3 import StageFile
from cfct.utils.logger import Logger
from os import environ
import pytest

logger = Logger('info')

@pytest.mark.unit
def test_convert_url():
    bucket_name = 'my-bucket-name'
    key_name = 'my-key-name'
    relative_path = "s3://" + bucket_name + "/" + key_name
    sf = StageFile(logger, relative_path)
    s3_url = sf.get_staged_file()
    logger.info(s3_url)
    assert s3_url.startswith("{}{}{}{}{}{}".format('https://',
                                                   bucket_name,
                                                   '.s3.',
                                                   environ.get('AWS_REGION'),
                                                   '.amazonaws.com/',
                                                   key_name))