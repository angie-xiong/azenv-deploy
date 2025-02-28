from dataclasses import dataclass
from typing import Dict, Optional, List, Input, Field
from constants import STANDARD_DS11_V2

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
    # NOTE: I am using pydantic.Field here rather than dataclasses.field. This is because
    # errors were reported when using dataclasses.field.
    #
    # This class is used as a parameter type for parameter compute_instance_config
    # which in Pydantic class AzureMlYamlConfig. It's also used as a parameter type in
    # dataclasses.dataclass AzureMlArgs. It appears that the pydantic class doesn't play well with
    # dataclasses.field
    vm_size: str = Field(default=STANDARD_DS11_V2)
    auto_pause: AutoPauseConfig = Field(default_factory=AutoPauseConfig)

@dataclass
class ComputeClusterConfigItem:
    pass

@dataclass
class AzureMLConfig:
    compute_instance_subnet_name: Optional[Input[str]]
    compute_cluster_subnet_name: Optional[Input[str]]
    compute_instance_config: Dict[str, ComputeInstanceConfigItem] = Field(
        default_factory=dict)
    compute_cluster_config: Dict[str, ComputeClusterConfigItem] = Field(
        default_factory=dict)