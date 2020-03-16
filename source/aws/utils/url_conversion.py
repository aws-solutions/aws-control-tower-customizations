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

from urllib.parse import urlparse


def convert_s3_url_to_http_url(s3_url):
    """Convert s3 url to http url.

    Converts the S3 URL s3://bucket-name/object
    to HTTP URL https://s3.amazonaws.com/bucket-name/object.

    Args:
        s3_url

    Returns:
        http url

    Raises:
    """
    u = urlparse(s3_url)
    s3bucket = u.netloc
    s3key = u.path[1:]
    http_url = "https://s3.amazonaws.com/{}/{}".format(s3bucket, s3key)
    return http_url


def convert_http_url_to_s3_url(http_url):
    """Convert http url to s3 url.

    Convert the HTTP URL https://s3.amazonaws.com/bucket-name/object
    to S3 URL s3://bucket-name/object.

    Args:
        http_url

    Returns:
        s3 url

    Raises:
    """
    u = urlparse(http_url)
    t = u.path.split('/', 2)
    s3bucket = t[1]
    s3key = t[2]
    s3_url = "s3://{}/{}".format(s3bucket, s3key)
    return s3_url
