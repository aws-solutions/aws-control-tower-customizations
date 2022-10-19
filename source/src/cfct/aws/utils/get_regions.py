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

import boto3


def get_available_regions(service_name):
    """Returns list of available regions given an AWS service.

    Args: service_name

    Return: list of available regions for the given AWS service
            Example: ['ap-northeast-1', 'ap-northeast-2', 'ap-south-1',
            'ap-southeast-1', 'ap-southeast-2','ca-central-1', 'eu-central-1',
            'eu-west-1', 'eu-west-2', 'eu-west-3', 'sa-east-1', 'us-east-1',
            'us-east-2', 'us-west-1', 'us-west-2']
    """
    session = boto3.session.Session()
    return session.get_available_regions(service_name)
