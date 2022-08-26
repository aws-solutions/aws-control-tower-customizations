
from typing import List, Dict, Any, TypedDict, Literal


class ResourcePropertiesTypeDef(TypedDict):
    """
    Capabilities is expected to be a json.dumps of CloudFormation capabilities
    """

    StackSetName: str
    TemplateURL: str
    Capabilities: str
    Parameters: Dict[str, Any]
    AccountList: List[str]
    RegionList: List[str]
    SSMParameters: Dict[str, Any]


class StackSetRequestTypeDef(TypedDict):
    RequestType: Literal["Delete", "Create"]
    ResourceProperties: ResourcePropertiesTypeDef
    SkipUpdateStackSet: Literal["no", "yes"]


class StackSetInstanceTypeDef(TypedDict):
    account: str
    region: str