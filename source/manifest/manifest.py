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

import yorm
from yorm.types import String
from yorm.types import List, AttributeDictionary


@yorm.attr(name=String)
@yorm.attr(value=String)
class SSM(AttributeDictionary):
    def __init__(self, name, value):
        super().__init__()
        self.name = name
        self.value = value


@yorm.attr(all=SSM)
class SSMList(List):
    def __init__(self):
        super().__init__()


@yorm.attr(all=String)
class RegionsList(List):
    def __init__(self):
        super().__init__()


@yorm.attr(all=String)
class AccountList(List):
    def __init__(self):
        super().__init__()


@yorm.attr(all=String)
class OUList(List):
    def __init__(self):
        super().__init__()


@yorm.attr(parameter_key=String)
@yorm.attr(parameter_value=String)
class Parameter(AttributeDictionary):
    def __init__(self, key, value):
        super().__init__()
        self.parameter_key = key
        self.parameter_value = value


@yorm.attr(all=Parameter)
class Parameters(List):
    def __init__(self):
        super().__init__()


@yorm.attr(accounts=AccountList)
@yorm.attr(organizational_units=OUList)
class DeployTargets(AttributeDictionary):
    def __init__(self):
        super().__init__()
        self.accounts = []
        self.organizational_units = []


@yorm.attr(all=String)
class ApplyToOUList(List):
    def __init__(self):
        super().__init__()


@yorm.attr(name=String)
@yorm.attr(template_file=String)
@yorm.attr(parameter_file=String)
@yorm.attr(deploy_method=String)
@yorm.attr(ssm_parameters=SSMList)
@yorm.attr(regions=RegionsList)
@yorm.attr(deploy_to_account=AccountList)
@yorm.attr(deploy_to_ou=OUList)
class CfnResource(AttributeDictionary):
    def __init__(self, name, template_file, parameter_file, deploy_method):
        super().__init__()
        self.name = name
        self.template_file = template_file
        self.parameter_file = parameter_file
        self.deploy_method = deploy_method
        self.deploy_to_account = []
        self.deploy_to_ou = []
        self.regions = []
        self.ssm_parameters = []


@yorm.attr(all=CfnResource)
class CfnResourcesList(List):
    def __init__(self):
        super().__init__()


@yorm.attr(name=String)
@yorm.attr(policy_file=String)
@yorm.attr(description=String)
@yorm.attr(apply_to_accounts_in_ou=ApplyToOUList)
class Policy(AttributeDictionary):
    def __init__(self, name, policy_file, description,
                 apply_to_accounts_in_ou):
        super().__init__()
        self.name = name
        self.description = description
        self.policy_file = policy_file
        self.apply_to_accounts_in_ou = apply_to_accounts_in_ou


@yorm.attr(all=Policy)
class PolicyList(List):
    def __init__(self):
        super().__init__()


@yorm.attr(name=String)
@yorm.attr(stackset_name=String)
@yorm.attr(resource_file=String)
@yorm.attr(parameter_file=String)
@yorm.attr(deploy_method=String)
@yorm.attr(export_outputs=SSMList)
@yorm.attr(regions=RegionsList)
@yorm.attr(deployment_targets=DeployTargets)
@yorm.attr(parameters=Parameters)
class ResourceProps(AttributeDictionary):
    def __init__(self, name, resource_file, parameters, parameter_file,
                 deploy_method, deployment_targets, export_outputs, regions,
                 stackset_name=None):
        super().__init__()
        self.name = name
        self.stackset_name = stackset_name
        self.resource_file = resource_file
        self.parameter_file = parameter_file
        self.parameters = parameters
        self.deploy_method = deploy_method
        self.deployment_targets = deployment_targets
        self.regions = regions
        self.export_outputs = export_outputs


@yorm.attr(all=ResourceProps)
class Resources(List):
    def __init__(self):
        super().__init__()


@yorm.attr(region=String)
@yorm.attr(version=String)
@yorm.attr(cloudformation_resources=CfnResourcesList)
@yorm.attr(organization_policies=PolicyList)
@yorm.attr(resources=Resources)
@yorm.sync("{self.manifest_file}", auto_create=False)
class Manifest:
    def __init__(self, manifest_file):
        self.manifest_file = manifest_file
        self.organization_policies = []
        self.cloudformation_resources = []
        self.resources = []
