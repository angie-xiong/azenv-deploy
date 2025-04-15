"""
This module creates an Azure private endpoint that is used by AzureML.
"""
from dataclasses import dataclass
from typing import Optional, List
from pulumi import Input, ComponentResource, ResourceOptions
from pulumi_azure_native import network

@dataclass
class PrivateEndpointArgs:
    # pylint: disable=too-many-instance-attributes
    """
    A class for configuring a Azure private endpoints.
    """
    resource_group_name: Input[str]
    private_link_service_id: Input[str]
    subnet_id: Input[str]
    dns_resource_group_name: Input[str]
    group_id: Input[str]
    private_dns_zones: List[str]

class PrivateEndpoint(ComponentResource):
    """
    Class that help create Azure private endpoints.
    """
    def __init__(
            self,
            name: str,
            args: PrivateEndpointArgs,
            opts: Optional[ResourceOptions] = None):
        child_opts = ResourceOptions(parent=self)
        super().__init__("azenv_deploy:private_endpoint:PrivateEndpoint", f"{name}-cmp", None, opts)

        private_endpoint = network.PrivateEndpoint(
            name,
            private_link_service_connections=[
                network.PrivateLinkServiceConnectionArgs(
                    group_ids=[args.group_id],
                    name=f"{name}-plsc",
                    private_link_service_id=args.private_link_service_id
                )
            ],
            # This is needed to avoid re-creation of dns groups which later lead to re-creation
            # of private endpoints. By passing empty custom dns configs list we ensure the state
            # is constant with out configurations.
            custom_dns_configs=[],
            resource_group_name=args.resource_group_name,
            subnet=network.SubnetArgs(
                id=args.subnet_id,
            ),
            opts=ResourceOptions.merge(
                child_opts,
                # Recreate the private endpoint when the related parent resource has been updated.
                # pylint: disable=line-too-long
                ResourceOptions(replace_on_changes=["*"], delete_before_replace=True,ignore_changes=["tags"]))
        )

        # The creation of Private DNS Zone Group needs the DNS Zone ID to register the IP of the
        # private endpoint with the DNS Zone.
        private_dns_zone_config_args: List[network.PrivateDnsZoneConfigArgs] = []
        for dns_zone_name in args.private_dns_zones:
            dns_zone = network.get_private_zone_output(
                private_zone_name=dns_zone_name,
                resource_group_name=args.dns_resource_group_name
            )
            private_dns_zone_config_args.append(
                network.PrivateDnsZoneConfigArgs(
                    name=dns_zone_name,
                    private_dns_zone_id=dns_zone.id
                )
            )

        # Extract the parent resource name as the prefix of dns group name.
        dns_group_name_prefix = name.split("-")[0]
        self.dns_group = network.PrivateDnsZoneGroup(
            # Use component name as part of the private dns zone group to avoid name
            # conflicts when we have 2 endpoints for the same group.
            f"{dns_group_name_prefix}-{args.group_id}-dnsgrp",
            private_dns_zone_configs=private_dns_zone_config_args,
            private_endpoint_name=private_endpoint.name,
            resource_group_name=args.resource_group_name,
            opts=ResourceOptions.merge(
                child_opts,
                ResourceOptions(delete_before_replace=True))
        )

        self.private_dns_zone_configs = self.dns_group.private_dns_zone_configs

        self.register_outputs({
            "resource_id": private_endpoint.id,
            "dns_group": self.dns_group,
            "private_dns_zone_group_id": self.dns_group.id,
            "dns_zone_configs": self.private_dns_zone_configs
            })
