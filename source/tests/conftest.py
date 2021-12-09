import pytest
import boto3
from os import environ
from moto import mock_s3, mock_organizations, mock_ssm, mock_cloudformation


@pytest.fixture(scope='module')
def aws_credentials():
    """Mocked AWS Credentials for moto"""
    environ['AWS_ACCESS_KEY_ID'] = 'testing'
    environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    environ['AWS_SECURITY_TOKEN'] = 'testing'
    environ['AWS_SESSION_TOKEN'] = 'testing'


@pytest.fixture(scope='module')
def s3_client(aws_credentials):
    """S3 Mock Client"""
    with mock_s3():
        connection = boto3.client("s3", region_name="us-east-1")
        yield connection


@pytest.fixture(scope='module')
def s3_client_resource(aws_credentials):
    """S3 Mock Client"""
    with mock_s3():
        connection = boto3.resource("s3", region_name="us-east-1")
        yield connection


@pytest.fixture(scope='module')
def org_client(aws_credentials):
    """Organizations Mock Client"""
    with mock_organizations():
        connection = boto3.client("organizations", region_name="us-east-1")
        yield connection


@pytest.fixture(scope='module')
def ssm_client(aws_credentials):
    """SSM Mock Client"""
    with mock_ssm():
        connection = boto3.client("ssm", region_name="us-east-1")
        yield connection
