"""
This module is to deploy Azure Machine Learning service and its related resources,
such as storage accounts, keyvault, private endpoints, etc.
"""
from dataclasses import dataclass, asdict
from typing import Dict, Optional
from pydantic import field_validator, Field, BaseModel
from pulumi import Input, ComponentResource, ResourceOptions
from pulumi_azure_native import network
from .constants import STANDARD_DS11_V2


@dataclass
class AutoPause:
    """
    A class for configuring the auto-pause policy of a Spark cluster
    powered by Synapse workspace.
    """
    enabled: bool = True
    delay_in_minutes: int = 60
    def __getitem__(self, key):
        return getattr(self,key)

@dataclass
class ComputeInstanceItem:
    """
    Class for a Compute Instance config.
    """
    user_email: str
    # NOTE: Using pydantic.Field here rather than dataclasses.field. This is because
    # errors were reported when using dataclasses.field.
    vm_size: str = Field(default=STANDARD_DS11_V2)
    auto_pause: AutoPause = Field(default_factory=AutoPause)

@dataclass
class ComputeClusterItem:
    """
    Class for Compute Cluster Config
    """
    max_node_count: int
    min_node_count: int
    node_idle_time_before_scale_down: str
    vm_priority: str
    vm_size: str

    @field_validator("vm_size")
    @classmethod
    def validate_vm_size_not_empty(cls, value): # pylint: disable=no-self-argument
        """Validate that vm_size is not empty"""
        if not value or value.strip() == "":
            raise ValueError("vm_size in compute cluster can't be empty.")
        return value

    def __getitem__(self, key):
        return getattr(self,key)

@dataclass
class AzureMLArgs:
    """This class represents the AzureML component configuration in the Pulumi YAML config file"""
    # pylint: disable=too-many-instance-attributes
    resource_group_name: Input[str]
    compute_instance_subnet_name: Optional[Input[str]]
    compute_cluster_subnet_name: Optional[Input[str]]

    # if enable_private_endpoints is `true`, then pe subnet name and dns
    # resource group shouldn't be empty.
    vnet_resource_group_name: Input[str]
    vnet_name: Input[str]
    enable_private_endpoints: Input[bool] = False
    dns_resource_group_name: Input[str] = ""

    private_endpoint_subnet_name: Input[str] = ""

    compute_instance_config: Dict[str, ComputeInstanceItem] = Field(
        default_factory=dict)
    compute_cluster_config: Dict[str, ComputeClusterItem] = Field(
        default_factory=dict)

class AzureMLYamlConfig(BaseModel):
    """
    Class represents the configuration for AzureML component in the Pulumi YAML config file.
    """
    compute_instance_subnet_name: Optional[str] = None
    compute_cluster_subnet_name: Optional[str] = None
    data_landing_subnet_name: Optional[str] = None
    compute_instance_config: Dict[str, ComputeInstanceItem] = Field(default_factory=dict)
    compute_cluster_config: Dict[str, ComputeClusterItem] = Field(default_factory=dict)

class AzureML(ComponentResource):
    """Pulumi Component for Azure ML Workspace and associated resources"""
    def __init__(
        self,
        name: str,
        args: AzureMLArgs,
        opts: Optional[ResourceOptions] = None
    ):
        child_opts = ResourceOptions(parent=self)
        super().__init__("azenv_deploy:azureml:AzureML",
                         f"{name}-comp",
                         # Register the arguments for the creation of resources in pulumi stack.
                         asdict(args),
                         opts)
        
        # 1. Get the subnet id of the subnet that is used by private endpoints.
        if args.private_endpoint_subnet_name:
            pe_subnet_id = network.get_subnet_output(
                resource_group_name=args.vnet_resource_group_name,
                virtual_network_name=args.vnet_name,
                subnet_name=args.private_endpoint_subnet_name
            ).id

        # TODO - 2. Create a Storage Account

        # TODO - 3. Create extra DNS record sets to link the endpoints with the
        # private dns zone in Spoke.

        # TODO - 4. Create a Azure Container Registry
        # 5. Create a Keyvault
        # TODO - 6. Create a Application Insights Component
        # TODO - 7. Create a Azureml Workspace
        # TODO - 8. Create private endpoints for AzureML workspace
        # TODO - 9. Create compute clusters
        # TODO - 10. Create compute instances
