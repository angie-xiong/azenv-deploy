"""Configuration of the project"""
from dataclasses import dataclass
import pulumi

class AzEnvConfig:
    """Turning the pulumi configuration file into objects."""
    def __init__(self):
        config = pulumi.Config()
        config.require("prefix")
        config.get_bool("enable_private_endpoints")
        self.common = CommonArgs(**config.require_object("common"))
        config.require_object("azureml")

@dataclass
class CommonArgs:
    """Class for storing common arguments from the stack configuration file."""
    dns_resource_group_name: str
    resource_group_name: str
    vnet_resource_group_name: str
    vnet_name: str
    private_endpoint_subnet_name: str
