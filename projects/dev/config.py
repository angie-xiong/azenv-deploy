"""Configuration of the project"""
from dataclasses import dataclass
from typing import Dict, Optional
import re
import pulumi
from azenv_deploy.azenv_deploy import azureml

@dataclass
class CommonArgs:
    """Class for storing common arguments from the stack configuration file."""
    dns_resource_group_name: str
    resource_group_name: str
    vnet_resource_group_name: str
    vnet_name: str
    private_endpoint_subnet_name: str

class AzEnvConfig:
    """Turning the pulumi configuration file into objects."""
    def __init__(self):
        config = pulumi.Config()
        prefix = config.require("prefix")
        validate_prefix(prefix)
        self.common = CommonArgs(**config.require_object("common"))
        enable_private_endpoint = config.get_bool("enable_private_endpoint", True)
        if enable_private_endpoint:
            validate_private_endpoint_config(
                enable_private_endpoint,
                self.common.private_endpoint_subnet_name,
                self.common.dns_resource_group_name)

        azml_yaml_config = azureml.AzureMLYamlConfig(**config.require_object('azureml'))
        self.azureml_args = azureml.AzureMLArgs(
            # Set stack args first
            resource_group_name=self.common.resource_group_name,
            vnet_name=self.common.vnet_name,
            vnet_resource_group_name=self.common.vnet_resource_group_name,
            enable_private_endpoint=enable_private_endpoint,
            private_endpoint_subnet_name=self.common.private_endpoint_subnet_name,
            dns_resource_group_name=self.common.dns_resource_group_name,
            # Allow component args to override
            **azml_yaml_config.model_dump()
        )

def validate_prefix(prefix: str):
    """
    Validate the format of prefix from input parameters.

    Args:
        prefix (str): The prefix string.

    Returns:
        prefix (str): The prefix string.

    Raises:
        (ValueError): The value of prefix should only contain letters and digits, and have
            length between 3 to 9. Otherwise `ValueError` will be thrown.
    """
    pattern = re.compile(r"^(?=.*[a-z])([a-z0-9]{3,9})$")
    if not re.fullmatch(pattern, prefix):
        raise ValueError('Invalid string. The prefix should contain letters and/or digits '
                         'only, and have length between 3 to 9 characters.')
    return prefix

def validate_private_endpoint_config(
    enable_private_endpoints_access_only: bool,
    private_endpoint_subnet_name: Optional[str],
    dns_resource_group_name: Optional[str]
) -> None:
    """
    Validate required parameters for creation of private endpoints.

    Attributes:
    enable_private_endpoints_access_only (bool): Enabling 
        private endpoints for resources or not.
    private_endpoint_subnet_name (Optional[str]): Subnet name.
    dns_resource_group_name (Optional[str]): The resource group name of Private Dns zones.

    Returns:
        None
    """
    if enable_private_endpoints_access_only:
        # pylint: disable=line-too-long
        if private_endpoint_subnet_name is None or private_endpoint_subnet_name.strip() == "" \
            or dns_resource_group_name is None or dns_resource_group_name.strip() == "":
            raise ValueError("`subnet_name` or `dns_resource_group_name` can not be empty.")
