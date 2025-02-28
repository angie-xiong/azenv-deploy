from dataclasses import dataclass
from typing import Dict, Optional, List, Input, Field
from constants import STANDARD_DS11_V2
from pydantic import field_validator, BaseModel, Field

@dataclass
class AutoPauseConfig:
    """
    A class for configuring the auto-pause policy of a Spark cluster
    powered by Synapse workspace.
    """
    enabled: bool = True
    delay_in_minutes: int = 60
    def __getitem__(self, key):
        return getattr(self,key)

@dataclass
class ComputeInstanceConfigItem:
    user_email: str
    # NOTE: Using pydantic.Field here rather than dataclasses.field. This is because
    # errors were reported when using dataclasses.field.
    vm_size: str = Field(default=STANDARD_DS11_V2)
    auto_pause: AutoPauseConfig = Field(default_factory=AutoPauseConfig)

@dataclass
class ComputeClusterConfigItem:
    # pylint: disable=too-few-public-methods,line-too-long
    """
    Class for Compute Cluster Config

    See https://docs.microsoft.com/en-us/azure/templates/microsoft.machinelearningservices/2021-03-01-preview/workspaces/computes?tabs=bicep#scalesettings
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
class AzureMLConfig:
    compute_instance_subnet_name: Optional[Input[str]]
    compute_cluster_subnet_name: Optional[Input[str]]
    compute_instance_config: Dict[str, ComputeInstanceConfigItem] = Field(
        default_factory=dict)
    compute_cluster_config: Dict[str, ComputeClusterConfigItem] = Field(
        default_factory=dict)