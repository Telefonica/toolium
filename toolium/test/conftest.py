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
import os

import pytest


def pytest_configure(config):  # noqa: ARG001
    """Configure logging for all tests in this directory and subdirectories."""
    # Configure logging to show DEBUG messages and save to file
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(log_formatter)

    # File handler
    log_dir = os.path.join('toolium', 'test', 'output')
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, 'toolium_tests.log')
    file_handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Clear any existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Add our handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Ensure specific toolium loggers use DEBUG level
    logging.getLogger('toolium').setLevel(logging.DEBUG)
    logging.getLogger('toolium.utils.ai_utils.ai_agent').setLevel(logging.DEBUG)


@pytest.fixture(scope='session', autouse=True)
def setup_logging():
    """Session-level fixture to ensure logging is properly configured."""
    # This fixture runs automatically for all tests
    # Additional logging setup can be done here if needed
    yield  # noqa: PT022
    # Cleanup can be done here if needed
