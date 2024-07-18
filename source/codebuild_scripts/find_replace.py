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
import sys

import yaml
from cfct.utils.logger import Logger
from cfct.utils.path_utils import is_safe_path
from jinja2 import Environment, FileSystemLoader

# initialise logger
log_level = "info"
logger = Logger(loglevel=log_level)


def find_replace(function_path, file_name, destination_file, parameters):
    try:
        j2loader = FileSystemLoader(function_path)
        j2env = Environment(loader=j2loader, autoescape=True)  # Compliant
        j2template = j2env.get_template(file_name)
        dictionary = {}
        for key, value in parameters.items():
            if "json" in file_name and not isinstance(value, list):
                value = '"%s"' % value
            elif "json" in file_name and isinstance(value, list):
                value = json.dumps(value)
            dictionary.update({key: value})
        logger.debug(dictionary)
        output = j2template.render(dictionary)
        if is_safe_path(function_path, destination_file):
            abs_destination_file = os.path.abspath(destination_file)
            with open(abs_destination_file, "w") as fh:
                fh.write(output)
        else:
            raise ValueError(f"Unsafe file path detected {destination_file}")
    except Exception as e:
        logger.log_general_exception(__file__.split("/")[-1], inspect.stack()[0][3], e)
        raise


def update_add_on_manifest(event, path):
    extract_path = path
    exclude_j2_files = []

    # Find and replace the variable in Manifest file
    for item in event.get("input_parameters"):
        f = item.get("file_name")
        exclude_j2_files.append(f)
        filename, file_extension = os.path.splitext(f)
        destination_file_path = (
            extract_path + "/" + filename
            if file_extension == ".j2"
            else extract_path + "/" + f
        )
        find_replace(extract_path, f, destination_file_path, item.get("parameters"))


def sanitize_boolean_type(s, bools):
    s = " " + s
    logger.info("Adding quotes around the boolean values: {}".format(bools))
    logger.info("Print original string: {}".format(s))
    for w in [x.strip() for x in bools.split(",")]:
        s = s.replace(":" + " " + w, ': "' + w + '"')
        logger.info(
            "If found, wrapped '{}' with double quotes, printing"
            " the modified string: {}".format(w, s)
        )
    return yaml.safe_load(s[1:])


def sanitize_null_type(d, none_type_values):
    s = json.dumps(d)
    s = " " + s
    logger.info("Replacing none_type/null with empty quotes.")
    for w in [x.strip() for x in none_type_values.split(",")]:
        s = s.replace(":" + " " + w, ': ""')
        logger.info(
            "If found, replacing '{}' with double quotes, printing"
            " the modified string: {}".format(w, s)
        )
    return yaml.safe_load(s[1:])


def generate_event(user_input_file, path, bools, none_types):
    logger.info("Generating Event")
    if is_safe_path(path, user_input_file):
        abs_user_path = os.path.abspath(user_input_file)
        with open(abs_user_path) as f:
            user_input = sanitize_boolean_type(f.read(), bools)
            logger.info("Boolean values wrapped with quotes (if applicable)")
            logger.info(user_input)
            user_input = sanitize_null_type(user_input, none_types)
            logger.info("Null values replaced with quotes (if applicable)")
            logger.info(user_input)
    else:
        raise ValueError(f"Unsafe file path detected {user_input_file}")
    update_add_on_manifest(user_input, path)


if __name__ == "__main__":
    if len(sys.argv) > 4:
        path = sys.argv[2]
        file_name = sys.argv[1]
        none_type_values = sys.argv[4]
        boolean_type_values = sys.argv[3]
        generate_event(file_name, path, boolean_type_values, none_type_values)
    else:
        print(
            "Not enough arguments provided. Please provide the path and"
            " user input file names."
        )
        print("Example: merge_manifest.py <PATH-OF-FILES>" " <USER-INPUT-FILE-NAME>")
        sys.exit(2)
