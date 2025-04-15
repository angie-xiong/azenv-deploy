"""
This module is to deploy Azure Machine Learning service and its related resources,
such as storage accounts, keyvault, private endpoints, etc.
"""
from dataclasses import dataclass, asdict
from typing import Dict, Optional
from pydantic import field_validator, Field, BaseModel
from pulumi import Input, Output, ComponentResource, ResourceOptions
from pulumi_azure_native import (
    network,
    storage,
    containerregistry,
    keyvault,
    authorization,
    insights,
    machinelearning,
    machinelearningservices as mls)
import pulumi_random as random
import pulumi_azuread as azuread
from .constants import (
    LOCATION,
    STANDARD_DS11_V2,
    PRIVATE_DNS_ZONE_STORAGE_FILE,
    PRIVATE_DNS_ZONE_STORAGE_BLOB,
    PRIVATE_DNS_ZONE_STORAGE_DFS,
    PRIVATE_DNS_ZONE_CONTAINER_REGISTRY,
    PRIVATE_DNS_ZONE_KEY_VAULT,
    PRIVATE_DNS_ZONE_AZUREML_NOTEBOOK,
    PRIVATE_DNS_ZONE_AZUREML_API_MS,
    KV_SOFT_DELETE_RETENTION_DAYS,
    RECORDSET_TYPE,
    RECORDSET_TTL
)
from .private_endpoint import PrivateEndpointArgs, PrivateEndpoint

@dataclass
class ComputeInstanceItem:
    """
    Class for a Compute Instance config.
    """
    user_email: str
    vm_size: str = Field(default=STANDARD_DS11_V2)

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

class AzureML(ComponentResource):
    """Pulumi Component for Azure ML Workspace and associated resources"""
    # pylint: disable=too-many-locals
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
        pe_subnet_id = None
        if args.private_endpoint_subnet_name:
            pe_subnet_id = network.get_subnet_output(
                resource_group_name=args.vnet_resource_group_name,
                virtual_network_name=args.vnet_name,
                subnet_name=args.private_endpoint_subnet_name
            ).id

        # 2. Create a Storage Account
        storage_name = f"{name}stg"
        # private_dns_zones_and_group_ids = None
        if args.enable_private_endpoints:
            private_dns_zones_and_group_ids = [
                # Use a Tuple to store the private dns zones and their group ids.
                (PRIVATE_DNS_ZONE_STORAGE_FILE, "file"),
                (PRIVATE_DNS_ZONE_STORAGE_BLOB, "blob"),
                (PRIVATE_DNS_ZONE_STORAGE_DFS, "dfs")]

        network_rule_set_args = None
        if args.enable_private_endpoints:
            network_rule_set_args=storage.NetworkRuleSetArgs(
                bypass=storage.Bypass.AZURE_SERVICES,
                default_action=storage.DefaultAction.DENY
            )
        else:
            network_rule_set_args=storage.NetworkRuleSetArgs(
                bypass=storage.Bypass.AZURE_SERVICES,
                default_action=storage.DefaultAction.ALLOW
            )
        self.storage_account = storage.StorageAccount(
            storage_name,
            location=LOCATION,
            allow_blob_public_access=not args.enable_private_endpoints,
            allow_shared_key_access=True,
            key_policy=storage.KeyPolicyArgs(
                key_expiration_period_in_days=90,
            ),
            kind=storage.Kind.STORAGE_V2,
            minimum_tls_version=storage.MinimumTlsVersion.TLS1_2,
            is_hns_enabled=False,
            access_tier=storage.AccessTier.HOT,
            public_network_access=storage.PublicNetworkAccess.DISABLED \
                if args.enable_private_endpoints else storage.PublicNetworkAccess.ENABLED,
            network_rule_set=network_rule_set_args,
            resource_group_name=args.resource_group_name,
            sku=storage.SkuArgs(name=storage.SkuName.STANDARD_GZRS),
            tags={},
            opts=child_opts
        )

        # 4. Create a Azure Container Registry with private endpoints
        self.container_registry = containerregistry.Registry(
            resource_name=f"{name}acr",
            location=LOCATION,
            resource_group_name=args.resource_group_name,
            sku=containerregistry.SkuArgs(name=containerregistry.SkuName.STANDARD),
            admin_user_enabled=True,
            public_network_access=containerregistry.PublicNetworkAccess.DISABLED \
                if args.enable_private_endpoints \
                    else containerregistry.PublicNetworkAccess.ENABLED,
            opts=child_opts)

        # 5. Create a Keyvault
        self.key_vault = keyvault.Vault(
            name,
            properties=keyvault.VaultPropertiesArgs(
                enable_soft_delete=True,
                enable_purge_protection=True,
                soft_delete_retention_in_days=KV_SOFT_DELETE_RETENTION_DAYS,
                network_acls=keyvault.NetworkRuleSetArgs(
                    bypass=keyvault.NetworkRuleBypassOptions.AZURE_SERVICES,
                    # pylint: disable=line-too-long
                    default_action="DENY") if args.enable_private_endpoints else keyvault.NetworkRuleSetArgs(
                        bypass=keyvault.NetworkRuleBypassOptions.AZURE_SERVICES,
                        default_action="ALLOW"),
                sku=keyvault.SkuArgs(
                    family=keyvault.SkuFamily.A,
                    name=keyvault.SkuName.STANDARD
                ),
                tenant_id=authorization.get_client_config().tenant_id,
                access_policies=[],
                public_network_access=keyvault.PublicNetworkAccess.DISABLED \
                    if args.enable_private_endpoints else keyvault.PublicNetworkAccess.ENABLED
            ),
            resource_group_name=args.resource_group_name,
            tags={},
            opts=child_opts
        )

        # 6. Create a Application Insights
        self.app_insights = insights.Component(
            f"{name}-app-insights",
            opts=child_opts,
            application_type="web",
            kind="web",
            resource_group_name=args.resource_group_name)

        # 7. Create a Azureml Workspace
        self.workspace = machinelearning.Workspace(
            resource_name=f"{name}-ws",
            key_vault_identifier_id=self.key_vault.id,
            location=LOCATION,
            owner_email="angie.xiong0627@gmail.com",
            resource_group_name=args.resource_group_name,
            sku=machinelearning.SkuArgs(
                name="Basic",
                tier="Basic"
            ),
            user_storage_account_id=self.storage_account.id,
            workspace_name=f"{name}-ws",
            opts=child_opts
        )

        # 8. Create compute instances
        tenant_id = authorization.get_client_config().tenant_id
        for compute_name, config in args.compute_instance_config.items():
            mls.Compute(
                resource_name=compute_name,
                resource_group_name=args.resource_group_name,
                location=LOCATION,
                properties=mls.ComputeInstancePropertiesArgs(
                    # pylint: disable=line-too-long
                    compute_instance_authorization_type=mls.ComputeInstanceAuthorizationType.PERSONAL,
                    personal_compute_instance_settings=mls.PersonalComputeInstanceSettingsArgs(
                        assigned_user=mls.AssignedUserArgs(
                                object_id=azuread.get_user(
                                    user_principal_name=config['user_email']).object_id,
                                tenant_id=tenant_id
                            )
                    ),
                    enable_node_public_ip=not args.enable_private_endpoints,
                    subnet=mls.ResourceIdArgs(id=pe_subnet_id),
                    vm_size=config['vm_size']
                ),
                workspace_name=self.workspace.name,
                opts=child_opts
            )

        # 9. Create compute clusters
        for cluster_name, cluster_config in args.compute_cluster_config.items():
            mls.Compute(
                cluster_name,
                opts=child_opts,
                compute_name=Output.format(
                    "{0}-{1}",
                    cluster_name,
                    random.RandomString(
                        f"{cluster_name}-suffix",
                        length=2,
                        upper=False,
                        special=False,
                        opts=child_opts).result
                ),
                identity=mls.ManagedServiceIdentityArgs(
                    type=mls.ManagedServiceIdentityType.SYSTEM_ASSIGNED
                ),
                properties=mls.AmlComputeArgs(
                    compute_type=mls.ComputeType.AML_COMPUTE,
                    disable_local_auth=True,
                    properties=mls.AmlComputePropertiesArgs(
                        enable_node_public_ip=not args.enable_private_endpoints,
                        isolated_network=False,
                        os_type=mls.OsType.LINUX,
                        remote_login_port_public_access=mls.RemoteLoginPortPublicAccess.DISABLED,
                        scale_settings=mls.ScaleSettingsArgs(
                            max_node_count=cluster_config['max_node_count'],
                            min_node_count=cluster_config['min_node_count'],
                            # pylint: disable=line-too-long
                            node_idle_time_before_scale_down=cluster_config['node_idle_time_before_scale_down']
                        ),
                        subnet=mls.ResourceIdArgs(id=pe_subnet_id),
                        vm_priority=mls.VmPriority(cluster_config['vm_priority']),
                        vm_size=cluster_config['vm_size']
                    )
                ),
                resource_group_name=args.resource_group_name,
                workspace_name=self.workspace.name
            )

        # 10. Create private endpoints
        if args.enable_private_endpoints:
            # 10.1. - Create private enddpoints for storage account
            self.private_ip_addresses: Dict[str, str] = {}
            for item in private_dns_zones_and_group_ids:
                endpoint = PrivateEndpoint(
                    name=f"{name}-{item[1]}-pe",
                    args=PrivateEndpointArgs(
                        resource_group_name=args.resource_group_name,
                        private_link_service_id=self.storage_account.id,
                        subnet_id=pe_subnet_id,
                        dns_resource_group_name=args.dns_resource_group_name,
                        group_id=item[1],
                        private_dns_zones=[item[0]]
                    ),
                    opts=child_opts
                )
                # pylint: disable=line-too-long
                self.private_ip_addresses[item[0]] = endpoint.private_dns_zone_configs[0]["record_sets"][0]["ip_addresses"][0]

            # 10.2. Create extra DNS record sets to link the endpoints with the
            # private dns zone in Spoke.
            for item in private_dns_zones_and_group_ids:
                private_ipv4_address = self.private_ip_addresses[item[0]]
                network.PrivateRecordSet(f"{storage_name}-{item[1]}-rs",
                    a_records=[network.ARecordArgs(
                        ipv4_address=private_ipv4_address
                    )],
                    record_type=RECORDSET_TYPE,
                    relative_record_set_name=self.storage_account.name,
                    resource_group_name=args.resource_group_name,
                    ttl=RECORDSET_TTL,
                    private_zone_name=item[0],
                    opts=ResourceOptions(parent=self, depends_on=[self.storage_account])
                )
            # 10.3. Create a private endpoint for container registry
            PrivateEndpoint(
                name=f"{name}-acr-pe",
                args=PrivateEndpointArgs(
                    resource_group_name=args.resource_group_name,
                    private_link_service_id=self.container_registry.id,
                    subnet_id=pe_subnet_id,
                    dns_resource_group_name=args.dns_resource_group_name,
                    group_id="registry",
                    private_dns_zones=[PRIVATE_DNS_ZONE_CONTAINER_REGISTRY]
                    ),
                opts=child_opts
            )
            # 10.4. Create a private endpoint for key vault
            PrivateEndpoint(
                name=f"{name}-kv-pe",
                args=PrivateEndpointArgs(
                    resource_group_name=args.resource_group_name,
                    private_link_service_id=self.key_vault.id,
                    subnet_id=pe_subnet_id,
                    dns_resource_group_name=args.dns_resource_group_name,
                    group_id="vault",
                    private_dns_zones=[PRIVATE_DNS_ZONE_KEY_VAULT]
                    ),
                opts=child_opts
            )
            # 10.5. Create private endpoints for AzureML
            PrivateEndpoint(
                name=f"{name}-ws-pe",
                args=PrivateEndpointArgs(
                    resource_group_name=args.resource_group_name,
                    private_link_service_id=self.workspace.id,
                    subnet_id=pe_subnet_id,
                    dns_resource_group_name=args.dns_resource_group_name,
                    group_id="amlworkspace",
                    private_dns_zones=[
                        PRIVATE_DNS_ZONE_AZUREML_NOTEBOOK,
                        PRIVATE_DNS_ZONE_AZUREML_API_MS
                        ]
                    ),
                opts=child_opts
            )
