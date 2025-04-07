"""
Unit test for config.py
"""

import json
from os import environ
from typing import Dict
import random
import string
import pulumi
import pytest
import os
from unittest import mock
import test_util_path
from projects.dev.config import AzEnvConfig, validate_prefix, validate_private_endpoint_config

class AzEnvConfigMocks(pulumi.runtime.Mocks):
    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        return [args.name + "_id", args.inputs]

    def call(self, args: pulumi.runtime.MockCallArgs):
        return {}

def mock_pulumi_config_settings(settings: Dict) -> None:
    """
    Mock Pulumi settings.
    """
    pulumi_settings: Dict[str, str] = {}
    for key, val in settings.items():
        pulumi_settings[key] = val
    pulumi_settings_str = json.dumps(pulumi_settings)
    environ["PULUMI_CONFIG"] = pulumi_settings_str

def set_mocks(settings: Dict = None) -> None:
    """
    Set up Pulumi config mocks for testing.
    """
    if settings:
        mock_pulumi_config_settings(settings)
    pulumi.runtime.set_mocks(
        AzEnvConfigMocks(),
        preview=False,
    )

expected_prefix='test'
expected_enable_private_endpoints="True"
expected_common_dns_resource_group_name="test_dns_resource_group_name"
expected_common_resource_group_name="test_resource_group_name"
expected_common_vnet_resource_group_name="test_vnet_resource_group_name="
expected_common_vnet_name="test_vnet_name"
expected_common_private_endpoint_subnet_name="test_private_endpoint_subnet_name"
expected_compute_instance_subnet_name='test_compute_instance_subnet_name'
expected_compute_cluster_subnet_name='test_compute_cluster_subnet_name'

expected_common_dump = json.dumps({
        "dns_resource_group_name": expected_common_dns_resource_group_name,
        "resource_group_name": expected_common_resource_group_name,
        "vnet_resource_group_name": expected_common_vnet_resource_group_name,
        "vnet_name": expected_common_vnet_name,
        "private_endpoint_subnet_name":expected_common_private_endpoint_subnet_name
        })
expected_azureml_cluster_dump = {"comp-cluster-01": {
                "max_node_count": 5,
                "min_node_count": 1,
                "node_idle_time_before_scale_down": "PT5M",
                "vm_priority": "LowPriority",
                "vm_size": "Standard_DS11_v2"
            }}
expected_azureml_instance_dump = {"comp-inst-ax01": {
                "user_email": "test@123.com",
                "vm_size": "Standard_DS12_v2",
                "auto_pause": {
                    "enabled": True,
                    "delay_in_minutes": 20
                }
            }}
expected_azureml_dump = json.dumps({
        "compute_instance_subnet_name": expected_compute_instance_subnet_name,
        "compute_cluster_subnet_name": expected_compute_cluster_subnet_name,
        "compute_cluster_config": expected_azureml_cluster_dump, 
        "compute_instance_config": expected_azureml_instance_dump
        })

"""
This config settings overwrites input parameters.
"""
mock_config_settings = {
    "project:prefix":expected_prefix,
    "project:enable_private_endpoints":expected_enable_private_endpoints,
    "project:common": expected_common_dump,
    "project:azureml": expected_azureml_dump
}

@pulumi.runtime.test
def test_config():
    """
    Test config parameters are set to correct values
    """
    set_mocks(mock_config_settings)
    test_config = AzEnvConfig()
    assert test_config is not None
    assert isinstance(test_config, AzEnvConfig)

    assert test_config.prefix == expected_prefix
    # Parameters for common use
    assert test_config.common.resource_group_name == expected_common_resource_group_name
    assert test_config.common.dns_resource_group_name == expected_common_dns_resource_group_name
    assert test_config.common.private_endpoint_subnet_name == expected_common_private_endpoint_subnet_name
    assert test_config.common.vnet_name == expected_common_vnet_name
    assert test_config.common.vnet_resource_group_name == expected_common_vnet_resource_group_name
    # Parameters for AzureML
    assert test_config.azureml_args.compute_instance_subnet_name == expected_compute_instance_subnet_name
    assert test_config.azureml_args.compute_cluster_subnet_name == expected_compute_cluster_subnet_name
    assert test_config.azureml_args.enable_private_endpoints == True
    assert test_config.azureml_args.compute_cluster_config == expected_azureml_cluster_dump
    assert test_config.azureml_args.compute_instance_config == expected_azureml_instance_dump


@mock.patch.dict(os.environ, {}, clear=True)
def test_parse_config_with_missing_vaues():
    """
    Test parse_config() with missing values.
    """
    with pytest.raises(pulumi.ConfigMissingError):
        AzEnvConfig()

def test_validate_prefix():
    """
    Test when the resource prefix is valid.
    """
    prefix = "dev0111"
    actual_prefix = validate_prefix(prefix)
    assert prefix == actual_prefix

def test_validate_prefix_greater_than_9():
    """
    Test when the length of the resource prefix is less than 2 chars.
    """
    prefix = "a1"
    with pytest.raises(ValueError):
        validate_prefix(prefix)

def test_validate_prefix_greater_than_9():
    """
    Test when the length of the resource prefix is greater than 9 chars.
    """
    prefix = ''.join(random.choice(string.ascii_lowercase) for _ in range(10))
    with pytest.raises(ValueError):
        validate_prefix(prefix)

def test_validate_prefix_with_invalid_chars():
    """
    Test when the resource prefix contains special characters,
    such as a underscore and/or a star.
    """
    prefix = "ax_01*1"
    with pytest.raises(ValueError):
        validate_prefix(prefix)

def test_validate_prefix_with_invalid_uppercase_chars():
    """
    Test when the resource prefix contains uppercase characters.
    """
    prefix = "AX_0111"
    with pytest.raises(ValueError):
        validate_prefix(prefix)

def test_private_endpoint_invalid_config():
    """
    Test when private endpoint enabled, subnet name and hub resource group 
    should't be empty strings or contain whitespaces only. `ValueError`
    should be thrown.
    """
    with pytest.raises(ValueError):
        validate_private_endpoint_config(
            private_endpoint_subnet_name="", 
            enable_private_endpoints=True,
            dns_resource_group_name="foo")
    
    with pytest.raises(ValueError):
        validate_private_endpoint_config(
            private_endpoint_subnet_name="   ", 
            enable_private_endpoints=True,
            dns_resource_group_name="foo")
    
    with pytest.raises(ValueError):
        validate_private_endpoint_config(
            private_endpoint_subnet_name="foo", 
            enable_private_endpoints=True,
            dns_resource_group_name="")

    with pytest.raises(ValueError):
        validate_private_endpoint_config(
            private_endpoint_subnet_name="foo", 
            enable_private_endpoints=True,
            dns_resource_group_name="   ")
