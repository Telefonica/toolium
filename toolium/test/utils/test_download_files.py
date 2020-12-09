# -*- coding: utf-8 -*-
u"""
Copyright 2018 Telefónica Investigación y Desarrollo, S.A.U.
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
import urllib

import mock
import os
import pytest

import toolium

try:
    from urllib import urlretrieve, urlopen  # Py2
except ImportError:
    from urllib.request import urlretrieve, urlopen  # Py3

from toolium.config_files import ConfigFiles
from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.utils.download_files import DOWNLOADS_FOLDER, get_download_directory_base, get_downloaded_file_path, \
    retrieve_remote_downloaded_file


@pytest.fixture
def context():
    # Create context mock
    context = mock.MagicMock()
    context.download_directory = ""

    # Reset wrappers pool values
    DriverWrappersPool._empty_pool()
    DriverWrapper.config_properties_filenames = None

    # Create a new wrapper
    driver_wrapper = DriverWrappersPool.get_default_wrapper()
    driver_wrapper.driver = mock.MagicMock()

    # Configure properties
    root_path = os.path.dirname(os.path.realpath(__file__))
    config_files = ConfigFiles()
    config_files.set_config_directory(os.path.join(root_path, 'conf'))
    config_files.set_config_properties_filenames('properties.cfg')
    config_files.set_output_directory(os.path.join(root_path, 'output'))
    driver_wrapper.configure(config_files)
    context.driver_wrapper = driver_wrapper

    return context


def test_get_download_directory_base_download_directory_none(context):
    context.download_directory = None

    assert get_download_directory_base(context) is None


def test_get_download_directory_base_no_server_section(context):
    context.download_directory = ""
    context.driver_wrapper.config.remove_option('Server', 'enabled')

    assert get_download_directory_base(context) == os.path.join(DriverWrappersPool.output_directory,
                                                                DOWNLOADS_FOLDER, '')


def test_get_download_directory_base_no_server_section_exception(context):
    context.download_directory = ""
    context.driver_wrapper.config.remove_option('Server', 'enabled')
    DriverWrappersPool.output_directory = os.path.join(os.path.realpath(__file__), 'incorrect_path')

    with pytest.raises(OSError):
        get_download_directory_base(context)


def test_get_download_directory_base_server_disabled(context):
    context.download_directory = ""
    context.driver_wrapper.config.set('Server', 'enabled', 'false')

    assert get_download_directory_base(context) == os.path.join(DriverWrappersPool.output_directory,
                                                                DOWNLOADS_FOLDER, '')


def test_get_download_directory_base_server_enabled_no_driver_section(context):
    context.download_directory = ""
    context.driver_wrapper.config.set('Server', 'enabled', 'true')

    assert get_download_directory_base(context) == "/tmp/%s/" % DOWNLOADS_FOLDER


def test_get_download_directory_base_server_enabled_linux(context):
    context.download_directory = ""
    context.driver_wrapper.config.set('Server', 'enabled', 'true')
    context.driver_wrapper.config.set('Driver', 'type', 'part1-part2-part3-linux')

    assert get_download_directory_base(context) == "/tmp/%s/" % DOWNLOADS_FOLDER


def test_get_download_directory_base_server_enabled_win(context):
    context.download_directory = ""
    context.driver_wrapper.config.set('Server', 'enabled', 'true')
    context.driver_wrapper.config.set('Driver', 'type', 'part1-part2-part3-win')

    assert get_download_directory_base(context) == 'C:\\tmp\\%s\\' % DOWNLOADS_FOLDER


    ##########

def test_get_downloaded_file_path_server_type_selenoid(context):
    context.driver_wrapper.server_type = 'selenoid'
    toolium.utils.download_files.retrieve_remote_downloaded_file = mock.Mock(return_value='https://path/file_name')

    assert get_downloaded_file_path(context, 'file_name') == 'https://path/file_name'


def test_get_downloaded_file_path_server_type_unknown(context):
    context.driver_wrapper.server_type = 'unknown'
    context.download_directory_base = '/'
    context.download_directory = 'path'

    assert get_downloaded_file_path(context, 'file_name') == '/path/file_name'


    ##########


def test_retrieve_remote_downloaded_file_download_directory_none(context):
    context.download_directory = None

    assert retrieve_remote_downloaded_file(context, 'file_name') is None


def test_retrieve_remote_downloaded_file_download_no_server_section(context):
    context.download_directory = 'donwload_path'
    context.driver_wrapper.config.remove_option('Server', 'enabled')

    assert retrieve_remote_downloaded_file(context, 'file_name') is None


def test_retrieve_remote_downloaded_file_download_directory_and_server_section(context):
    context.download_directory = "/downloads"
    context.driver_wrapper.config.set('Server', 'enabled', 'true')
    toolium.utils.download_files._get_download_directory_url = mock.Mock(return_value='https://path')
    toolium.utils.path_utils.makedirs_safe = mock.Mock()
    urllib.request.urlretrieve = mock.Mock()


    assert retrieve_remote_downloaded_file(context, 'file_name') == ''


