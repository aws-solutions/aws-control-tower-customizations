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

import os
from datetime import datetime
from json import dumps

import requests
from cfct.aws.services.ssm import SSM
from cfct.utils.decimal_encoder import DecimalEncoder


class SolutionMetrics(object):
    """This class is used to send anonymous metrics from customer using
    the solution to the Solutions Builder team when customer choose to
    have their data sent during the deployment of the solution.
    """

    def __init__(self, logger):
        self.logger = logger
        self.ssm = SSM(logger)

    def _get_parameter_value(self, key):
        response = self.ssm.describe_parameters(key)
        # get parameter if key exist
        if response:
            value = self.ssm.get_parameter(key)
        else:
            value = "ssm-param-key-not-found"
        return value

    def solution_metrics(
        self,
        data,
        solution_id=os.environ.get("SOLUTION_ID"),
        url=os.environ.get("METRICS_URL"),
    ):

        """Sends anonymous customer metrics to s3 via API gateway owned and
           managed by the Solutions Builder team.

        Args:
            data: anonymous customer metrics to be sent
            solution_id: unique id of the solution
            url: url for API Gateway via which data is sent

        Return: status code returned by https post request
        """
        try:
            send_metrics = self._get_parameter_value("/org/primary/" "metrics_flag")
            if send_metrics.lower() == "yes":
                uuid = self._get_parameter_value("/org/primary/customer_uuid")
                time_stamp = {"TimeStamp": str(datetime.utcnow().isoformat())}
                params = {"Solution": solution_id, "UUID": uuid, "Data": data}
                metrics = dict(time_stamp, **params)
                json_data = dumps(metrics, cls=DecimalEncoder)
                headers = {"content-type": "application/json"}
                r = requests.post(url, data=json_data, headers=headers)
                code = r.status_code
                return code
        except:
            pass
