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

# !/bin/python

import inspect
import json
import os
import zipfile
from hashlib import md5
from uuid import uuid4

from jinja2 import Environment, FileSystemLoader

from cfct.aws.services.kms import KMS
from cfct.aws.services.s3 import S3
from cfct.aws.services.ssm import SSM
from cfct.utils.crhelper import cfn_handler
from cfct.utils.logger import Logger

# initialise logger
log_level = os.environ.get("LOG_LEVEL")
logger = Logger(loglevel=log_level)
init_failed = False

# instantiate classes from lib
kms = KMS(logger)
ssm = SSM(logger)


def safe_extract(zip_file_name, output_path, max_files=1000, max_size=500 * 1024 * 1024):
    with zipfile.ZipFile(zip_file_name, "r") as zip_file:
        # Get the list of files
        file_list = zip_file.infolist()

        # Check the number of files
        if len(file_list) > max_files:
            raise Exception(f"The number of files in the ZIP archive exceeds {max_files}.")

        # Check the total size of files
        total_size = sum(file.file_size for file in file_list)
        if total_size > max_size:
            raise Exception(f"The total size of files in the ZIP archive exceeds {max_size}.")

        for file in file_list:
            zip_file.extract(file, output_path)


def unzip_function(zip_file_name, function_path, output_path):
    orig_path = os.getcwd()
    os.chdir(function_path)
    safe_extract(zip_file_name, output_path)
    os.chdir(orig_path)


def find_replace(function_path, file_name, destination_file, parameters):
    j2loader = FileSystemLoader(function_path)
    j2env = Environment(loader=j2loader, autoescape=True)  # Compliant
    j2template = j2env.get_template(file_name)
    dictionary = {}
    for key, value in parameters.items():
        value = '"%s"' % value if "json" in file_name else value
        dictionary.update({key: value})
    logger.debug(dictionary)
    output = j2template.render(dictionary)
    with open(destination_file, "w") as fh:
        fh.write(output)


def zip_function(zip_file_name, function_path, output_path, exclude_list):
    orig_path = os.getcwd()
    os.chdir(output_path)
    function_path = os.path.normpath(function_path)
    if os.path.exists(zip_file_name):
        try:
            os.remove(zip_file_name)
        except OSError:
            pass
    zip_file = zipfile.ZipFile(zip_file_name, mode="a")
    os.chdir(function_path)
    for folder, subs, files in os.walk("."):
        for filename in files:
            file_path = os.path.join(folder, filename)
            if not any(x in file_path for x in exclude_list):
                logger.debug(file_path)
                zip_file.write(file_path)
    zip_file.close()
    os.chdir(orig_path)


def find_alias(alias_name):
    # List Aliases (loop through the response to if next marker exists)
    marker = None
    alias_not_found = True
    while alias_not_found:
        response_list_alias = kms.list_aliases(marker)
        truncated_flag = response_list_alias.get("Truncated")
        for alias in response_list_alias.get("Aliases"):
            if alias.get("AliasName") == alias_name:
                logger.info("Found key attached with existing key id.")
                key_id = alias.get("TargetKeyId")
                return key_id
        if not truncated_flag:
            logger.info("Alias not found in the list")
            alias_not_found = False
        else:
            logger.info("Could not find alias in truncated response," " trying again...")
            marker = response_list_alias.get("NextMarker")
            logger.info("Trying again with NextMarker: {}".format(marker))


def create_cmk_with_alias(alias_name, event_policy):
    logger.info("Creating new KMS key id and alias.")
    policy = str(json.dumps(event_policy))
    logger.info("Policy")
    logger.info(policy)
    response_create_key = kms.create_key(
        str(policy),
        "CMK created for Custom" " Control Tower Resources",
        "AWSSolutions",
        "CustomControlTower",
    )
    logger.info("KMS Key created.")
    key_id = response_create_key.get("KeyMetadata", {}).get("KeyId")
    kms.create_alias(alias_name, key_id)
    logger.info("Alias created.")
    return key_id


def update_key_policy(key_id, event_policy):
    policy = str(json.dumps(event_policy))
    logger.info("Policy")
    logger.info(policy)
    response_update_policy = kms.put_key_policy(key_id, policy)
    logger.info("Response: Update Key Policy")
    logger.info(response_update_policy)


def put_ssm_parameter(key, value):
    response = ssm.describe_parameters(key)
    # put parameter if key does not exist
    if not response:
        ssm.put_parameter(key, value)


def config_deployer(event):
    try:
        s3 = S3(logger)

        # set variables
        source_bucket_name = event.get("BucketConfig", {}).get("SourceBucketName")
        key_name = event.get("BucketConfig", {}).get("SourceS3Key")
        destination_bucket_name = event.get("BucketConfig", {}).get("DestinationBucketName")
        input_zip_file_name = key_name.split("/")[-1] if "/" in key_name else key_name
        output_zip_file_name = event.get("BucketConfig", {}).get("DestinationS3Key")
        alias_name = event.get("KMSConfig", {}).get("KMSKeyAlias")
        policy = event.get("KMSConfig", {}).get("KMSKeyPolicy")
        flag_value = event.get("MetricsFlag")
        base_path = "/tmp/custom_control_tower"
        input_file_path = base_path + "/" + input_zip_file_name
        extract_path = base_path + "/" + "extract"
        output_path = base_path + "/" + "out"
        exclude_j2_files = []

        # Search for existing KMS key alias
        key_id = find_alias(alias_name)

        # if alias name not found in the list, create a new alias with
        # new target key
        if not key_id:
            key_id = create_cmk_with_alias(alias_name, policy)
            logger.info("Key ID created: {}".format(key_id))
            kms.enable_key_rotation(key_id)
            logger.info("Automatic key rotation enabled.")
        else:
            logger.info("Key ID: {} found attached with alias: {}".format(key_id, alias_name))
            logger.info("Updating KMS key policy")
            update_key_policy(key_id, policy)
            kms.enable_key_rotation(key_id)

        # Encrypt configuration bucket
        s3.put_bucket_encryption(destination_bucket_name, key_id)

        # Download the file from Solutions S3 bucket
        logger.info(f"Creating {base_path} if it doesn't exist")
        os.makedirs(base_path, exist_ok=True)
        s3.download_file(source_bucket_name, key_name, input_file_path)

        # Unzip the config zip file
        unzip_function(input_zip_file_name, base_path, extract_path)

        # Find and replace the variable in Manifest file
        for item in event.get("FindReplace"):
            f = item.get("FileName")
            parameters = item.get("Parameters")
            exclude_j2_files.append(f)
            filename, file_extension = os.path.splitext(f)
            destination_file_path = (
                extract_path + "/" + filename if file_extension == ".j2" else extract_path + "/" + f
            )
            find_replace(extract_path, f, destination_file_path, parameters)

        # Zip the contents
        exclude = ["zip"] + exclude_j2_files
        logger.info(f"Creating {output_path} if it doesn't exist")
        os.makedirs(output_path)
        zip_function(output_zip_file_name, extract_path, output_path, exclude)

        # Upload the file in the customer S3 bucket
        local_file = output_path + "/" + output_zip_file_name
        remote_file = output_zip_file_name
        s3.upload_file(destination_bucket_name, local_file, remote_file)

        # create SSM parameters to send anonymous data if opted in
        put_ssm_parameter("/org/primary/metrics_flag", flag_value)
        put_ssm_parameter("/org/primary/customer_uuid", str(uuid4()))
        return None
    except Exception as e:
        logger.log_general_exception(__file__.split("/")[-1], inspect.stack()[0][3], e)
        raise


def update_config_deployer(event):
    alias_name = event.get("KMSConfig", {}).get("KMSKeyAlias")
    policy = event.get("KMSConfig", {}).get("KMSKeyPolicy")
    flag_value = event.get("MetricsFlag")

    # Search for existing KMS key alias
    key_id = find_alias(alias_name)

    # if alias name not found in the list, create a new alias with
    # new target key
    if not key_id:
        key_id = create_cmk_with_alias(alias_name, policy)
        logger.info("Key ID created: {}".format(key_id))
        kms.enable_key_rotation(key_id)
        logger.info("Automatic key rotation enabled.")
    else:
        logger.info("Key ID: {} found attached with alias: {}".format(key_id, alias_name))
        logger.info("Updating KMS key policy")
        update_key_policy(key_id, policy)
        kms.enable_key_rotation(key_id)

        # create SSM parameters to send anonymous data if opted in
        put_ssm_parameter("/org/primary/metrics_flag", flag_value)
        put_ssm_parameter("/org/primary/customer_uuid", str(uuid4()))

    return None


def create(event, context):
    """
    Runs on Stack Creation.
    As there is no real 'resource', and it will never be replaced,
    PhysicalResourceId is set to a hash of StackId and LogicalId.
    """
    s = "%s-%s" % (event.get("StackId"), event.get("LogicalResourceId"))
    physical_resource_id = md5(s.encode("UTF-8")).hexdigest()
    logger.info("physical_resource_id: {}".format(physical_resource_id))

    if event.get("ResourceType") == "Custom::ConfigDeployer":
        response = config_deployer(event.get("ResourceProperties"))
        return physical_resource_id, response
    else:
        logger.error("No valid ResourceType found!")


def update(event, context):
    """
    Update the KMS key policy.
    """
    physical_resource_id = event.get("PhysicalResourceId")

    if event.get("ResourceType") == "Custom::ConfigDeployer":
        response = update_config_deployer(event.get("ResourceProperties"))
        return physical_resource_id, response
    else:
        logger.error("No valid ResourceType found!")


def delete(event, context):
    """
    Delete capability is not required for this function.
    """


def lambda_handler(event, context):
    logger.info("<<<<<<<<<< ConfigDeployer Event >>>>>>>>>>")
    logger.info(event)
    logger.debug(context)
    return cfn_handler(event, context, create, update, delete, logger, init_failed)
