import os
import sys
import json
from manifest.manifest import Manifest
from manifest.stage_to_s3 import StageFile
from manifest.sm_input_builder import InputBuilder, SCPResourceProperties, \
    StackSetResourceProperties
from utils.parameter_manipulation import transform_params
from aws.services.s3 import S3
from aws.services.organizations import Organizations
from manifest.cfn_params_handler import CFNParamsHandler


class SCPParser:
    """
    This class parses the Service Control Policies section of the manifest file.
    It converts the yaml (manifest) into JSON input for the SCP state machine.
    :return List of JSON

    Example:
        get_scp_input = SCPParser(logger)
        list_of_inputs = get_scp_input.parse_scp_manifest()
    """
    def __init__(self, logger):
        self.logger = logger
        self.manifest = Manifest(os.environ.get('MANIFEST_FILE_PATH'))

    def parse_scp_manifest(self) -> list:
        self.logger.info(
            "Processing SCPs from {} file".format(
                os.environ.get('MANIFEST_FILE_PATH')))
        state_machine_inputs = []

        for policy in self.manifest.organization_policies:
            # Generate the list of OUs to attach this SCP to
            ou_list = []
            attach_ou_list = set(policy.apply_to_accounts_in_ou)

            for ou in attach_ou_list:
                ou_list.append((ou, 'Attach'))

            local_file = StageFile(self.logger, policy.policy_file)
            policy_url = local_file.stage_file()
            resource_properties = SCPResourceProperties(policy.name,
                                                        policy.description,
                                                        policy_url,
                                                        ou_list)
            scp_input = InputBuilder(resource_properties.get_scp_input_map())
            sm_input = scp_input.input_map()
            self.logger.debug(sm_input)
            state_machine_inputs.append(sm_input)

        # Exit if there are no organization policies
        if len(state_machine_inputs) == 0:
            self.logger.info("Organization policies not found"
                             " in the manifest.")
            sys.exit(0)
        else:
            return state_machine_inputs


class StackSetParser:
    def __init__(self, logger):
        self.logger = logger
        self.s3 = S3(logger)
        self.param_handler = CFNParamsHandler(logger)
        self.manifest = Manifest(os.environ.get('MANIFEST_FILE_PATH'))
        self.manifest_folder = os.environ.get('MANIFEST_FOLDER')

    def parse_stack_set_manifest(self):

        self.logger.info("Parsing Core Resources from {} file"
                         .format(os.environ.get('MANIFEST_FILE_PATH')))

        accounts_in_all_ous, ou_id_to_account_map, ou_name_to_id_map, \
            name_to_account_map = self.get_organization_details()
        state_machine_inputs = []

        for resource in self.manifest.cloudformation_resources:
            self.logger.info(">>>> START : {} >>>>".format(resource.name))
            # Handle scenario if 'deploy_to_ou' key
            # does not exist in the resource
            try:
                self.logger.info(resource.deploy_to_ou)
            except TypeError:
                resource.deploy_to_ou = []

            # Handle scenario if 'deploy_to_account' key
            # does not exist in the resource
            try:
                self.logger.info(resource.deploy_to_account)
            except TypeError:
                resource.deploy_to_account = []

            # find accounts for given ou name
            accounts_in_ou = []

            # check if OU name list is empty
            if resource.deploy_to_ou:
                accounts_in_ou = self.get_accounts_in_ou(ou_id_to_account_map,
                                                         ou_name_to_id_map,
                                                         resource)

            # convert account numbers to string type
            account_list = self._convert_list_values_to_string(
                resource.deploy_to_account)
            self.logger.info(">>>>>> ACCOUNT LIST")
            self.logger.info(account_list)

            sanitized_account_list = self.get_final_account_list(
                account_list, accounts_in_all_ous,
                accounts_in_ou, name_to_account_map)

            self.logger.info("Print merged account list - accounts in manifest"
                             " + account under OU in manifest")
            self.logger.info(sanitized_account_list)

            # Raise exception if account list is empty
            if not sanitized_account_list:
                raise ValueError("The account list must have at least 1 "
                                 "valid account id. Please check the manifest"
                                 " under CloudFormation resource: {}. "
                                 "\n Account List: {} \n OU list: {}"
                                 .format(resource.name,
                                         resource.deploy_to_account,
                                         resource.deploy_to_ou))

            if resource.deploy_method.lower() == 'stack_set':
                sm_input = self._get_state_machine_input(
                    resource, sanitized_account_list)
                state_machine_inputs.append(sm_input)
            else:
                raise Exception("Unsupported deploy_method: {} found for "
                                "resource {} and Account: {} in Manifest"
                                .format(resource.deploy_method,
                                        resource.name,
                                        sanitized_account_list))
            self.logger.info("<<<<<<<<< FINISH : {} <<<<<<<<<"
                             .format(resource.name))

        # Exit if there are no CloudFormation resources
        if len(state_machine_inputs) == 0:
            self.logger.info("CloudFormation resources not found in the "
                             "manifest")
            sys.exit(0)
        else:
            return state_machine_inputs

    def get_accounts_in_ou(self, ou_id_to_account_map, ou_name_to_id_map,
                           resource):
        accounts_in_ou = []
        ou_ids_manifest = []
        # convert OU Name to OU IDs
        for ou_name in resource.deploy_to_ou:
            ou_id = [value for key, value in ou_name_to_id_map.items()
                     if ou_name == key]
            ou_ids_manifest.extend(ou_id)
        # convert OU IDs to accounts
        for ou_id, accounts in ou_id_to_account_map.items():
            if ou_id in ou_ids_manifest:
                accounts_in_ou.extend(accounts)
        self.logger.info(">>> Accounts: {} in OUs: {}"
                         .format(accounts_in_ou, resource.deploy_to_ou))
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
                                if name.lower() in key.lower()]
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

    def get_organization_details(self):
        """Gets organization details including active accounts under an OU,
            account to OU mapping, OU name to OU id mapping, account name to
            account id mapping, etc.
        Args:
            None

        Return:
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

        return accounts_in_all_ous, ou_id_to_account_map, \
            ou_name_to_id_map, name_to_account_map

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

    # return list of strings
    @staticmethod
    def _convert_list_values_to_string(_list):
        return list(map(str, _list))

    def _get_state_machine_input(self, resource, account_list) -> dict:
        local_file = StageFile(self.logger, resource.template_file)
        template_url = local_file.get_staged_file()

        parameters = {}

        # set region variables
        if len(resource.regions) > 0:
            region = resource.regions[0]
            region_list = resource.regions
        else:
            region = self.manifest.region
            region_list = [region]

        # if parameter file link is provided for the CFN resource
        if resource.parameter_file:
            parameters = self._load_params(resource.parameter_file,
                                           account_list,
                                           region)

        ssm_parameters = self._create_ssm_input_map(resource.ssm_parameters)

        # generate state machine input list
        stack_set_name = "CustomControlTower-{}".format(resource.name)
        resource_properties = StackSetResourceProperties(stack_set_name,
                                                         template_url,
                                                         parameters,
                                                         os.environ
                                                         .get('CAPABILITIES'),
                                                         account_list,
                                                         region_list,
                                                         ssm_parameters)
        ss_input = InputBuilder(resource_properties.get_stack_set_input_map())
        return ss_input.input_map()

    def _load_params(self, relative_parameter_path, account=None, region=None):
        if relative_parameter_path.lower().startswith('s3'):
            parameter_file = self.s3.download_remote_file(
                relative_parameter_path
            )
        else:
            parameter_file = os.path.join(self.manifest_folder,
                                          relative_parameter_path)

        self.logger.info("Parsing the parameter file: {}".format(
            parameter_file))

        with open(parameter_file, 'r') as content_file:
            parameter_file_content = content_file.read()

        params = json.loads(parameter_file_content)

        sm_params = self.param_handler.update_params(params, account,
                                                     region, False)

        self.logger.info("Input Parameters for State Machine: {}".format(
            sm_params))
        return sm_params

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
