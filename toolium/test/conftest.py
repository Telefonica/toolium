"""
Copyright 2026 Telefónica Innovación Digital, S.L.
This file is part of Toolium.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging
import logging.config
import os

import pytest


def pytest_configure(config):  # noqa: ARG001
    """Configure logging for all tests in this directory and subdirectories."""
    # Configure the log filename (use forward slashes for cross-platform compatibility)
    log_filename = 'toolium/test/output/toolium_tests.log'

    # Ensure log directory exists before loading logging config
    log_dir = os.path.dirname(log_filename)
    os.makedirs(log_dir, exist_ok=True)

    # Load logging configuration from .conf file with custom logfilename
    config_file = os.path.join('toolium', 'test', 'conf', 'logging.conf')
    logging.config.fileConfig(config_file, defaults={'logfilename': log_filename}, disable_existing_loggers=False)


@pytest.fixture(scope='session', autouse=True)
def setup_logging():
    """
    Session-level fixture to ensure logging is properly configured.
    This fixture is automatically used for all tests in this directory and subdirectories.
    """
    yield  # noqa: PT022
