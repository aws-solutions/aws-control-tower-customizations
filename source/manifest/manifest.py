##############################################################################
#  Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.   #
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
class Resource(AttributeDictionary):
    def __init__(self, name, template_file, parameter_file, deploy_method,
                 deploy_to_account, deploy_to_ou):
        super().__init__()
        self.name = name
        self.template_file = template_file
        self.parameter_file = parameter_file
        self.deploy_method = deploy_method
        self.deploy_to_account = []
        self.deploy_to_ou = []
        self.regions = []
        self.ssm_parameters = []


@yorm.attr(all=Resource)
class ResourcesList(List):
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


@yorm.attr(region=String)
@yorm.attr(version=String)
@yorm.attr(cloudformation_resources=ResourcesList)
@yorm.attr(organization_policies=PolicyList)
@yorm.sync("{self.manifest_file}", auto_create=False)
class Manifest:
    def __init__(self, manifest_file):
        self.manifest_file = manifest_file
        self.organization_policies = []
        self.cloudformation_resources = []
