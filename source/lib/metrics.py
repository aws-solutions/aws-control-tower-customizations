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

import json
from datetime import datetime
from lib.ssm import SSM
from decimal import Decimal
import inspect
import requests

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


class Metrics(object):
    def __init__(self, logger):
        self.logger = logger
        self.ssm = SSM(logger)

    def _get_parameter_value(self, key):
        response = self.ssm.describe_parameters(key)
        # get paramter if key exist
        if response:
            value = self.ssm.get_parameter(key)
        else:
            value = 'ssm-param-key-not-found'
        return value

    # Send anonymous metrics
    def metrics(self, data, solution_id='SO0089', url='https://metrics.awssolutionsbuilder.com/generic'):
        try:
            send_metrics = self._get_parameter_value('/org/primary/metrics_flag')
            if send_metrics.lower() == 'yes':
                uuid = self._get_parameter_value('/org/primary/customer_uuid')
                time_stamp = {'TimeStamp': str(datetime.utcnow().isoformat())}
                params = {'Solution': solution_id,
                          'UUID': uuid,
                          'Data': data}
                metrics = dict(time_stamp, **params)
                json_data = json.dumps(metrics, indent=4, cls=DecimalEncoder, sort_keys=True)
                headers = {'content-type': 'application/json'}
                r = requests.post(url, data=json_data, headers=headers)
                code = r.status_code
                return code
        except:
            pass