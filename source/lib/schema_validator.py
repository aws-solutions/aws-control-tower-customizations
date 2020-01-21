
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

#!/usr/bin/env python

import os,sys
# pykwalify imports
import pykwalify
from pykwalify.core import Core
from pykwalify.errors import SchemaError, CoreError

function_path = os.path.normpath('../../deployment/custom_control_tower_framework')
if os.path.isfile(os.path.join(function_path, 'manifest.yaml')):
    source_f = os.path.join(function_path, 'manifest.yaml')
if os.path.isfile(os.path.join(function_path, 'manifest.schema.yaml')):
    schema_f = os.path.join(function_path, 'manifest.schema.yaml')

c = Core(source_file=str(source_f), schema_files=[str(schema_f)])
try:
    c.validate(raise_exception=True)
except SchemaError:
    print("Schema Error: ")
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise