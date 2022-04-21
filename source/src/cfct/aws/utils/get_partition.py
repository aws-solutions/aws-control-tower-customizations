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


def get_partition():
    """
    :return: partition name for the current AWS region
    """
    region_name = environ.get('AWS_REGION')
    china_region_name_prefix = 'cn'
    us_gov_cloud_region_name_prefix = 'us-gov'
    aws_regions_partition = 'aws'
    aws_china_regions_partition = 'aws-cn'
    aws_us_gov_cloud_regions_partition = 'aws-us-gov'

    # China regions
    if region_name.startswith(china_region_name_prefix):
        return aws_china_regions_partition
    # AWS GovCloud(US) Regions
    elif region_name.startswith(us_gov_cloud_region_name_prefix):
        return aws_us_gov_cloud_regions_partition
    else:
        return aws_regions_partition
