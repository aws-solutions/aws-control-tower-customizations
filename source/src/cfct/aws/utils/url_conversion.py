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
from urllib.parse import urlparse
from boto3.session import Session


def convert_s3_url_to_http_url(s3_url):
    """Convert s3 url to http url.

    Converts the S3 URL s3://bucket-name/object
    to HTTP URL https://bucket-name.s3.Region.amazonaws.com/key-name

    Args:
        s3_url

    Returns:
        http url

    Raises:
    """
    u = urlparse(s3_url)
    s3bucket = u.netloc
    s3key = u.path[1:]
    http_url = build_http_url(s3bucket, s3key)
    return http_url


def build_http_url(bucket_name, key_name):
    """Builds http url for the given bucket and key name

    :param bucket_name:
    :param key_name:
    :return HTTP URL:
     example: https://bucket-name.s3.Region.amazonaws.com/key-name
    """
    return "{}{}{}{}{}{}".format(
        "https://",
        bucket_name,
        ".s3.",
        environ.get("AWS_REGION"),
        ".amazonaws.com/",
        key_name,
    )


def parse_bucket_key_names(http_url):
    """Convert http url to s3 url.

    Convert the HTTP URL https://bucket-name.s3.Region.amazonaws.com/key-name or
    https://s3.Region.amazonaws.com/bucket-name/key-name
    to S3 URL s3://bucket-name/key-name.
    Args:
        http_url

    Returns:
        bucket_name, key_name, region
    """
    # Handle Amazon S3 path-style URL
    # Needed to handle response from describe_provisioning_artifact API - response['Info']['TemplateUrl']
    # example: https://s3.Region.amazonaws.com/bucket-name/key-name
    if http_url.startswith("https://s3."):
        parsed_url = urlparse(http_url)
        bucket_name = parsed_url.path.split("/", 2)[1]
        key_name = parsed_url.path.split("/", 2)[2]
        region = parsed_url.netloc.split(".")[1]
    # Handle Amazon S3 virtual-hosted–style URL
    # example: https://bucket-name.s3.Region.amazonaws.com/key-name
    else:
        parsed_url = urlparse(http_url)
        bucket_name = parsed_url.netloc.split(".")[0]
        key_name = parsed_url.path[1:]
        region = parsed_url.netloc.split(".")[2]
    session = Session()
    partition_name = session.get_partition_for_region(region_name=session.region_name)
    if region not in session.get_available_regions(partition_name=partition_name, service_name='s3'):
        raise ValueError(f"URL: {http_url} is missing a 'Region' or is using a region you are not opted into.\nExpected URL format https://s3.Region.amazonaws.com/bucket-name/key-name or https://bucket-name.s3.Region.amazonaws.com/key-name")
    return bucket_name, key_name, region
