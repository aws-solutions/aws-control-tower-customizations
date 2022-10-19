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

from os import environ

import pytest
from cfct.aws.utils.get_partition import get_partition
from cfct.utils.logger import Logger

logger = Logger("info")

aws_regions_partition = "aws"
aws_china_regions_partition = "aws-cn"
aws_us_gov_cloud_regions_partition = "aws-us-gov"


@pytest.mark.unit
def test_get_partition_for_us_region():
    environ["AWS_REGION"] = "us-east-1"
    assert aws_regions_partition == get_partition()


@pytest.mark.unit
def test_get_partition_for_eu_region():
    environ["AWS_REGION"] = "eu-west-1"
    assert aws_regions_partition == get_partition()


@pytest.mark.unit
def test_get_partition_for_cn_region():
    environ["AWS_REGION"] = "cn-north-1"
    assert aws_china_regions_partition == get_partition()


@pytest.mark.unit
def test_get_partition_for_us_gov_cloud_region():
    environ["AWS_REGION"] = "us-gov-west-1"
    assert aws_us_gov_cloud_regions_partition == get_partition()
