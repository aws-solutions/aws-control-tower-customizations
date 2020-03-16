from abc import ABC, abstractmethod


class StateMachineInput(ABC):
    """
    The State Machine input class that declares a set of methods that returns
    abstract input.
    """
    @abstractmethod
    def input_map(self):
        pass


class InputBuilder(StateMachineInput):
    """
    This class wraps the specific state machine input with
    common required keys.

    """
    def __init__(self, resource_properties, request_type='Create'):
        self._request_type = request_type
        self._resource_properties = resource_properties

    def input_map(self):
        return {
            "RequestType": self._request_type,
            "ResourceProperties": self._resource_properties
        }


class SCPResourceProperties:
    """
    This class helps create and return input needed to execute SCP state
    machine. This also defines the required keys to execute the state machine.

    Example:

    resource_properties = SCPResourceProperties(name, description, policy_url,
                                                policy_list, account_id,
                                                operation, ou_list,
                                                delimiter, scp_parameters)
    scp_input = InputBuilder(resource_properties.get_scp_input_map())
    sm_input = scp_input.input_map()

    """
    def __init__(self, policy_name, policy_description, policy_url, ou_list,
                 policy_list=None, account_id='', operation='',
                 ou_name_delimiter=''):
        self._policy_name = policy_name
        self._policy_description = policy_description
        self._policy_url = policy_url
        self._policy_list = [] if None else policy_list
        self._account_id = account_id
        self._operation = operation
        self._ou_list = ou_list
        self._ou_name_delimiter = ou_name_delimiter

    def get_scp_input_map(self):
        return {
                "PolicyDocument": self._get_policy_document(),
                "AccountId": self._account_id,
                "PolicyList": self._policy_list,
                "Operation": self._operation,
                "OUList": self._ou_list,
                "OUNameDelimiter": self._ou_name_delimiter
        }

    def _get_policy_document(self):
        return {
            "Name": self._policy_name,
            "Description": self._policy_description,
            "PolicyURL": self._policy_url
        }


class StackSetResourceProperties:
    """
        This class helps create and return input needed to execute Stack Set
        state machine. This also defines the required keys to execute the state
        machine.

        Example:

        resource_properties = StackSetResourceProperties(stack_set_name,
                                                     template_url,
                                                     parameters,
                                                     capabilities,
                                                     account_list,
                                                     region_list,
                                                     ssm_parameters)
        ss_input = InputBuilder(resource_properties.get_stack_set_input_map())
        sm_input = ss_input.input_map()
        """
    def __init__(self, stack_set_name, template_url, parameters,
                 capabilities, account_list, region_list, ssm_parameters):
        self._stack_set_name = stack_set_name
        self._template_url = template_url
        self._parameters = parameters
        self._capabilities = capabilities
        self._account_list = account_list
        self._region_list = region_list
        self._ssm_parameters = ssm_parameters

    def get_stack_set_input_map(self):
        return {
            "StackSetName": self._stack_set_name,
            "TemplateURL": self._template_url,
            "Capabilities": self._capabilities,
            "Parameters": self._get_cfn_parameters(),
            "AccountList": self._get_account_list(),
            "RegionList": self._get_region_list(),
            "SSMParameters": self._get_ssm_parameters()
        }

    def _get_cfn_parameters(self):
        if isinstance(self._parameters, dict):
            return self._parameters
        else:
            raise TypeError("Parameters must be of dict type")

    def _get_account_list(self):
        if isinstance(self._account_list, list):
            return self._account_list
        else:
            raise TypeError("Account list value must be of list type")

    def _get_ssm_parameters(self):
        if isinstance(self._ssm_parameters, dict):
            return self._ssm_parameters
        else:
            raise TypeError("SSM Parameter value must be of dict type")

    def _get_region_list(self):
        if isinstance(self._region_list, list):
            return self._region_list
        else:
            raise TypeError("Region list value must be of list type")
