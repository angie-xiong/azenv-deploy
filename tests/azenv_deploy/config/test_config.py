"""
Unit test for config.py
"""

import json
from os import environ
from typing import Dict
import pulumi
import pytest
import os
from unittest import mock
import test_util_path
from projects.dev.config import AzEnvConfig
# datasci.config import AIADataSciConfig

@mock.patch.dict(os.environ, {}, clear=True)
def test_parse_config_with_missing_vaues():
    """
    Test parse_config() with missing values.
    """
    with pytest.raises(pulumi.ConfigMissingError):
        AzEnvConfig()

