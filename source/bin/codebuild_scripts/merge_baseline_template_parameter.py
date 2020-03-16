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

import json
import sys
import os
import subprocess
from utils.logger import Logger


def _read_file(file):
    if os.path.isfile(file):
        logger.info('File - {} exists'.format(file))
        logger.info("Reading from {}".format(file))
        with open(file) as f:
            return json.load(f)
    else:
        logger.error("File: {} not found.".format(file))
        sys.exit(1)


def _write_file(data, file, mode='w'):
    logger.info("Writing to {}".format(file))
    with open(file, mode) as outfile:
        json.dump(data, outfile, indent=2)
    outfile.close()


def _flip_to_json(yaml_file):
    json_file = os.path.join(yaml_file + json_extension)
    logger.info("Flipping YAML > {} to JSON > {}".format(yaml_file, json_file))
    subprocess.run(["cfn-flip", "-j", yaml_file, json_file])
    return _read_file(json_file)


def _flip_to_yaml(json_file):
    yaml_file = json_file[:-len(updated_flag)]
    logger.info("Flipping JSON > {} to YAML > {}".format(json_file, yaml_file))
    # final stage - convert json avm template to yaml format
    subprocess.run(["cfn-flip", "-y", json_file, yaml_file])


def file_matcher(master_data, add_on_data, master_key='master',
                 add_on_key='add_on'):
    for item in master_data.get(master_key):
        logger.info("Iterating Master AVM File List")
        for key, value in item.items():
            logger.info('{}: {}'.format(key, value))
            master_file_name = value.split('/')[-1]
            logger.info("master_value: {}".format(value.split('/')[-1]))
            for i in add_on_data.get(add_on_key):
                logger.info("Iterating Add-On AVM File List for comparision.")
                for k, v in i.items():
                    logger.info('{}: {}'.format(k, v))
                    add_on_file_name = v.split('/')[-1]
                    logger.info("add_on_value: {}".format(v.split('/')[-1]))
                    if master_file_name == add_on_file_name:
                        logger.info("Matching file names found - "
                                    "full path below")
                        logger.info("File in master list: {}".format(value))
                        logger.info("File in add-on list: {}".format(v))
                        # Pass value and v to merge functions
                        if master_file_name.lower().endswith('.template'):
                            logger.info("Processing template file")
                            # merge master avm template with add_on template
                            # send json data
                            final_json = update_template(_flip_to_json(value),
                                                         _flip_to_json(v))
                            # write the json data to json file
                            updated_json_file_name =  \
                                os.path.join(value+updated_flag)
                            _write_file(final_json, updated_json_file_name)
                            _flip_to_yaml(updated_json_file_name)
                        if master_file_name.lower().endswith('.json'):
                            logger.info("Processing parameter file")
                            update_parameters(value, v)


def update_level_1_dict(master, add_on, level_1_key):
    for key1, value1 in add_on.items():
        if isinstance(value1, dict):
            # Check if primary key matches
            if key1 == level_1_key:
                logger.info("Level 1 keys matched ADDON {} == {}".format(
                    key1, level_1_key))
                # Iterate through the 2nd level dicts in the value
                for key2, value2 in value1.items():
                    logger.info("----------------------------------")
                    # Match k with master dict keys - add if not present
                    for k1, v1 in master.items():
                        if isinstance(v1, dict):
                            if k1 == level_1_key:
                                logger.info("Level 1 keys matched MASTER "
                                            "{} == {}".format(k1, level_1_key))
                                flag = False
                                # Iterate through the 2nd level dicts in
                                # the value
                                for k2, v2 in v1.items():
                                    logger.info("Is {} == {}".format(key2, k2))
                                    if key2 == k2:
                                        logger.info("Found matching keys")
                                        flag = False
                                        logger.info("Setting flag value to {}"
                                                    .format(flag))
                                        break
                                    else:
                                        flag = True
                                        logger.info(
                                            "Add-on key not found in existing"
                                            " dict, setting flag value to {}"
                                            " to update dict.".format(flag))
                                if flag:
                                    logger.info('Adding key {}'.format(key2))
                                    d2 = {key2: value2}
                                    v1.update(d2)
                                    logger.debug(master)
    return master


def _reload(add_on, original):
    # return original manifest if updated manifest is None
    update = add_on if add_on is not None else original
    return update


def _keys(json_data):
    # dynamically build key list to process the add-on avm template
    keys = list()
    for k, v in json_data.items():
        keys.append(k)
    return keys


def update_template(master, add_on):
    logger.info("Merging template files.")
    # get keys for iteration
    keys = _keys(add_on)
    for key in keys:
        # Iterate through the keys in add_on baseline template
        updated_temp = update_level_1_dict(master, add_on, key)
        master = _reload(updated_temp, master)
    return master


def update_parameters(master, add_on, decision_key='ParameterKey'):
    logger.info("Merging parameter files.")
    m_list = _read_file(master)
    add_list = _read_file(add_on)
    if add_list:
        for item in add_list:
            logger.info(item.get(decision_key))
            if m_list:
                flag = False
                for i in m_list:
                    logger.info(i.get(decision_key))
                    if item.get(decision_key) == i.get(decision_key):
                        logger.info("Keys: '{}' matched, skipping"
                                    .format(item.get(decision_key)))
                        flag = False
                        logger.info("Setting flag value to {} and stopping"
                                    " the loop.".format(flag))
                        break
                    else:
                        flag = True
                        logger.info("Setting flag value to {}".format(flag))
                if flag:
                    # avoid appending same parameter in the parameter list
                    if item not in m_list:
                        m_list.append(item)
                        logger.info("Printing updated parameter file.")
                        logger.info(m_list)
        return m_list


if __name__ == '__main__':
    if len(sys.argv) > 3:
        log_level = sys.argv[1]
        master_baseline_file = sys.argv[2]
        add_on_baseline_file = sys.argv[3]

        json_extension = ".json"
        updated_flag = ".update"
        logger = Logger(loglevel=log_level)

        master_list = _read_file(master_baseline_file)
        add_on_list = _read_file(add_on_baseline_file)
        file_matcher(master_list, add_on_list)

    else:
        print('No arguments provided. Please provide the existing and '
              'new manifest files names.')
        print('Example: merge_baseline_template_parameter.py <LOG-LEVEL>'
              ' <MASTER_FILE_NAME> <ADD_ON_FILE_NAME>')
        sys.exit(2)
