"""An Azure RM Python Pulumi program"""

# import pulumi
# from pulumi_azure_native import storage
# from pulumi_azure_native import resources
from config import AzEnvConfig
from azenv_deploy.azenv_deploy import azureml

# Get configuration from Yaml
config = AzEnvConfig()
azureml.AzureML(f"{config.prefix}azml",
                config.azureml_args)
