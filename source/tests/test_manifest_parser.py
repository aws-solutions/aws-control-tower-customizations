import os
import pytest
from utils.logger import Logger
import manifest.manifest_parser as parse

TESTS_DIR = './tests/'

logger = Logger(loglevel='info')


@pytest.fixture
def bucket_name():
    return os.getenv('STAGING_BUCKET')


@pytest.fixture
def s3_setup(s3_client, bucket_name):
    s3_client.create_bucket(Bucket=bucket_name)
    yield


@pytest.fixture
def organizations_setup(org_client):
    dev_map = {
        "AccountName": "Developer1",
        "AccountEmail": "dev@mock",
        "OUName": "Dev"
    }
    prod_map = {
        "AccountName": "Production1",
        "AccountEmail": "prod@mock",
        "OUName": "Prod"
    }

    test_map = {
        "AccountName": "Testing1",
        "AccountEmail": "test@mock",
        "OUName": "Test"
    }
    # create organization
    org_client.create_organization(FeatureSet="ALL")
    root_id = org_client.list_roots()["Roots"][0]["Id"]

    # create accounts
    dev_account_id = org_client.create_account(
        AccountName=dev_map['AccountName'],
        Email=dev_map['AccountEmail'])["CreateAccountStatus"]["AccountId"]
    test_account_id = org_client.create_account(
        AccountName=test_map['AccountName'],
        Email=test_map['AccountEmail'])["CreateAccountStatus"]["AccountId"]
    prod_account_id = org_client.create_account(
        AccountName=prod_map['AccountName'],
        Email=prod_map['AccountEmail'])["CreateAccountStatus"]["AccountId"]

    # create org units
    dev_resp = org_client.create_organizational_unit(ParentId=root_id,
                                                     Name=dev_map['OUName'])
    dev_ou_id = dev_resp["OrganizationalUnit"]["Id"]
    test_resp = org_client.create_organizational_unit(ParentId=root_id,
                                                      Name=test_map['OUName'])
    test_ou_id = test_resp["OrganizationalUnit"]["Id"]
    prod_resp = org_client.create_organizational_unit(ParentId=root_id,
                                                      Name=prod_map['OUName'])
    prod_ou_id = prod_resp["OrganizationalUnit"]["Id"]

    # move accounts
    org_client.move_account(
        AccountId=dev_account_id, SourceParentId=root_id,
        DestinationParentId=dev_ou_id
    )
    org_client.move_account(
        AccountId=test_account_id, SourceParentId=root_id,
        DestinationParentId=test_ou_id
    )
    org_client.move_account(
        AccountId=prod_account_id, SourceParentId=root_id,
        DestinationParentId=prod_ou_id
    )
    yield


def test_version_1_manifest_scp_sm_input(s3_setup):
    manifest_name = 'manifest_version_1.yaml'
    file_path = TESTS_DIR + manifest_name
    os.environ['MANIFEST_FILE_NAME'] = manifest_name
    os.environ['MANIFEST_FILE_PATH'] = file_path
    os.environ['MANIFEST_FOLDER'] = file_path[:-len(manifest_name)]
    os.environ['STAGE_NAME'] = 'scp'
    sm_input_list = parse.scp_manifest()
    logger.info("SCP sm_input_list:")
    logger.info(sm_input_list)
    logger.info(sm_input_list[0])
    assert sm_input_list[0]['ResourceProperties']['PolicyDocument'][
               'Name'] == "test-preventive-guardrails"
    assert sm_input_list[1]['ResourceProperties']['PolicyDocument'][
               'Name'] == "test-guardrails-2"


def test_version_2_manifest_scp_sm_input(s3_setup):
    manifest_name = 'manifest_version_2.yaml'
    file_path = TESTS_DIR + manifest_name
    os.environ['MANIFEST_FILE_NAME'] = manifest_name
    os.environ['MANIFEST_FILE_PATH'] = file_path
    os.environ['MANIFEST_FOLDER'] = file_path[:-len(manifest_name)]
    os.environ['STAGE_NAME'] = 'scp'

    sm_input_list = parse.scp_manifest()
    logger.info("SCP sm_input_list:")
    logger.info(sm_input_list)
    assert sm_input_list[0]['ResourceProperties']['PolicyDocument'][
               'Name'] == "test-preventive-guardrails"
    assert sm_input_list[1]['ResourceProperties']['PolicyDocument'][
               'Name'] == "test-guardrails-2"


def test_version_1_manifest_stackset_sm_input(s3_setup, organizations_setup,
                                              ssm_client):
    manifest_name = 'manifest_version_1.yaml'
    file_path = TESTS_DIR + manifest_name
    os.environ['MANIFEST_FILE_NAME'] = manifest_name
    os.environ['MANIFEST_FILE_PATH'] = file_path
    os.environ['MANIFEST_FOLDER'] = file_path[:-len(manifest_name)]
    os.environ['STAGE_NAME'] = 'stackset'
    sm_input_list = parse.stack_set_manifest()
    logger.info("Stack Set sm_input_list:")
    logger.info(sm_input_list)
    assert sm_input_list[0]['ResourceProperties']['StackSetName'] == \
           "CustomControlTower-stackset-1"
    assert sm_input_list[1]['ResourceProperties']['StackSetName'] == \
           "CustomControlTower-stackset-2"


def test_version_2_manifest_stackset_sm_input(s3_setup, organizations_setup,
                                              ssm_client):
    manifest_name = 'manifest_version_2.yaml'
    file_path = TESTS_DIR + manifest_name
    os.environ['MANIFEST_FILE_NAME'] = manifest_name
    os.environ['MANIFEST_FILE_PATH'] = file_path
    os.environ['MANIFEST_FOLDER'] = file_path[:-len(manifest_name)]
    os.environ['STAGE_NAME'] = 'stackset'
    sm_input_list = parse.stack_set_manifest()
    logger.info("Stack Set sm_input_list:")
    logger.info(sm_input_list)
    # check if namespace CustomControlTower is added to the stack name
    assert sm_input_list[0]['ResourceProperties']['StackSetName'] == \
           "CustomControlTower-stackset-1"
    # check if export_outputs is not defined then SSMParameters is set to
    # empty dict
    assert sm_input_list[1]['ResourceProperties']['SSMParameters'] == {}
    # check if empty OU, account list should be empty string
    assert sm_input_list[2]['ResourceProperties']['AccountList'] == []
