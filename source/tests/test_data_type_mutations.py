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


from lib.logger import Logger
from trigger_stackset_sm import DeployStackSetStateMachine


log_level = 'info'
logger = Logger(loglevel=log_level)
wait_time = 30
manifest_file_path = './manifest.yaml'
sm_arn_stackset = 'arn::::::stackset'
staging_bucket = 'bucket_name'
execution_mode = 'parallel'


dss = DeployStackSetStateMachine(logger, wait_time, manifest_file_path, sm_arn_stackset, staging_bucket, execution_mode)

def test_list_item_conversion():
    list_of_numbers = [1234, 5678]
    list_of_strings = dss._convert_list_values_to_string(list_of_numbers)
    for string in list_of_strings:
        assert type(string) is str