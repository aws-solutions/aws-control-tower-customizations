######################################################################################################################
# Copyright 2012-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.                                                                           #
######################################################################################################################

#!/usr/bin/env python
import os
import sys
import zipfile


def zip_function(zip_file_name, function_path, output_path, exclude_list):
    orig_path = os.getcwd()
    os.chdir(output_path)
    function_path = os.path.normpath(function_path)
    zip_name = zip_file_name + '.zip'
    if os.path.exists(zip_name):
        try:
            os.remove(zip_name)
        except OSError:
            pass
    zip_file = zipfile.ZipFile(zip_name, mode='a')
    os.chdir(function_path)
    print('\n Following files will be zipped in {} and saved in the deployment/regional-s3-assets folder. \n--------------'
          '------------------------------------------------------------------------'.format(zip_name))
    for folder, subs, files in os.walk('.'):
        for filename in files:
            fpath = os.path.join(folder, filename)
            if fpath.endswith('.py') or fpath.endswith('.sh') or '.so' in fpath or 'cacert.pem' in fpath or 'schema' in fpath:
                if not any(x in fpath for x in exclude_list):
                    print(fpath)
                    zip_file.write(fpath)
    zip_file.close()
    os.chdir(orig_path)
    return


def make_dir(directory):
    # if exist skip else create dir
    try:
        os.stat(directory)
        print("\n Directory {} already exist... skipping".format(directory))
    except:
        print("\n Directory {} not found, creating now...".format(directory))
        os.makedirs(directory)


def main(argv):
    # if condition changes the path this script runs from command line '$ python source/bin/build_scripts/lambda_build.py'
    if 'bin' not in os.getcwd():
        os.chdir('./source/bin')

    # Create Lambda Zip
    function_path = '../../source'
    output_path = '../../deployment/regional-s3-assets/'
    make_dir(output_path)
    base_exclude = ['egg', 'requirement', 'setup', 'scratch', 'dist-info', '.so']
    print(argv)
    if 'help' in argv:
        print('Help: Please provide either or all the arguments as shown in the example below.')
        print('lambda_build.py avm_cr_lambda state_machine_lambda trigger_lambda deployment_lambda')
        sys.exit(2)
    else:
        for arg in argv:
            print('\n Building {} \n ==========================='.format(arg))
            if arg == 'state_machine_lambda':
                zip_file_name = 'custom-control-tower-state-machine'
                exclude = ['bin', 'config_deployer', 'custom_resource', 'trigger', 'jinja2', 'simplejson', 'markupsafe',
                           'yaml', 'yorm', 'netaddr', 'validation', 'manifest_handler', 'handshake_sm', 'add_on_config_deployer', 'launch_avm', 'publish',
                           'lifecycle_event_handler']
            elif arg == 'deployment_lambda':
                zip_file_name = 'custom-control-tower-config-deployer'
                exclude = ['bin', 'yorm', 'yaml', 'custom_resource', 'state_machine_', 'netaddr', 'validation', 'trigger',
                           'manifest_handler', 'handshake_sm', 'add_on_config_deployer', 'launch_avm', 'publish', 'lifecycle_event_handler']
            elif arg == 'build_scripts':
                zip_file_name = 'custom-control-tower-scripts'
                # DO NOT INCLUDE 'yaml' to the exclude list or else it will skip to include manifest.schema.yaml which will cause the build stage to fail
                exclude = ['config_deployer', 'state_machine_', 'simplejson', 'netaddr','yorm', 'jinja2', 'handshake_sm',
                           'markupsafe', 'custom_resource', 'certifi', 'chardet', 'idna' , 'requests', 'urllib3', 'add_on_config_deployer', 
                           'launch_avm', 'publish', 'lifecycle_event_handler']
            elif arg == 'scp_state_machine_trigger':
                zip_file_name = 'custom-control-tower-trigger-scp-sm'
                exclude = ['bin', 'config_deployer', 'custom_resource', 'trigger_stackset','add_on_config_deployer', 'launch_avm',
                           'netaddr', 'validation', 'manifest_handler', 'handshake_sm', 'publish', 'state_machine_', 'lifecycle_event_handler']
            elif arg == 'stackset_state_machine_trigger':
                zip_file_name = 'custom-control-tower-trigger-stackset-sm'
                exclude = ['bin', 'config_deployer', 'custom_resource', 'add_on_config_deployer', 'launch_avm', 'trigger_scp'
                           'netaddr', 'validation', 'manifest_handler', 'handshake_sm', 'publish', 'state_machine_', 'lifecycle_event_handler']
            elif arg == 'lifecycle_event_handler':
                zip_file_name = 'custom-control-tower-lifecycle-event-handler'
                exclude = ['bin', 'config_deployer', 'custom_resource', 'add_on_config_deployer', 'launch_avm', 'trigger_scp',
                           'jinja2','simplejson', 'markupsafe','yaml', 'yorm', 'netaddr', 'validation', 'manifest_handler', 'handshake_sm', 
                           'publish', 'state_machine_','trigger_stackset', 'state_machine_']
            else:
                print('Invalid argument... Please provide either or all the arguments as shown in the example below.')
                print('lambda_build.py avm_cr_lambda state_machine_lambda trigger_lambda deployment_lambda add_on_deployment_lambda')
                sys.exit(2)

            lambda_exclude = base_exclude + exclude
            zip_function(zip_file_name, function_path, output_path, lambda_exclude)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        print('No arguments provided. Please provide any combination of OR all 4 arguments as shown in the example below.')
        print('lambda_build.py avm_cr_lambda state_machine_lambda trigger_lambda deployment_lambda add_on_deployment_lambda')
        print('Example 2:')
        print('lambda_build.py avm_cr_lambda state_machine_lambda trigger_lambda')
        print('Example 3:')
        print('lambda_build.py avm_cr_lambda state_machine_lambda')
        print('Example 4:')
        print('lambda_build.py avm_cr_lambda')
        sys.exit(2)
