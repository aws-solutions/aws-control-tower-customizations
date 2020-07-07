import os
import sys
from utils.logger import Logger
from manifest.sm_input_builder import InputBuilder, SCPResourceProperties

logger = Logger('info')

# declare SCP state machine input variables
name = "policy_name"
description = "policy_description"
policy_url = "https://s3.amazonaws.com/bucket/prefix"
account_id = "account_id_1"
policy_list = []
operation = "operation_id"
ou_list = [
    [
        "ou_name_1",
        "Attach"
    ],
    [
        "ou_name_2",
        "Attach"
    ]
]

def build_scp_input(name, description, policy_url,
                    policy_list, account_id,
                    operation, ou_list):
    # get SCP output
    resource_properties = SCPResourceProperties(name, description, policy_url,
                                                policy_list, account_id,
                                                operation, ou_list)
    scp_input = InputBuilder(resource_properties.get_scp_input_map())
    return scp_input.input_map()

def test_default_delimiter():
    scp_input = build_scp_input(name, description, policy_url,
                                policy_list, account_id,
                                operation, ou_list)
    assert scp_input.get("ResourceProperties").get("OUNameDelimiter") == ':'
