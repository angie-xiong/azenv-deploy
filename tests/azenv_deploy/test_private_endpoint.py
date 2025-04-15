"""
Module to test private endpoint component
"""
import pulumi
from typing import List, Set
from pulumi_azure_native import network
# import config.test_util_path
from azenv_deploy.azenv_deploy import private_endpoint

FAKE_RESOURCE_ID="00000000-0000-0000-0000-000000000000"
class FakeDnsZone:
    def __init__(self, id):
        self.id = id

PRIVATE_DNS_ZONE_CONFIGS = [
    {
        "name": "privatelink.xxx.io",
        "privateDnsZoneId": "fake_private_dns_zone_id",
        "recordSets": [
            {
                "fqdn": "xxx.xxx.xxx.xxx.xxx.xxx",
                "ipAddresses": ["0.0.0.0"],
                "recordSetName": "xxx.xxx.xxx"
            }
        ]
    }
]

def get_child_resource_by_type(
    type: object, 
    child_resources: Set[object]
) -> object:
    """
    Fetch child resources by its type.
    """
    for resource in child_resources:
        if isinstance(resource, type):
            return resource
    return None

def get_all_child_resources_by_type(
    type: object, 
    child_resources: Set[object]
) -> List[object]:
    """
    Fetch all child resources having the same type.
    """
    child_list: List[object] = []
    for child in child_resources:
        if isinstance(child, type):
            child_list.append(child)
    return child_list

class PrivateEndpointMocks(pulumi.runtime.Mocks):
    """
    Mocking class for pulumi component: PrivateEndpoint
    """
    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        outputs = args.inputs
        return [args.name + '_id', outputs]
    
    def call(self, args: pulumi.runtime.MockCallArgs):
        match args.token:
            case "azure-native:network:getPrivateZone":            
                return {
                    "id": FAKE_RESOURCE_ID
                }
            case _:
                return {}  

def setup_module():
    """
    Setup mocks to the execution of the module.
    """
    pulumi.runtime.set_mocks(
        PrivateEndpointMocks(),
        # Sets the flag `dry_run`, which is true at runtime during a preview.
        preview=False,
    )

expected_resource_group_name = 'resource_group_name_foo'
expected_private_link_service_id = 'aia_datasci_synapse_stg_id'
expected_subnet_id = 'subnet-id'
expected_dns_resource_group_name = "fake_dns_resource_group_name"
expected_group_id = 'blob'
expected_private_dns_zones = ['privatelink.foo.windows.net']

expected_private_endpoint_name = 'aia_datasci_foo-pe'
private_endpoint_args = private_endpoint.PrivateEndpointArgs(
    resource_group_name = expected_resource_group_name,
    private_link_service_id = expected_private_link_service_id,
    subnet_id = expected_subnet_id,
    dns_resource_group_name=expected_dns_resource_group_name,
    group_id = expected_group_id,
    private_dns_zones = expected_private_dns_zones)
    
@pulumi.runtime.test
def test_on_success():
    """
    Test if PrivateEndpoint is successfully created.
    """
    def check_private_endpoint(args_inside: List[str]):
        urn = args_inside[0]
        # component resource
        assert 'azenv_deploy:private_endpoint:PrivateEndpoint' in urn

    private_endpoint_output = private_endpoint.PrivateEndpoint(expected_private_endpoint_name, args=private_endpoint_args)
    assert private_endpoint_output._name == f"{expected_private_endpoint_name}-cmp" 
    return pulumi.Output.all(private_endpoint_output.urn).apply(check_private_endpoint)
    
def assert_azure_native_network_private_dns_zone_group(
    actual_azure_private_dns_zone_group: network.PrivateDnsZoneGroup,
    expected_name: str
):
    """
    Test properties of network.PrivateDnsZoneGroup resource.
    """
    assert actual_azure_private_dns_zone_group is not None
    assert actual_azure_private_dns_zone_group._name == expected_name

@pulumi.runtime.test
def test_if_private_dns_zone_group_created():
    """
    Test if private dns zone group is successfully created.
    """
    output = private_endpoint.PrivateEndpoint(
        expected_private_endpoint_name, 
        args=private_endpoint_args)

    private_dns_zone_group = get_child_resource_by_type(network.PrivateDnsZoneGroup, output._childResources)
    dns_group_name_prefix = expected_private_endpoint_name.split("-")[0]
    assert_azure_native_network_private_dns_zone_group(
        private_dns_zone_group, 
        f"{dns_group_name_prefix}-{private_endpoint_args.group_id}-dnsgrp")

def test_private_endpoint_args_class():
    """
    Test data class: PrivateEndpointArgs
    """
    private_endpoint_args = private_endpoint.PrivateEndpointArgs(
        resource_group_name = expected_resource_group_name,
        private_link_service_id = expected_private_link_service_id,
        subnet_id = expected_subnet_id,
        dns_resource_group_name = expected_dns_resource_group_name,
        group_id = expected_group_id,
        private_dns_zones = expected_private_dns_zones
    )
    assert private_endpoint_args.resource_group_name == expected_resource_group_name
    assert private_endpoint_args.private_link_service_id == expected_private_link_service_id
    assert private_endpoint_args.subnet_id == expected_subnet_id
    assert private_endpoint_args.dns_resource_group_name == expected_dns_resource_group_name
    assert private_endpoint_args.group_id == expected_group_id
    assert private_endpoint_args.private_dns_zones == expected_private_dns_zones
