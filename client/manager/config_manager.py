import logging
import os
from typing import Dict

import streamlit as st
import yaml


class ConfigManager:
    """
    Manages application configuration loading and access.
    """

    def __init__(self, config_file: str = 'sidebar.yaml'):
        """Initialize configuration manager."""
        self._validate_config_file(config_file)
        self.config_file = config_file
        self.config = self._load_config()

    def _validate_config_file(self, config_file: str) -> None:
        """
        Validate the configuration file name.

        Args:
            config_file (str): Configuration file name to validate

        Raises:
            ValueError: If the file name is invalid
        """
        if not config_file.endswith('.yaml') and not config_file.endswith('.yml'):
            raise ValueError("Configuration file must be a YAML file")

        # Prevent path traversal by rejecting any path-like names
        if os.path.basename(config_file) != config_file:
            raise ValueError("Invalid configuration file name")

    def _load_config(self) -> Dict:
        """
        Load configuration from YAML file.

        Returns:
            Dict: Configuration dictionary
        """
        directory_name = os.path.dirname(__file__)
        config_path = os.path.abspath(os.path.join(
            os.path.dirname(directory_name),
            'config',
            self.config_file
        ))

        # Ensure the path is within the expected directory
        expected_base = os.path.abspath(os.path.join(os.path.dirname(directory_name), 'config'))
        if not config_path.startswith(expected_base):
            logging.error(f"Attempted to access configuration outside allowed directory: {config_path}")
            return {}

        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            st.error(f"Configuration file not found: {config_path}")
            return {}
        except yaml.YAMLError as e:
            st.error(f"Error parsing configuration file: {e}")
            return {}
        except Exception as e:
            logging.error(f"Unexpected error loading configuration: {e}")
            st.error("An unexpected error occurred while loading configuration.")
            return {}
