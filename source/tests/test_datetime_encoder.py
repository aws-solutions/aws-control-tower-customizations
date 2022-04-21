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
from cfct.utils.datetime_encoder import DateTimeEncoder
from datetime import datetime, date
import json
import pytest

@pytest.mark.unit
def test_datetime_encoder():
    datetime_str = '02/17/20 23:38:26'
    datetime_object = datetime.strptime(datetime_str, '%m/%d/%y %H:%M:%S')
    date_object = datetime_object.date()
    encoder = DateTimeEncoder()
    assert encoder.encode({"datetime": datetime_object}) == json.dumps(
        {"datetime": "2020-02-17T23:38:26"})
    assert json.dumps(
        {"datetime": datetime_object}, cls=DateTimeEncoder) == json.dumps(
        {"datetime": "2020-02-17T23:38:26"})
    assert encoder.encode({"date": date_object}) == json.dumps(
        {"date": "2020-02-17"})
    assert json.dumps(
        {"date": date_object}, cls=DateTimeEncoder) == json.dumps(
        {"date": "2020-02-17"})
    assert encoder.encode(
        {"date": date_object, "datetime": datetime_object}) == json.dumps(
        {"date": "2020-02-17", "datetime": "2020-02-17T23:38:26"})
