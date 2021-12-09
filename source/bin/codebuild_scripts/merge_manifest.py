##############################################################################
#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.   #
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

import yaml
import sys
from utils.logger import Logger

log_level = 'info'
logger = Logger(loglevel=log_level)


# Iterate through the first level keys and add them if not found in the
# existing manifest file
def update_level_one_list(existing, add_on, level_one_dct_key, decision_key):
    if add_on.get(level_one_dct_key):
        for add_on_key_level_one_list in add_on.get(level_one_dct_key):
            flag = False
            if existing.get(level_one_dct_key):
                for existing_key_level_one_list in \
                        existing.get(level_one_dct_key):
                    if add_on_key_level_one_list.get(decision_key) ==  \
                         existing_key_level_one_list.get(decision_key):
                        flag = False
                        # break the loop if same name is found in the list
                        break
                    else:
                        # Setting the flag to add the value after scanning
                        # the full list
                        flag = True
            else:
                flag = True
            if flag and add_on_key_level_one_list not in existing.get(level_one_dct_key):
                # to avoid duplication append check to see if value in
                # the list already exist
                logger.info("(Level 1) Adding new {} > {}: {}"
                            .format(type(add_on_key_level_one_list)
                                    .__name__, decision_key,
                                    add_on_key_level_one_list
                                    .get(decision_key)))
                existing.get(level_one_dct_key) \
                    .append(add_on_key_level_one_list)
                logger.debug(existing.get(level_one_dct_key))
        return existing


def _reload(add_on, original):
    # return original manifest if updated manifest is None
    update = add_on if add_on is not None else original
    return update


def _json_to_yaml(json, filename):
    # Convert json to yaml
    # logger.debug(json)
    yml = yaml.safe_dump(json, default_flow_style=False, indent=2)
    # print(yml)

    # create new manifest file
    file = open(filename, 'w')
    file.write(yml)
    file.close()


def update_scp_policies(add_on, original):
    level_1_key = 'organization_policies'
    decision_key = 'name'

    # process new scp policy addition
    updated_manifest = update_level_one_list(
        original, add_on, level_1_key, decision_key)
    original = _reload(updated_manifest, original)

    return original


def update_cloudformation_resources(add_on, original):
    level_1_key = 'cloudformation_resources'
    decision_key = 'name'

    # process new baseline addition
    updated_manifest = update_level_one_list(
        original, add_on, level_1_key, decision_key)
    original = _reload(updated_manifest, original)

    return original


def main():
    manifest = yaml.safe_load(open(master_manifest_file_path))
    logger.debug(manifest)

    add_on_manifest = yaml.safe_load(open(add_on_manifest_file_path))
    logger.debug(add_on_manifest)

    manifest = update_scp_policies(add_on_manifest, manifest)

    manifest = update_cloudformation_resources(add_on_manifest, manifest)

    _json_to_yaml(manifest, output_manifest_file_path)


if __name__ == "__main__":
    if len(sys.argv) > 3:
        master_manifest_file_path = sys.argv[1]
        add_on_manifest_file_path = sys.argv[2]
        output_manifest_file_path = sys.argv[3]
        main()
    else:
        print('No arguments provided. Please provide the existing and'
              ' new manifest files names.')
        print('Example: merge_manifest.py'
              ' <ORIG-FILE-NAME> <ADD-ON-FILE-NAME> <NEW-FILE-NAME>')
        sys.exit(2)
