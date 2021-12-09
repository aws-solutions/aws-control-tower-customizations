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
import pytest
import mock
from utils.logger import Logger
import manifest.manifest_parser as parse

TESTS_DIR = './tests/'

logger = Logger(loglevel='info')

os.environ['ACCOUNT_LIST'] = ''

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
    dev_map_2 = {
        "AccountName": "Developer1-SuperSet",
        "AccountEmail": "dev-2@mock",
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
    dev_account_id_2 = org_client.create_account(
        AccountName=dev_map_2['AccountName'],
        Email=dev_map_2['AccountEmail'])["CreateAccountStatus"]["AccountId"]
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
        AccountId=dev_account_id_2, SourceParentId=root_id,
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

    # Get account list
    os.environ['ACCOUNT_LIST'] = dev_account_id + ','+ dev_account_id_2 + ','+  test_account_id + ','+  prod_account_id

    yield


def test_version_1_manifest_scp_sm_input(s3_setup, organizations_setup, ssm_client):
    manifest_name = 'manifest_version_1.yaml'
    file_path = TESTS_DIR + manifest_name
    os.environ['MANIFEST_FILE_NAME'] = manifest_name
    os.environ['MANIFEST_FILE_PATH'] = file_path
    os.environ['MANIFEST_FOLDER'] = file_path[:-len(manifest_name)]
    os.environ['STAGE_NAME'] = 'scp'
    sm_input_list = parse.scp_manifest()
    logger.info("[test_version_1_manifest_scp_sm_input] SCP sm_input_list for manifest_version_1.yaml:")
    logger.info(sm_input_list)
    logger.info(sm_input_list[0])
    assert sm_input_list[0]['ResourceProperties']['PolicyDocument'][
               'Name'] == "test-preventive-guardrails"
    assert sm_input_list[1]['ResourceProperties']['PolicyDocument'][
               'Name'] == "test-guardrails-2"


def test_version_2_manifest_scp_sm_input(s3_setup, organizations_setup, ssm_client):
    manifest_name = 'manifest_version_2.yaml'
    file_path = TESTS_DIR + manifest_name
    os.environ['MANIFEST_FILE_NAME'] = manifest_name
    os.environ['MANIFEST_FILE_PATH'] = file_path
    os.environ['MANIFEST_FOLDER'] = file_path[:-len(manifest_name)]
    os.environ['STAGE_NAME'] = 'scp'

    sm_input_list = parse.scp_manifest()
    logger.info("[test_version_2_manifest_scp_sm_input] SCP sm_input_list for manifest_version_2.yaml:")
    logger.info(sm_input_list)
    assert sm_input_list[0]['ResourceProperties']['PolicyDocument'][
               'Name'] == "test-preventive-guardrails"
    assert sm_input_list[1]['ResourceProperties']['PolicyDocument'][
               'Name'] == "test-guardrails-2"


def test_version_1_manifest_stackset_sm_input(s3_setup, organizations_setup,
                                              ssm_client):
    # mock API call and assign return value
    with mock.patch("manifest.manifest_parser.OrganizationsData.get_accounts_in_ct_baseline_config_stack_set", mock.MagicMock(return_value=[list(os.environ['ACCOUNT_LIST'].split(',')),[]])):         
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
                                              ssm_client, mocker):

    logger.info('os.environ[ACCOUNT_LIST]: {}'.format(list(os.environ['ACCOUNT_LIST'].split(','))))

    # mock API call and assign return value
    with mock.patch("manifest.manifest_parser.OrganizationsData.get_accounts_in_ct_baseline_config_stack_set", mock.MagicMock(return_value=[list(os.environ['ACCOUNT_LIST'].split(',')),[]])):                        
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
        # check the account list should have 2 accounts - Developer1 only (not
        # Developer1-SuperSet
        assert len(sm_input_list[0]['ResourceProperties']['AccountList']) == 2
        # check if export_outputs is not defined then SSMParameters is set to
        # empty dict
        assert sm_input_list[1]['ResourceProperties']['SSMParameters'] == {}
        # check the account list should have 3 accounts - Developer1 only (not
        # Developer1-SuperSet
        assert len(sm_input_list[1]['ResourceProperties']['AccountList']) == 3
        # check if empty OU, account list should be empty string
        assert sm_input_list[2]['ResourceProperties']['AccountList'] == []
        # parameters key has empty dict
        assert sm_input_list[2]['ResourceProperties']['Parameters'] == {}


def test_root_ou_stackset(mocker):
    org = parse.OrganizationsData()
    mocker.patch.object(org.stack_set, 'get_accounts_and_regions_per_stack_set')
    org.stack_set.get_accounts_and_regions_per_stack_set.return_value = ['000', '111'],[]
    ou_id_to_account_map = {}
    ou_name_to_id_map = {}
    ou_list = ['Root']
    resp = org.get_accounts_in_ou(ou_id_to_account_map, ou_name_to_id_map, ou_list)
    assert resp == ['000', '111']


def test_root_ou_stackset_no():
    org = parse.OrganizationsData()
    ou_id_to_account_map = {}
    ou_name_to_id_map = {}
    ou_list = ['Dev']
    resp = org.get_accounts_in_ou(ou_id_to_account_map, ou_name_to_id_map, ou_list)
    assert resp == []