######################################################################################################################
#  Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.                                           #
#                                                                                                                    #
#  Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance        #
#  with the License. A copy of the License is located at                                                             #
#                                                                                                                    #
#      http://www.apache.org/licenses/LICENSE-2.0                                                                                    #
#                                                                                                                    #
#  or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES #
#  OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions    #
#  and limitations under the License.                                                                                #
######################################################################################################################

import re
import boto3
from os import environ
from urllib.parse import urlparse
import inspect
import tempfile
from lib.s3 import S3

def sanitize(name, space_allowed=False, replace_with_character='_'):
    # This function will replace any character other than [a-zA-Z0-9._-] with '_'
    if space_allowed:
        sanitized_name = re.sub(r'([^\sa-zA-Z0-9._-])', replace_with_character, name)
    else:
        sanitized_name = re.sub(r'([^a-zA-Z0-9._-])', replace_with_character, name)
    return sanitized_name


def trim_length(string, length):
    if len(string) > length:
        return string[:length]
    else:
        return string


# Getting Service regions
def get_available_regions(service_name):
    """ Returns list of regions
    Example: ['ap-northeast-1', 'ap-northeast-2', 'ap-south-1', 'ap-southeast-1', 'ap-southeast-2',
     'ca-central-1', 'eu-central-1', 'eu-west-1', 'eu-west-2', 'eu-west-3', 'sa-east-1', 'us-east-1',
      'us-east-2', 'us-west-1', 'us-west-2']
    """
    session = boto3.session.Session()
    return session.get_available_regions(service_name)


def get_sts_region():
    return environ.get('AWS_REGION')


def get_sts_endpoint():
    return "https://sts.%s.amazonaws.com" % environ.get('AWS_REGION')


def transform_params(params_in):
    """
    Args:
        params_in (dict): Python dict of input params e.g.
        {
            "principal_role": "$[alfred_ssm_/org/primary/service_catalog/principal/role_arn]"
        }

    Return:
        params_out (list): Python list of output params e.g.
        {
            "ParameterKey": "principal_role",
            "ParameterValue": "$[alfred_ssm_/org/primary/service_catalog/principal/role_arn]"
        }
    """
    params_list = []
    for key, value in params_in.items():
        param = {}
        param.update({"ParameterKey": key})
        param.update({"ParameterValue": value})
        params_list.append(param)
    return params_list


def reverse_transform_params(params_in):
    """
    Args:
        params_in (list): Python list of output params e.g.
        {
            "ParameterKey": "principal_role",
            "ParameterValue": "$[alfred_ssm_/org/primary/service_catalog/principal/role_arn]"
        }
    Return:
        params_out (dict): Python dict of input params e.g.
        {
            "principal_role": "$[alfred_ssm_/org/primary/service_catalog/principal/role_arn]"
        }
    """
    params_out = {}
    for param in params_in:
        key = param.get("ParameterKey")
        value = param.get("ParameterValue")
        params_out.update({key: value})
    return params_out


def convert_s3_url_to_http_url(s3_url):
    # Convert the S3 URL s3://bucket-name/object
    # to HTTP URL https://s3.amazonaws.com/bucket-name/object
    u = urlparse(s3_url)
    s3bucket = u.netloc
    s3key = u.path[1:]
    http_url = "https://s3.amazonaws.com/{}/{}".format(s3bucket, s3key)
    return http_url


def convert_http_url_to_s3_url(http_url):
    # Convert the HTTP URL https://s3.amazonaws.com/bucket-name/object
    # to S3 URL s3://bucket-name/object
    u = urlparse(http_url)
    t = u.path.split('/', 2)
    s3bucket = t[1]
    s3key = t[2]
    s3_url = "s3://{}/{}".format(s3bucket, s3key)
    return s3_url


def download_remote_file(logger, remote_s3_path):
    try:
        _file = tempfile.mkstemp()[1]
        t = remote_s3_path.split("/", 3) # s3://bucket-name/key
        remote_bucket = t[2] # Bucket name
        remote_key = t[3] # Key
        logger.info("Downloading {}/{} from S3 to {}".format(remote_bucket, remote_key, _file))
        s3 = S3(logger)
        s3.download_file(remote_bucket, remote_key, _file)
        return _file
    except Exception as e:
        message = {'FILE': __file__.split('/')[-1],
                   'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
        logger.exception(message)
        raise

