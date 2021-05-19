import os
import sys
import json
from utils.logger import Logger
from manifest.manifest import Manifest
from manifest.stage_to_s3 import StageFile
from manifest.sm_input_builder import InputBuilder, SCPResourceProperties, \
    StackSetResourceProperties
from utils.parameter_manipulation import transform_params
from utils.string_manipulation import convert_list_values_to_string
from aws.services.s3 import S3
from aws.services.organizations import Organizations
from manifest.cfn_params_handler import CFNParamsHandler
from metrics.solution_metrics import SolutionMetrics

VERSION_1 = '2020-01-01'
VERSION_2 = '2021-03-15'

logger = Logger(loglevel=os.environ['LOG_LEVEL'])


def scp_manifest():
    # determine manifest version
    manifest = Manifest(os.environ.get('MANIFEST_FILE_PATH'))
    if manifest.version == VERSION_1:
        get_scp_input = SCPParser()
        return get_scp_input.parse_scp_manifest_v1()
    elif manifest.version == VERSION_2:
        get_scp_input = SCPParser()
        return get_scp_input.parse_scp_manifest_v2()


def stack_set_manifest():
    # determine manifest version
    manifest = Manifest(os.environ.get('MANIFEST_FILE_PATH'))
    send = SolutionMetrics(logger)
    if manifest.version == VERSION_1:
        data = {"ManifestVersion": VERSION_1}
        send.solution_metrics(data)
        get_stack_set_input = StackSetParser()
        return get_stack_set_input.parse_stack_set_manifest_v1()
    elif manifest.version == VERSION_2:
        data = {"ManifestVersion": VERSION_2}
        send.solution_metrics(data)
        get_stack_set_input = StackSetParser()
        return get_stack_set_input.parse_stack_set_manifest_v2()


class SCPParser:
    """
    This class parses the Service Control Policies resources from the manifest
    file. It converts the yaml (manifest) into JSON input for the SCP state
    machine.
    :return List of JSON

    Example:
        get_scp_input = SCPParser()
        list_of_inputs = get_scp_input.parse_scp_manifest_v1|2()
    """

    def __init__(self):
        self.logger = logger
        self.manifest = Manifest(os.environ.get('MANIFEST_FILE_PATH'))

    def parse_scp_manifest_v1(self) -> list:
        state_machine_inputs = []
        self.logger.info(
            "Processing SCPs from {} file".format(
                os.environ.get('MANIFEST_FILE_PATH')))
        build = BuildStateMachineInput(self.manifest.region)
        for policy in self.manifest.organization_policies:
            local_file = StageFile(self.logger, policy.policy_file)
            policy_url = local_file.get_staged_file()
            # Generate the list of OUs to attach this SCP to
            attach_ou_list = set(policy.apply_to_accounts_in_ou)

            state_machine_inputs.append(build.scp_sm_input(
                attach_ou_list,
                policy,
                policy_url))

        # Exit if there are no organization policies
        if len(state_machine_inputs) == 0:
            self.logger.info("Organization policies not found"
                             " in the manifest.")
            sys.exit(0)
        else:
            return state_machine_inputs

    def parse_scp_manifest_v2(self) -> list:
        state_machine_inputs = []
        self.logger.info(
            "Processing SCPs from {} file".format(
                os.environ.get('MANIFEST_FILE_PATH')))
        build = BuildStateMachineInput(self.manifest.region)
        for resource in self.manifest.resources:
            if resource.deploy_method == 'scp':
                local_file = StageFile(self.logger, resource.resource_file)
                policy_url = local_file.get_staged_file()
                attach_ou_list = set(
                    resource.deployment_targets.organizational_units)
                state_machine_inputs.append(build.scp_sm_input(
                    attach_ou_list,
                    resource,
                    policy_url))

        # Exit if there are no organization policies
        if len(state_machine_inputs) == 0:
            self.logger.info("Organization policies not found"
                             " in the manifest.")
            sys.exit(0)
        else:
            return state_machine_inputs


class StackSetParser:
    """
    This class parses the Stack Set resources from the manifest file.
    It converts the yaml (manifest) into JSON input for the Stack Set state
    machine.
    :return List of JSON

    Example:
        get_scp_input = StackSetParser()
        list_of_inputs = get_scp_input.parse_stack_set_manifest_v1|2()
    """
    def __init__(self):
        self.logger = logger
        self.manifest = Manifest(os.environ.get('MANIFEST_FILE_PATH'))
        self.manifest_folder = os.environ.get('MANIFEST_FOLDER')

    def parse_stack_set_manifest_v1(self) -> list:

        self.logger.info("Parsing Core Resources from {} file"
                         .format(os.environ.get('MANIFEST_FILE_PATH')))
        build = BuildStateMachineInput(self.manifest.region)
        org = OrganizationsData()
        organizations_data = org.get_organization_details()
        state_machine_inputs = []

        for resource in self.manifest.cloudformation_resources:
            self.logger.info(f">>>> START : {resource.name} >>>>")
            accounts_in_ou = []

            # build OU to accounts map if OU list present in manifest
            if resource.deploy_to_ou:
                accounts_in_ou = org.get_accounts_in_ou(
                    organizations_data.get("OuIdToAccountMap"),
                    organizations_data.get("OuNameToIdMap"),
                    resource.deploy_to_ou)

            # convert account numbers to string type
            account_list = convert_list_values_to_string(
                resource.deploy_to_account)
            self.logger.info(">>>>>> ACCOUNT LIST")
            self.logger.info(account_list)

            sanitized_account_list = org.get_final_account_list(
                account_list, organizations_data.get("AccountsInAllOUs"),
                accounts_in_ou, organizations_data.get("NameToAccountMap"))

            self.logger.info("Print merged account list - accounts in manifest"
                             " + account under OU in manifest")
            self.logger.info(sanitized_account_list)

            if resource.deploy_method.lower() == 'stack_set':
                sm_input = build.stack_set_state_machine_input_v1(
                    resource, sanitized_account_list)
                state_machine_inputs.append(sm_input)
            else:
                raise ValueError(
                    f"Unsupported deploy_method: {resource.deploy_method} "
                    f"found for resource {resource.name}")
            self.logger.info(f"<<<<<<<<< FINISH : {resource.name} <<<<<<<<<")

        # Exit if there are no CloudFormation resources
        if len(state_machine_inputs) == 0:
            self.logger.info("CloudFormation resources not found in the "
                             "manifest")
            sys.exit(0)
        else:
            return state_machine_inputs

    def parse_stack_set_manifest_v2(self) -> list:

        self.logger.info("Parsing Core Resources from {} file"
                         .format(os.environ.get('MANIFEST_FILE_PATH')))
        build = BuildStateMachineInput(self.manifest.region)
        org = OrganizationsData()
        organizations_data = org.get_organization_details()
        state_machine_inputs = []

        for resource in self.manifest.resources:
            if resource.deploy_method == 'stack_set':
                self.logger.info(f">>>> START : {resource.name} >>>>")
                accounts_in_ou = []

                # build OU to accounts map if OU list present in manifest
                if resource.deployment_targets.organizational_units:
                    accounts_in_ou = org.get_accounts_in_ou(
                        organizations_data.get("OuIdToAccountMap"),
                        organizations_data.get("OuNameToIdMap"),
                        resource.deployment_targets.organizational_units)

                # convert account numbers to string type
                account_list = convert_list_values_to_string(
                    resource.deployment_targets.accounts)
                self.logger.info(">>>>>> ACCOUNT LIST")
                self.logger.info(account_list)

                sanitized_account_list = org.get_final_account_list(
                    account_list, organizations_data.get("AccountsInAllOUs"),
                    accounts_in_ou, organizations_data.get("NameToAccountMap"))

                self.logger.info("Print merged account list - accounts in "
                                 "manifest + account under OU in manifest")
                self.logger.info(sanitized_account_list)

                if resource.deploy_method.lower() == 'stack_set':
                    sm_input = build.stack_set_state_machine_input_v2(
                        resource, sanitized_account_list)
                    state_machine_inputs.append(sm_input)
                else:
                    raise ValueError(
                        f"Unsupported deploy_method: {resource.deploy_method} "
                        f"found for resource {resource.name}")
                self.logger.info(f"<<<<<<<<< FINISH : {resource.name} <<<<<<<<")

        # Exit if there are no CloudFormation resources
        if len(state_machine_inputs) == 0:
            self.logger.info("CloudFormation resources not found in the "
                             "manifest")
            sys.exit(0)
        else:
            return state_machine_inputs


class BuildStateMachineInput:
    """
    This class build state machine inputs for SCP and Stack Set state machines

    """
    def __init__(self, region):
        self.logger = logger
        self.param_handler = CFNParamsHandler(logger)
        self.manifest_folder = os.environ.get('MANIFEST_FOLDER')
        self.region = region
        self.s3 = S3(logger)

    def scp_sm_input(self, attach_ou_list, policy, policy_url) -> dict:
        ou_list = []

        for ou in attach_ou_list:
            ou_list.append((ou, 'Attach'))
        resource_properties = SCPResourceProperties(policy.name,
                                                    policy.description,
                                                    policy_url,
                                                    ou_list)
        scp_input = InputBuilder(resource_properties.get_scp_input_map())
        sm_input = scp_input.input_map()
        self.logger.debug("&&&&& sm_input &&&&&&")
        self.logger.debug(sm_input)
        return sm_input

    def stack_set_state_machine_input_v1(self, resource, account_list) -> dict:

        local_file = StageFile(self.logger, resource.template_file)
        template_url = local_file.get_staged_file()

        # set region variables
        if len(resource.regions) > 0:
            region = resource.regions[0]
            region_list = resource.regions
        else:
            region = self.region
            region_list = [region]

        # if parameter file link is provided for the CFN resource

        parameters = self._load_params_from_file(resource.parameter_file)

        sm_params = self.param_handler.update_params(parameters, account_list,
                                                     region, False)

        ssm_parameters = self._create_ssm_input_map(resource.ssm_parameters)

        # generate state machine input list
        stack_set_name = "CustomControlTower-{}".format(resource.name)
        resource_properties = StackSetResourceProperties(stack_set_name,
                                                         template_url,
                                                         sm_params,
                                                         os.environ
                                                         .get('CAPABILITIES'),
                                                         account_list,
                                                         region_list,
                                                         ssm_parameters)
        ss_input = InputBuilder(resource_properties.get_stack_set_input_map())
        return ss_input.input_map()

    def stack_set_state_machine_input_v2(self, resource, account_list) -> dict:

        local_file = StageFile(self.logger, resource.resource_file)
        template_url = local_file.get_staged_file()

        parameters = {}
        # set region variables
        if len(resource.regions) > 0:
            region = resource.regions[0]
            region_list = resource.regions
        else:
            region = self.region
            region_list = [region]

        # if parameter file link is provided for the CFN resource
        if resource.parameter_file == "":
            self.logger.info("parameter_file property not found in the "
                             "manifest")
            self.logger.info(resource.parameter_file)
            self.logger.info(resource.parameters)
            parameters = self._load_params_from_manifest(resource.parameters)
        elif not resource.parameters:
            self.logger.info("parameters property not found in the "
                             "manifest")
            self.logger.info(resource.parameter_file)
            self.logger.info(resource.parameters)
            parameters = self._load_params_from_file(resource.parameter_file)

        sm_params = self.param_handler.update_params(parameters, account_list,
                                                     region, False)

        self.logger.info("Input Parameters for State Machine: {}".format(
            sm_params))

        ssm_parameters = self._create_ssm_input_map(resource.export_outputs)

        # generate state machine input list
        stack_set_name = "CustomControlTower-{}".format(resource.name)
        resource_properties = StackSetResourceProperties(stack_set_name,
                                                         template_url,
                                                         sm_params,
                                                         os.environ
                                                         .get('CAPABILITIES'),
                                                         account_list,
                                                         region_list,
                                                         ssm_parameters)
        ss_input = InputBuilder(resource_properties.get_stack_set_input_map())
        return ss_input.input_map()

    def _load_params_from_manifest(self, parameter_list: list):

        self.logger.info("Replace the keys with CloudFormation "
                         "Parameter data type")
        params_list = []
        for item in parameter_list:
            # must initialize params inside loop to avoid overwriting values
            # for existing items
            params = {}
            params.update({"ParameterKey": item.parameter_key})
            params.update({"ParameterValue": item.parameter_value})
            params_list.append(params)
        return params_list

    def _load_params_from_file(self, relative_parameter_path):
        if relative_parameter_path.lower().startswith('s3'):
            parameter_file = self.s3.get_s3_object(relative_parameter_path)
        else:
            parameter_file = os.path.join(self.manifest_folder,
                                          relative_parameter_path)

        self.logger.info("Parsing the parameter file: {}".format(
            parameter_file))

        with open(parameter_file, 'r') as content_file:
            parameter_file_content = content_file.read()

        params = json.loads(parameter_file_content)
        return params

    def _create_ssm_input_map(self, ssm_parameters):
        ssm_input_map = {}

        for ssm_parameter in ssm_parameters:
            key = ssm_parameter.name
            value = ssm_parameter.value
            ssm_value = self.param_handler.update_params(
                transform_params({key: value})
            )
            ssm_input_map.update(ssm_value)
        return ssm_input_map


class OrganizationsData:
    """
    This class build organization details including active accounts under
    an OU, account to OU mapping, OU name to OU id mapping, account name to
    account id mapping, etc.
    """
    def __init__(self):
        self.logger = logger

    def get_accounts_in_ou(self, ou_id_to_account_map, ou_name_to_id_map,
                           ou_list):
        accounts_in_ou = []
        ou_ids_manifest = []

        # convert OU Name to OU IDs
        for ou_name in ou_list:
            ou_id = [value for key, value in ou_name_to_id_map.items()
                     if ou_name == key]
            ou_ids_manifest.extend(ou_id)

        # convert OU IDs to accounts
        for ou_id, accounts in ou_id_to_account_map.items():
            if ou_id in ou_ids_manifest:
                accounts_in_ou.extend(accounts)
        self.logger.info(">>> Accounts: {} in OUs: {}"
                         .format(accounts_in_ou, ou_list))
        return accounts_in_ou

    def get_final_account_list(self, account_list, accounts_in_all_ous,
                               accounts_in_ou, name_to_account_map):
        # separate account id and emails
        name_list = []
        new_account_list = []
        self.logger.info(account_list)
        for item in account_list:
            # if an actual account ID
            if item.isdigit() and len(item) == 12:
                new_account_list.append(item)
                self.logger.info(new_account_list)
            else:
                name_list.append(item)
                self.logger.info(name_list)
        # check if name list is empty
        if name_list:
            # convert OU Name to OU IDs
            for name in name_list:
                name_account = [value for key, value in
                                name_to_account_map.items()
                                if name.lower() == key.lower()]
                self.logger.info(f"==== name_account: {name_account}")
                self.logger.info("%%%%%%% Name {} -  Account {}"
                                 .format(name, name_account))
                new_account_list.extend(name_account)
        # Remove account ids from the manifest that is not
        # in the organization or not active
        sanitized_account_list = list(
            set(new_account_list).intersection(set(accounts_in_all_ous))
        )
        self.logger.info("Print Updated Manifest Account List")
        self.logger.info(sanitized_account_list)
        # merge account lists manifest account list and
        # accounts under OUs in the manifest
        sanitized_account_list.extend(accounts_in_ou)
        # remove duplicate accounts
        return list(set(sanitized_account_list))

    def get_organization_details(self) -> dict:
        """
        Return:
            dict with following properties:
            accounts_in_all_ous: list. Active accounts
            ou_id_to_account_map: dictionary. Accounts for each OU at the root
                                  level
            ou_name_to_id_map: dictionary. OU Name to OU ID mapping
            name_to_account_map: dictionary. account names in manifest to
                                 account ID mapping
        """

        # Returns 1) OU Name to OU ID mapping (dict)
        # key: OU Name (in the manifest); value: OU ID (at root level)
        # 2) all OU IDs under root (dict)
        org = Organizations(self.logger)
        all_ou_ids, ou_name_to_id_map = self._get_ou_ids(org)

        # Returns 1) active accounts (list) under an OU.
        # use case: used to validate accounts in the manifest file
        # 2) Accounts for each OU at the root level.
        # use case: map OU Name to account IDs
        # key: OU ID (str); value: Active accounts (list)
        accounts_in_all_ous, ou_id_to_account_map = \
            self._get_accounts_in_ou(org, all_ou_ids)

        # Returns account name in manifest to account id mapping.
        # key: account name; value: account id
        name_to_account_map = self.get_account_for_name(org)

        return {
            "AccountsInAllOUs": accounts_in_all_ous,
            "OuIdToAccountMap": ou_id_to_account_map,
            "OuNameToIdMap": ou_name_to_id_map,
            "NameToAccountMap": name_to_account_map
        }

    def _get_ou_ids(self, org):
        """Get list of accounts under each OU
        :param
        org: Organization service client
        return:
        _all_ou_ids: OU IDs of the OUs in the Organization at the root level
        _ou_name_to_id_map: Account name to account id mapping
        """

        # get root id
        root_id = self._get_root_id(org)

        # get OUs under the Org root
        ou_list_at_root_level = self._list_ou_for_parent(org, root_id)

        _ou_name_to_id_map = {}
        _all_ou_ids = []

        for ou_at_root_level in ou_list_at_root_level:
            # build list of all the OU IDs under Org root
            _all_ou_ids.append(ou_at_root_level.get('Id'))
            # build a list of ou id
            _ou_name_to_id_map.update(
                {ou_at_root_level.get('Name'): ou_at_root_level.get('Id')}
            )

        self.logger.info("Print OU Name to OU ID Map")
        self.logger.info(_ou_name_to_id_map)

        return _all_ou_ids, _ou_name_to_id_map

    def _get_root_id(self, org):
        response = org.list_roots()
        self.logger.info("Response: List Roots")
        self.logger.info(response)
        return response['Roots'][0].get('Id')

    def _list_ou_for_parent(self, org, parent_id):
        _ou_list = org.list_organizational_units_for_parent(parent_id)
        self.logger.info("Print Organizational Units List under {}"
                         .format(parent_id))
        self.logger.info(_ou_list)
        return _ou_list

    def _get_accounts_in_ou(self, org, ou_id_list):
        _accounts_in_ou = []
        accounts_in_all_ous = []
        ou_id_to_account_map = {}

        for _ou_id in ou_id_list:
            _account_list = org.list_accounts_for_parent(_ou_id)
            for _account in _account_list:
                # filter ACTIVE and CREATED accounts
                if _account.get('Status') == "ACTIVE":
                    # create a list of accounts in OU
                    accounts_in_all_ous.append(_account.get('Id'))
                    _accounts_in_ou.append(_account.get('Id'))

            # create a map of accounts for each ou
            self.logger.info("Creating Key:Value Mapping - "
                             "OU ID: {} ; Account List: {}"
                             .format(_ou_id, _accounts_in_ou))
            ou_id_to_account_map.update({_ou_id: _accounts_in_ou})
            self.logger.info(ou_id_to_account_map)

            # reset list of accounts in the OU
            _accounts_in_ou = []

        self.logger.info("All accounts in OU List: {}"
                         .format(accounts_in_all_ous))
        self.logger.info("OU to Account ID mapping")
        self.logger.info(ou_id_to_account_map)
        return accounts_in_all_ous, ou_id_to_account_map

    def get_account_for_name(self, org):
        # get all accounts in the organization
        account_list = org.get_accounts_in_org()

        _name_to_account_map = {}
        for account in account_list:
            if account.get("Status") == "ACTIVE":
                _name_to_account_map.update(
                    {account.get("Name"): account.get("Id")}
                )

        self.logger.info("Print Account Name > Account Mapping")
        self.logger.info(_name_to_account_map)

        return _name_to_account_map
