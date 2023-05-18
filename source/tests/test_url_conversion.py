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
from mock import patch, Mock
from boto3.session import Session
import pytest
from pytest import MonkeyPatch

from cfct.aws.utils.url_conversion import (
    build_http_url,
    convert_s3_url_to_http_url,
    parse_bucket_key_names,
)


@pytest.fixture
def mock_session() -> Session:
    mock_session = Mock(spec=Session)
    mock_session.session_name = "us-mock-1"
    mock_session.get_partition_for_region = Mock(return_value="mock-partition")
    mock_session.get_available_regions = Mock(return_value=["us-mock-1", "us-mock-2"])
    return mock_session


@pytest.fixture()
def mock_bucket_name() -> str:
    return "mock-bucket-name"


@pytest.fixture()
def mock_key_name() -> str:
    return "key/path/in/bucket"


@pytest.fixture()
def mock_region_name() -> str:
    return "us-mock-1"


@pytest.fixture
def virtual_host_s3_url(mock_bucket_name: str, mock_key_name: str, mock_region_name: str) -> str:
    return f"https://{mock_bucket_name}.s3.{mock_region_name}.amazonaws.com/{mock_key_name}"


@pytest.fixture
def http_path_s3_url(mock_bucket_name: str, mock_key_name: str, mock_region_name: str) -> str:
    return f"https://s3.{mock_region_name}.amazonaws.com/{mock_bucket_name}/{mock_key_name}"


@pytest.fixture
def s3_url(mock_bucket_name: str, mock_key_name: str) -> str:
    return f"s3://{mock_bucket_name}/{mock_key_name}"


@pytest.mark.unit
def test_s3_url_to_http_url(mock_region_name: str, s3_url: str, virtual_host_s3_url: str, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("AWS_REGION", mock_region_name)
    assert convert_s3_url_to_http_url(s3_url) == virtual_host_s3_url


@pytest.mark.unit
def test_virtual_hosted_style_http_url_to_s3_url(mock_session: Session, virtual_host_s3_url: str, mock_bucket_name: str, mock_key_name: str, mock_region_name: str):
    with patch("cfct.aws.utils.url_conversion.Session", return_value=mock_session):
        bucket, key, region = parse_bucket_key_names(virtual_host_s3_url)
    assert mock_bucket_name == bucket
    assert mock_key_name == key
    assert mock_region_name == region


@pytest.mark.unit
def test_path_style_http_url_to_s3_url(
        mock_session: Session,
        http_path_s3_url: str,
        mock_bucket_name: str,
        mock_region_name: str,
        mock_key_name: str
    ):
    
    with patch("cfct.aws.utils.url_conversion.Session", return_value=mock_session):
        bucket, key, region = parse_bucket_key_names(http_path_s3_url)
    assert mock_bucket_name == bucket
    assert mock_key_name == key
    assert mock_region_name == region


@pytest.mark.unit
def test_build_http_url(mock_bucket_name: str, mock_key_name: str):
    http_url = build_http_url(mock_bucket_name, mock_key_name)
    assert http_url.startswith("https://")
    assert http_url.endswith(mock_key_name)
