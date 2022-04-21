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
from cfct.utils.decimal_encoder import DecimalEncoder
import json
import decimal
import pytest

@pytest.mark.unit
def test_decimal_encoder():
    assert json.dumps(
        {'x': decimal.Decimal('5.5')}, cls=DecimalEncoder) == json.dumps(
        {'x': 5.5})
    assert json.dumps(
        {'x': decimal.Decimal('5.0')}, cls=DecimalEncoder) == json.dumps(
        {'x': 5})
    encoder = DecimalEncoder()
    assert encoder.encode({'x': decimal.Decimal('5.65')}) == json.dumps(
        {'x': 5.65})
    assert encoder.encode({'x': decimal.Decimal('5.0')}) == json.dumps(
        {'x': 5})
    assert encoder.encode(
        {'x': decimal.Decimal('5.0'),
         'y': decimal.Decimal('5.5')}) == json.dumps({'x': 5, 'y': 5.5})

