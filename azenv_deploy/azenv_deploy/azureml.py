"""
This module is to deploy Azure Machine Learning service and its related resources,
such as storage accounts, keyvault, private endpoints, etc.
"""
from dataclasses import dataclass, asdict
from typing import Dict, Optional
from pydantic import field_validator, Field, BaseModel
from pulumi import Input, ComponentResource, ResourceOptions
# from pulumi_azure_native import network
from .constants import (
    STANDARD_DS11_V2,
    # PRIVATE_DNS_ZONE_STORAGE_FILE,
    # PRIVATE_DNS_ZONE_STORAGE_BLOB,
    # PRIVATE_DNS_ZONE_STORAGE_DFS
)
# from .storage import PrivateDnsZoneAndGroupIdItem, Storage, StorageArgs


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

class AzureMLYamlConfig(BaseModel):
    """
    Class represents the configuration for AzureML component in the Pulumi YAML config file.
    """
    compute_instance_subnet_name: Optional[str] = None
    compute_cluster_subnet_name: Optional[str] = None
    compute_instance_config: Dict[str, ComputeInstanceItem] = Field(default_factory=dict)
    compute_cluster_config: Dict[str, ComputeClusterItem] = Field(default_factory=dict)

@dataclass
class AzureMLArgs:
    """This class represents the AzureML component configuration in the Pulumi YAML config file"""
    # pylint: disable=too-many-instance-attributes
    resource_group_name: Input[str]
    compute_instance_subnet_name: Optional[Input[str]]
    compute_cluster_subnet_name: Optional[Input[str]]

    # if enable_private_endpoint is `true`, then pe subnet name and dns
    # resource group shouldn't be empty.
    vnet_resource_group_name: Input[str]
    vnet_name: Input[str]
    enable_private_endpoint: Input[bool] = False
    dns_resource_group_name: Input[str] = ""

    private_endpoint_subnet_name: Input[str] = ""

    compute_instance_config: Dict[str, ComputeInstanceItem] = Field(
        default_factory=dict)
    compute_cluster_config: Dict[str, ComputeClusterItem] = Field(
        default_factory=dict)

class AzureML(ComponentResource):
    """Pulumi Component for Azure ML Workspace and associated resources"""
    def __init__(
        self,
        name: str,
        args: AzureMLArgs,
        opts: Optional[ResourceOptions] = None
    ):
        # child_opts = ResourceOptions(parent=self)
        super().__init__("azenv_deploy:azureml:AzureML",
                         f"{name}-comp",
                         # Register the arguments for the creation of resources in pulumi stack.
                         asdict(args),
                         opts)
        # 1. Get the subnet id of the subnet that is used by private endpoints.
        # pe_subnet_id = None
        # if args.private_endpoint_subnet_name:
        #     pe_subnet_id = network.get_subnet_output(
        #         resource_group_name=args.vnet_resource_group_name,
        #         virtual_network_name=args.vnet_name,
        #         subnet_name=args.private_endpoint_subnet_name
        #     ).id

        # 2. Create a Storage Account
        # storage_name = f"{name}stg"
        # private_dns_zones_and_group_ids = None
        # if args.enable_private_endpoint:
        #     private_dns_zones_and_group_ids = [
        #         PrivateDnsZoneAndGroupIdItem(
        #             dns_zone=PRIVATE_DNS_ZONE_STORAGE_FILE,
        #             group_id="file"
        #         ),
        #         PrivateDnsZoneAndGroupIdItem(
        #             dns_zone=PRIVATE_DNS_ZONE_STORAGE_BLOB,
        #             group_id="blob"
        #         ),
        #         PrivateDnsZoneAndGroupIdItem(
        #             dns_zone=PRIVATE_DNS_ZONE_STORAGE_DFS,
        #             group_id="dfs"
        #         )
        #     ]
        # self.storage_account = Storage(
        #     name=storage_name,
        #     args=StorageArgs(
        #         resource_group_name=args.resource_group_name,
        #         enable_private_endpoint=args.enable_private_endpoint,
        #         subnet_id=pe_subnet_id,
        #         dns_resource_group_name=args.dns_resource_group_name,
        #         private_dns_zones_and_group_ids=private_dns_zones_and_group_ids,
        #         logging_workspace_id=args.logging_workspace_id,
        #         tags=[]
        #     ),
        #     opts=child_opts
        # )

        # 3. Create extra DNS record sets to link the endpoints with the
        # private dns zone in Spoke.
        # if args.enable_private_endpoint:
        #     for item in private_dns_zones_and_group_ids:
        #         # pylint: disable=line-too-long
        #         private_ipv4_address = self.storage_account.private_ip_addresses[item.dns_zone]
        #         network.PrivateRecordSet(f"{storage_name}-{item.group_id}-rs",
        #             a_records=[network.ARecordArgs(
        #                 ipv4_address=private_ipv4_address
        #             )],
        #             record_type="A",
        #             relative_record_set_name=self.storage_account.resource_name,
        #             resource_group_name=args.resource_group_name,
        #             ttl=3600,
        #             private_zone_name=item.dns_zone,
        #             opts=ResourceOptions(parent=self, depends_on=[self.storage_account])
        #         )

        # 4. Create a Azure Container Registry
        # 5. Create a Keyvault
        # 6. Create a Application Insights Component
        # 7. Create a Azureml Workspace
        # 8. Create private endpoints for AzureML workspace
        # 9. Create compute clusters
        # 10. Create compute instances
