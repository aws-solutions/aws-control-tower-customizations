##############################################################################
#  Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.   #
#                                                                            #
#  Licensed under the Apache License, Version 2.0 (the "License").           #
#  You may not use this file except in compliance                            #
#  with the License. A copy of the License is located at                     #
#                                                                            #
#      http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                            #
#  or in the "license" file accompanying this file. This file is             #
#  distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY  #
#  KIND, express or implied. See the License for the specific language       #
#  governing permissions  and limitations under the License.                 #
##############################################################################
from aws.utils.url_conversion import parse_bucket_key_names, \
    convert_s3_url_to_http_url, build_http_url
from utils.logger import Logger
logger = Logger('info')
bucket_name = 'bucket-name'
key_name = 'key-name/key2/object'


def test_s3_url_to_http_url():
    s3_path = '%s/%s' % (bucket_name, key_name)
    s3_url = 's3://' + s3_path
    http_url = convert_s3_url_to_http_url(s3_url)
    assert http_url.startswith("https://")
    assert http_url.endswith(key_name)


def test_virtual_hosted_style_http_url_to_s3_url():
    http_url = 'https://' + bucket_name + '.s3.Region.amazonaws.com/' + key_name
    bucket, key = parse_bucket_key_names(http_url)
    assert bucket_name == bucket
    assert key_name == key


def test_path_style_http_url_to_s3_url():
    http_url = 'https://s3.Region.amazonaws.com/' + bucket_name + '/' + key_name
    bucket, key = parse_bucket_key_names(http_url)
    assert bucket_name == bucket
    assert key_name == key


def test_build_http_url():
    http_url = build_http_url(bucket_name, key_name)
    assert http_url.startswith("https://")
    assert http_url.endswith(key_name)
