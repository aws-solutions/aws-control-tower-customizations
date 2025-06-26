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

# !/bin/python

import inspect
import os

from cfct.state_machine_handler import (
    CloudFormation,
    ResourceControlPolicy,
    ServiceControlPolicy,
    StackSetSMRequests,
)
from cfct.utils.logger import Logger

# initialise logger
log_level = os.environ["LOG_LEVEL"]
logger = Logger(loglevel=log_level)


def cloudformation(event, function_name):
    logger.info("Router FunctionName: {}".format(function_name))
    stack_set = CloudFormation(event, logger)
    if function_name == "describe_stack_set":
        response = stack_set.describe_stack_set()
    elif function_name == "describe_stack_set_operation":
        response = stack_set.describe_stack_set_operation()
    elif function_name == "list_stack_instances":
        response = stack_set.list_stack_instances()
    elif function_name == "list_stack_instances_account_ids":
        response = stack_set.list_stack_instances_account_ids()
    elif function_name == "create_stack_set":
        response = stack_set.create_stack_set()
    elif function_name == "create_stack_instances":
        response = stack_set.create_stack_instances()
    elif function_name == "update_stack_set":
        response = stack_set.update_stack_set()
    elif function_name == "update_stack_instances":
        response = stack_set.update_stack_instances()
    elif function_name == "delete_stack_set":
        response = stack_set.delete_stack_set()
    elif function_name == "delete_stack_instances":
        response = stack_set.delete_stack_instances()
    else:
        message = build_messages(1)
        logger.info(message)
        return {"Message": message}

    logger.info(response)
    return response


def service_control_policy(event, function_name):
    scp = ServiceControlPolicy(event, logger)
    logger.info("Router FunctionName: {}".format(function_name))
    if function_name == "list_policies":
        response = scp.list_policies()
    elif function_name == "list_policies_for_account":
        response = scp.list_policies_for_account()
    elif function_name == "list_policies_for_ou":
        response = scp.list_policies_for_ou()
    elif function_name == "create_policy":
        response = scp.create_policy()
    elif function_name == "update_policy":
        response = scp.update_policy()
    elif function_name == "delete_policy":
        response = scp.delete_policy()
    elif function_name == "configure_count":
        policy_list = event.get("ResourceProperties").get("PolicyList", [])
        logger.info("List of policies: {}".format(policy_list))
        event.update({"Index": 0})
        event.update({"Step": 1})
        event.update({"Count": len(policy_list)})
        return event
    elif function_name == "iterator":
        index = event.get("Index")
        step = event.get("Step")
        count = event.get("Count")
        policy_list = event.get("ResourceProperties").get("PolicyList", [])
        policy_to_apply = policy_list[index] if len(policy_list) > index else None

        if index < count:
            _continue = True
        else:
            _continue = False

        index = index + step

        event.update({"Index": index})
        event.update({"Step": step})
        event.update({"Continue": _continue})
        event.update({"PolicyName": policy_to_apply})
        return event
    elif function_name == "attach_policy":
        response = scp.attach_policy()
    elif function_name == "detach_policy":
        response = scp.detach_policy()
    elif function_name == "detach_policy_from_all_accounts":
        response = scp.detach_policy_from_all_accounts()
    elif function_name == "enable_policy_type":
        response = scp.enable_policy_type()
    elif function_name == "configure_count_2":
        ou_list = event.get("ResourceProperties").get("OUList", [])
        logger.info("List of OUs: {}".format(ou_list))
        event.update({"Index": 0})
        event.update({"Step": 1})
        event.update({"Count": len(ou_list)})
        return event
    elif function_name == "iterator2":
        index = event.get("Index")
        step = event.get("Step")
        count = event.get("Count")
        ou_list = event.get("ResourceProperties").get("OUList", [])
        ou_map = ou_list[index] if len(ou_list) > index else None

        if index < count:
            _continue = True
        else:
            _continue = False

        index = index + step

        event.update({"Index": index})
        event.update({"Step": step})
        event.update({"Continue": _continue})
        if ou_map:  # ou list example: [['ouname1','ouid1],'Attach']
            logger.info("[state_machine_router.service_control_policy] ou_map:  {}".format(ou_map))
            logger.debug(
                "[state_machine_router.service_control_policy] OUName: {}; OUId: {}; Operation: {}".format(
                    ou_map[0][0], ou_map[0][1], ou_map[1]
                )
            )

            event.update({"OUName": ou_map[0][0]})
            event.update({"OUId": ou_map[0][1]})
            event.update({"Operation": ou_map[1]})

        return event

    else:
        message = build_messages(1)
        logger.info(message)
        return {"Message": message}

    logger.info(response)
    return response


def resource_control_policy(event, function_name):
    rcp = ResourceControlPolicy(event, logger)
    logger.info("Router FunctionName: {}".format(function_name))
    if function_name == "list_policies":
        response = rcp.list_policies()
    elif function_name == "list_policies_for_account":
        response = rcp.list_policies_for_account()
    elif function_name == "list_policies_for_ou":
        response = rcp.list_policies_for_ou()
    elif function_name == "create_policy":
        response = rcp.create_policy()
    elif function_name == "update_policy":
        response = rcp.update_policy()
    elif function_name == "delete_policy":
        response = rcp.delete_policy()
    elif function_name == "configure_count":
        policy_list = event.get("ResourceProperties").get("PolicyList", [])
        logger.info("List of policies: {}".format(policy_list))
        event.update({"Index": 0})
        event.update({"Step": 1})
        event.update({"Count": len(policy_list)})
        return event
    elif function_name == "iterator":
        index = event.get("Index")
        step = event.get("Step")
        count = event.get("Count")
        policy_list = event.get("ResourceProperties").get("PolicyList", [])
        policy_to_apply = policy_list[index] if len(policy_list) > index else None

        if index < count:
            _continue = True
        else:
            _continue = False

        index = index + step

        event.update({"Index": index})
        event.update({"Step": step})
        event.update({"Continue": _continue})
        event.update({"PolicyName": policy_to_apply})
        return event
    elif function_name == "attach_policy":
        response = rcp.attach_policy()
    elif function_name == "detach_policy":
        response = rcp.detach_policy()
    elif function_name == "detach_policy_from_all_accounts":
        response = rcp.detach_policy_from_all_accounts()
    elif function_name == "enable_policy_type":
        response = rcp.enable_policy_type()
    elif function_name == "configure_count_2":
        ou_list = event.get("ResourceProperties").get("OUList", [])
        logger.info("List of OUs: {}".format(ou_list))
        event.update({"Index": 0})
        event.update({"Step": 1})
        event.update({"Count": len(ou_list)})
        return event
    elif function_name == "iterator2":
        index = event.get("Index")
        step = event.get("Step")
        count = event.get("Count")
        ou_list = event.get("ResourceProperties").get("OUList", [])
        ou_map = ou_list[index] if len(ou_list) > index else None

        if index < count:
            _continue = True
        else:
            _continue = False

        index = index + step

        event.update({"Index": index})
        event.update({"Step": step})
        event.update({"Continue": _continue})
        if ou_map:  # ou list example: [['ouname1','ouid1],'Attach']
            logger.info("[state_machine_router.resource_control_policy] ou_map:  {}".format(ou_map))
            logger.debug(
                "[state_machine_router.resource_control_policy] OUName: {}; OUId: {}; Operation: {}".format(
                    ou_map[0][0], ou_map[0][1], ou_map[1]
                )
            )

            event.update({"OUName": ou_map[0][0]})
            event.update({"OUId": ou_map[0][1]})
            event.update({"Operation": ou_map[1]})

        return event

    else:
        message = build_messages(1)
        logger.info(message)
        return {"Message": message}

    logger.info(response)
    return response


def stackset_sm_requests(event, function_name):
    sr = StackSetSMRequests(event, logger)
    logger.info("Router FunctionName: {}".format(function_name))

    if function_name == "ssm_put_parameters":
        response = sr.ssm_put_parameters()
    elif function_name == "export_cfn_output":
        response = sr.export_cfn_output()
    elif function_name == "send_execution_data":
        response = sr.send_execution_data()
    elif function_name == "random_wait":
        response = sr.random_wait()
    else:
        message = build_messages(1)
        logger.info(message)
        return {"Message": message}

    logger.info(response)
    return response


def build_messages(type):
    """build different logger messages based on type
    Args:
        type: int. determines what message to build

    Return:
        message
    """
    if type == 1:
        message = "Function name does not match any function" " in the handler file."
    elif type == 2:
        message = "Class name does not match any class" " in the handler file."
    else:
        message = "Class name not found in input."
    return message


def lambda_handler(event, context):
    # Lambda handler function
    try:
        logger.debug("Lambda_handler Event")
        logger.debug(event)
        # Execute custom resource handlers
        class_name = event.get("params", {}).get("ClassName")
        function_name = event.get("params", {}).get("FunctionName")

        if class_name is not None:
            if class_name == "CloudFormation":
                return cloudformation(event, function_name)
            elif class_name == "StackSetSMRequests":
                return stackset_sm_requests(event, function_name)
            elif class_name == "SCP":
                return service_control_policy(event, function_name)
            elif class_name == "RCP":
                return resource_control_policy(event, function_name)
            else:
                message = build_messages(2)
                logger.info(message)
                return {"Message": message}
        else:
            message = build_messages(3)
            logger.info(message)
            return {"Message": message}
    except Exception as e:
        logger.log_general_exception(__file__.split("/")[-1], inspect.stack()[0][3], e)
        raise
