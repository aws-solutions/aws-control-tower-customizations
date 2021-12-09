import os
import pytest

BUCKET_NAME = "test-bucket"

@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests():
    os.environ['STAGING_BUCKET'] = BUCKET_NAME
    os.environ['TEMPLATE_KEY_PREFIX'] = '_custom_ct_templates_staging'
    os.environ['LOG_LEVEL'] = 'info'
    os.environ['STAGE_NAME'] = 'stackset'
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['CAPABILITIES'] = 'CAPABILITY_NAMED_IAM, CAPABILITY_AUTO_EXPAND'


