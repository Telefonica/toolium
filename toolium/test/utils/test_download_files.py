# -*- coding: utf-8 -*-
"""
Copyright 2020 Telefónica Investigación y Desarrollo, S.A.U.
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
import mock
import os
import pytest

import toolium
from toolium.config_files import ConfigFiles
from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.utils.download_files import DOWNLOADS_FOLDER, get_download_directory_base, get_downloaded_file_path, \
    retrieve_remote_downloaded_file, get_downloaded_files_list, _get_remote_node_for_download, \
    _get_download_directory_url, delete_remote_downloaded_file, delete_retrieved_downloaded_file, DOWNLOADS_SERVICE_PORT


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


def test_get_downloaded_file_path_server_type_selenoid(context):
    context.driver_wrapper.server_type = 'selenoid'
    toolium.utils.download_files.retrieve_remote_downloaded_file = mock.Mock(return_value='https://path/file_name')

    assert get_downloaded_file_path(context, 'file_name') == 'https://path/file_name'


def test_get_downloaded_file_path_server_type_unknown(context):
    context.driver_wrapper.server_type = 'unknown'
    context.download_directory_base = os.path.sep
    context.download_directory = 'path'

    assert get_downloaded_file_path(context, 'file_name') == os.path.join(os.path.sep, 'path', 'file_name')


def test_retrieve_remote_downloaded_file_download_directory_none(context):
    context.download_directory = None

    assert retrieve_remote_downloaded_file(context, 'file_name') is None


def test_retrieve_remote_downloaded_no_server_section(context):
    context.download_directory = 'donwload_path'
    context.driver_wrapper.config.remove_option('Server', 'enabled')

    assert retrieve_remote_downloaded_file(context, 'file_name') is None


def test_retrieve_remote_downloaded_file_download_directory_and_server_section(context):
    context.download_directory = 'download_path'
    context.driver_wrapper.config.set('Server', 'enabled', 'true')
    toolium.utils.download_files._get_download_directory_url = mock.Mock(return_value='https://host:8001')
    toolium.utils.download_files.makedirs_safe = mock.Mock(return_value=0)
    toolium.utils.download_files.urlretrieve = mock.Mock(return_value=0)

    download_filename = os.path.join(DriverWrappersPool.output_directory, DOWNLOADS_FOLDER,
                                     context.download_directory, 'file_name')
    assert retrieve_remote_downloaded_file(context, 'file_name') == download_filename
    toolium.utils.download_files.urlretrieve.assert_called_once_with('https://host:8001/file_name', download_filename)


def test_get_downloaded_files_list_download_directory_none(context):
    context.download_directory = None
    toolium.utils.download_files.os.listdir = mock.Mock(return_value=['file1.jpg', 'file2.txt'])

    assert get_downloaded_files_list(context) == ['file1.jpg', 'file2.txt']
    toolium.utils.download_files.os.listdir.assert_called_once_with(os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'output', 'downloads'))


def test_get_downloaded_files_list_no_server_section(context):
    context.download_directory = 'download_path'
    context.driver_wrapper.config.remove_option('Server', 'enabled')
    toolium.utils.download_files.os.listdir = mock.Mock(return_value=['file1.jpg', 'file2.txt'])

    assert get_downloaded_files_list(context) == ['file1.jpg', 'file2.txt']
    download_folder = os.path.join(DriverWrappersPool.output_directory, DOWNLOADS_FOLDER, context.download_directory)
    toolium.utils.download_files.os.listdir.assert_called_once_with(download_folder)


def test_get_downloaded_files_list_download_directory_and_server_section(context):
    context.download_directory = "download_path"
    context.driver_wrapper.config.set('Server', 'enabled', 'true')
    toolium.utils.download_files._get_download_directory_url = mock.Mock(return_value='https://host:8001')
    response = mock.Mock()
    response.read.return_value = "html_response"
    toolium.utils.download_files.urlopen = mock.Mock(return_value=response)
    text = mock.Mock()
    text.xpath.return_value = ['file1.jpg', 'file2.txt']
    toolium.utils.download_files.html.fromstring = mock.Mock(return_value=text)

    assert get_downloaded_files_list(context) == ['file1.jpg', 'file2.txt']


def test_get_remote_node_for_download(context):
    context.driver_wrapper.remote_node = "localhost"
    assert _get_remote_node_for_download(context) == "localhost"


def test_get_download_directory_url_download_directory(context):
    context.download_directory = "download_path"
    toolium.utils.download_files._get_remote_node_for_download = mock.Mock(return_value='localhost')

    assert _get_download_directory_url(context) == "http://localhost:{}/download_path".format(DOWNLOADS_SERVICE_PORT)


def test_get_download_directory_url_download_directory_none(context):
    context.download_directory = None
    toolium.utils.download_files._get_remote_node_for_download = mock.Mock(return_value='localhost')

    assert _get_download_directory_url(context) == "http://localhost:{}".format(DOWNLOADS_SERVICE_PORT)


def test_delete_remote_downloaded_file_no_server_section(context):
    context.driver_wrapper.config.remove_option('Server', 'enabled')
    response = mock.Mock()
    response.status_code.return_value = 200
    toolium.utils.download_files.requests.delete = mock.Mock(return_value=response)

    delete_remote_downloaded_file(context, "filename")
    toolium.utils.download_files.requests.delete.assert_not_called()


def test_delete_remote_downloaded_file_server_section(context):
    context.driver_wrapper.config.set('Server', 'enabled', 'true')
    toolium.utils.download_files._get_download_directory_url = mock.Mock(return_value='https://host:8001')
    response_mock = mock.MagicMock()
    type(response_mock).status_code = mock.PropertyMock(return_value=200)
    toolium.utils.download_files.requests.delete = mock.Mock(return_value=response_mock)

    delete_remote_downloaded_file(context, "filename")
    toolium.utils.download_files.requests.delete.assert_called_once_with('https://host:8001/filename')


def test_delete_remote_downloaded_file_server_section_error(context):
    context.driver_wrapper.config.set('Server', 'enabled', 'true')
    toolium.utils.download_files._get_download_directory_url = mock.Mock(return_value='https://host:8001')
    response_mock = mock.MagicMock()
    type(response_mock).status_code = mock.PropertyMock(return_value=404)
    toolium.utils.download_files.requests.delete = mock.Mock(return_value=response_mock)

    with pytest.raises(AssertionError) as exc:
        delete_remote_downloaded_file(context, "filename")
    assert 'ERROR deleting file "https://host:8001/filename":' in str(exc.value)


def test_delete_retrieved_downloaded_file_download_directory_file_dwn(context):
    context.download_directory = "download_path"
    toolium.utils.download_files.os.remove = mock.Mock(return_value=0)
    toolium.utils.download_files.os.rmdir = mock.Mock(return_value=0)

    delete_retrieved_downloaded_file(context, 'file_downloaded', None)
    download_folder = os.path.join(DriverWrappersPool.output_directory, DOWNLOADS_FOLDER, context.download_directory)
    toolium.utils.download_files.os.remove.assert_called_once_with(os.path.join(download_folder, 'file_downloaded'))
    toolium.utils.download_files.os.rmdir.assert_called_once_with(os.path.join(download_folder))


def test_delete_retrieved_downloaded_file_download_directory_file_retr(context):
    context.download_directory = "download_path"
    toolium.utils.download_files.os.remove = mock.Mock(return_value=0)
    toolium.utils.download_files.os.rmdir = mock.Mock(return_value=0)

    delete_retrieved_downloaded_file(context, 'file_downloaded', 'file_retrieved')
    download_folder = os.path.join(DriverWrappersPool.output_directory, DOWNLOADS_FOLDER, context.download_directory)
    toolium.utils.download_files.os.remove.assert_called_once_with(os.path.join(download_folder, 'file_retrieved'))
    toolium.utils.download_files.os.rmdir.assert_called_once_with(os.path.join(download_folder))


def test_delete_retrieved_downloaded_file_download_directory_none(context):
    context.download_directory = ''
    toolium.utils.download_files.os.remove = mock.Mock(return_value=0)
    toolium.utils.download_files.os.rmdir = mock.Mock(return_value=0)

    delete_retrieved_downloaded_file(context, 'file_name', None)
    download_folder = os.path.join(DriverWrappersPool.output_directory, DOWNLOADS_FOLDER, context.download_directory)
    toolium.utils.download_files.os.remove.assert_called_once_with(os.path.join(download_folder, 'file_name'))
    toolium.utils.download_files.os.rmdir.assert_not_called()
