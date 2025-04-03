"""
"""
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
from pulumi import Input, ComponentResource, ResourceOptions
from pulumi_azure_native import storage

@dataclass
class PrivateDnsZoneAndGroupIdItem:
    """
    A helper class for storing private dns zones and group_ids.

    Storage accounts used by AzureML with private endpoints normally needs 2
    private dns zones("file", "blob") with different group_ids("file", "blob").
    """
    dns_zone: str
    group_id: str

@dataclass
class StorageArgs:
    """
    A class for configuring a Azure Storage account.
    """
    resource_group_name: Input[str]
    private_dns_zones_and_group_ids: List[PrivateDnsZoneAndGroupIdItem]
    logging_workspace_id: Input[str]

    tags: Dict[str, str]
    enable_private_endpoints_access_only: Input[bool] = False
    subnet_id: Input[str] = ''
    dns_resource_group_name: Input[str]= ''
    create_container: Input[bool] = False
    is_hns_enabled: Input[bool] = False
    sku: Input[storage.SkuName] = storage.SkuName.STANDARD_GZRS
    # if false, then override dns_resource_group_name and use the spoke's own DNS zones
    use_spoke_dns_zones: bool = False

class Storage(ComponentResource):
    """
    Class that help create Azure storage accounts.
    """
    def __init__(
            self,
            name: str,
            args: StorageArgs,
            opts: Optional[ResourceOptions] = None):
        super().__init__(
            "azenv_deploy:storage:Storage",
            f"{name}-comp",
            # Register the arguments for the creation of resources in pulumi stack.
            asdict(args),
            opts)
        
