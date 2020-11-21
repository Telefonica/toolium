# -*- coding: utf-8 -*-
u"""
Copyright 2015 Telefónica Investigación y Desarrollo, S.A.U.
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

import os
import time

import mock
import pytest
import requests_mock
from requests.exceptions import ConnectionError
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from toolium.config_files import ConfigFiles
from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.pageelements.page_element import PageElement
from toolium.utils.driver_utils import Utils

navigation_bar_tests = (
    ('android', 'C:/Demo.apk', None, 0),
    ('android', None, 'chrome', 0),
    ('ios', '/tmp/Demo.zip', None, 0),
    ('ios', None, 'safari', 64),
    ('firefox', None, None, 0),
)

driver_name_tests = (
    ('firefox', 'firefox'),
    ('chrome', 'chrome'),
    ('iexplore-11', 'iexplore'),
    ('iexplore-11-on-WIN10', 'iexplore'),
)


def get_mock_element(x, y, height, width):
    """Create a mock element with custom location and size

    :param x: x location
    :param y: y location
    :param height: element height
    :param width: element width
    :returns: mock element
    """
    mock_element = mock.MagicMock(spec=WebElement)
    mock_element.location = {'x': x, 'y': y}
    mock_element.size = {'height': height, 'width': width}
    return mock_element


@pytest.yield_fixture
def driver_wrapper():
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

    yield driver_wrapper

    # Reset wrappers pool values
    DriverWrappersPool._empty_pool()
    DriverWrapper.config_properties_filenames = None


@pytest.fixture
def utils():
    # Create a new Utils instance
    return Utils()


@pytest.mark.parametrize("driver_type, driver_name", driver_name_tests)
def test_get_driver_name(driver_type, driver_name, driver_wrapper, utils):
    driver_wrapper.config.set('Driver', 'type', driver_type)
    assert utils.get_driver_name() == driver_name


def test_get_available_log_types_one_log_type(driver_wrapper, utils):
    # Configure mock
    log_types_mock = mock.PropertyMock(return_value=['client', 'server'])
    type(driver_wrapper.driver).log_types = log_types_mock

    driver_wrapper.config.set('Server', 'log_types', 'client')

    log_types = utils.get_available_log_types()
    log_types_mock.assert_not_called()
    assert log_types == ['client']


def test_get_available_log_types_multiple_log_types(driver_wrapper, utils):
    # Configure mock
    log_types_mock = mock.PropertyMock(return_value=['client', 'server'])
    type(driver_wrapper.driver).log_types = log_types_mock

    driver_wrapper.config.set('Server', 'log_types', 'client,server,browser')

    log_types = utils.get_available_log_types()
    log_types_mock.assert_not_called()
    assert log_types == ['client', 'server', 'browser']


def test_get_available_log_types_multiple_log_types_with_spaces(driver_wrapper, utils):
    # Configure mock
    log_types_mock = mock.PropertyMock(return_value=['client', 'server'])
    type(driver_wrapper.driver).log_types = log_types_mock

    driver_wrapper.config.set('Server', 'log_types', 'client, server , browser')

    log_types = utils.get_available_log_types()
    log_types_mock.assert_not_called()
    assert log_types == ['client', 'server', 'browser']


def test_get_available_log_types_none_log_type(driver_wrapper, utils):
    # Configure mock
    log_types_mock = mock.PropertyMock(return_value=['client', 'server'])
    type(driver_wrapper.driver).log_types = log_types_mock

    driver_wrapper.config.set('Server', 'log_types', '')

    log_types = utils.get_available_log_types()
    log_types_mock.assert_not_called()
    assert log_types == []


def test_get_available_log_types_all_log_type(driver_wrapper, utils):
    # Configure mock
    log_types_mock = mock.PropertyMock(return_value=['client', 'server'])
    type(driver_wrapper.driver).log_types = log_types_mock

    driver_wrapper.config.set('Server', 'log_types', 'all')

    log_types = utils.get_available_log_types()
    log_types_mock.assert_called_once_with()
    assert log_types == ['client', 'server']


def test_get_available_log_types_without_log_types(driver_wrapper, utils):
    # Configure mock
    log_types_mock = mock.PropertyMock(return_value=['client', 'server'])
    type(driver_wrapper.driver).log_types = log_types_mock

    log_types = utils.get_available_log_types()
    log_types_mock.assert_called_once_with()
    assert log_types == ['client', 'server']


def test_save_webdriver_logs_all_log_type(utils):
    # Configure mock
    Utils.save_webdriver_logs_by_type = mock.MagicMock()
    Utils.get_available_log_types = mock.MagicMock(return_value=['client', 'server'])

    utils.save_webdriver_logs('test_name')
    Utils.save_webdriver_logs_by_type.assert_has_calls([mock.call('client', 'test_name'),
                                                        mock.call('server', 'test_name')])


def test_save_webdriver_logs_without_log_types(utils):
    # Configure mock
    Utils.save_webdriver_logs_by_type = mock.MagicMock()
    Utils.get_available_log_types = mock.MagicMock(return_value=[])

    utils.save_webdriver_logs('test_name')
    Utils.save_webdriver_logs_by_type.assert_not_called()


def test_get_remote_node(driver_wrapper, utils):
    # Configure mock
    driver_wrapper.driver.session_id = '5af'
    url = 'http://{}:{}/grid/api/testsession?session={}'.format('localhost', 4444, '5af')
    grid_response_json = {'session': 'e2', 'proxyId': 'http://10.20.30.40:5555', 'msg': 'slot found !',
                          'inactivityTime': 78, 'success': True, 'internalKey': '7a'}

    with requests_mock.mock() as req_mock:
        req_mock.get(url, json=grid_response_json)

        # Get remote node and check result
        assert utils.get_remote_node() == ('grid', '10.20.30.40')
        assert url == req_mock.request_history[0].url


def test_get_remote_node_selenium3(driver_wrapper, utils):
    # Configure mock
    driver_wrapper.driver.session_id = '5af'
    url = 'http://{}:{}/grid/api/testsession?session={}'.format('localhost', 4444, '5af')
    grid_response_json = {'session': 'e2', 'proxyId': '10.20.30.40', 'msg': 'slot found !',
                          'inactivityTime': 78, 'success': True, 'internalKey': '7a'}

    with requests_mock.mock() as req_mock:
        req_mock.get(url, json=grid_response_json)

        # Get remote node and check result
        assert utils.get_remote_node() == ('grid', '10.20.30.40')
        assert url == req_mock.request_history[0].url


def test_get_remote_node_ggr(driver_wrapper, utils):
    # Configure mock
    driver_wrapper.driver.session_id = '5af'
    grid_url = 'http://{}:{}/grid/api/testsession?session={}'.format('localhost', 4444, '5af')
    ggr_url = 'http://{}:{}/host/{}'.format('localhost', 4444, '5af')
    ggr_response_json = {'Count': 3, 'Username': '', 'Scheme': '', 'VNC': '', 'Name': 'host_name', 'Password': '',
                         'Port': 4500}

    with requests_mock.mock() as req_mock:
        req_mock.get(grid_url, text='non_json_response')
        req_mock.get(ggr_url, json=ggr_response_json)

        # Get remote node and check result
        assert utils.get_remote_node() == ('ggr', 'host_name')
        assert grid_url == req_mock.request_history[0].url
        assert ggr_url == req_mock.request_history[1].url


def test_get_remote_node_selenoid(driver_wrapper, utils):
    # Configure mock
    driver_wrapper.driver.session_id = '5af'
    grid_url = 'http://{}:{}/grid/api/testsession?session={}'.format('localhost', 4444, '5af')
    ggr_url = 'http://{}:{}/host/{}'.format('localhost', 4444, '5af')
    selenoid_url = 'http://{}:{}/status'.format('localhost', 4444)
    selenoid_response_json = {'total': 5, 'used': 0, 'queued': 0, 'pending': 0, 'browsers': {'firefox': {'59.0': {}}}}

    with requests_mock.mock() as req_mock:
        req_mock.get(grid_url, text='non_json_response')
        req_mock.get(ggr_url, json={})
        req_mock.get(selenoid_url, json=selenoid_response_json)

        # Get remote node and check result
        assert utils.get_remote_node() == ('selenoid', 'localhost')
        assert grid_url == req_mock.request_history[0].url
        assert ggr_url == req_mock.request_history[1].url
        assert selenoid_url == req_mock.request_history[2].url


def test_get_remote_node_non_grid(driver_wrapper, utils):
    # Configure mock
    driver_wrapper.driver.session_id = '5af'
    grid_url = 'http://{}:{}/grid/api/testsession?session={}'.format('localhost', 4444, '5af')
    ggr_url = 'http://{}:{}/host/{}'.format('localhost', 4444, '5af')
    selenoid_url = 'http://{}:{}/status'.format('localhost', 4444)

    with requests_mock.mock() as req_mock:
        req_mock.get(grid_url, text='non_json_response')
        req_mock.get(ggr_url, json={})
        req_mock.get(selenoid_url, json={})

        # Get remote node and check result
        assert utils.get_remote_node() == ('selenium', 'localhost')
        assert grid_url == req_mock.request_history[0].url
        assert ggr_url == req_mock.request_history[1].url
        assert selenoid_url == req_mock.request_history[2].url


def test_get_remote_node_local_execution(driver_wrapper, utils):
    driver_wrapper.config.set('Server', 'enabled', 'false')
    assert utils.get_remote_node() == ('local', None)


def test_get_remote_video_url(utils):
    # Configure mock
    url = 'http://{}:{}/video'.format('10.20.30.40', 3000)
    video_url = 'http://{}:{}/download_video/f4.mp4'.format('10.20.30.40', 3000)
    video_response_json = {'exit_code': 1, 'out': [],
                           'error': ['Cannot call this endpoint without required parameters: session and action'],
                           'available_videos': {'5af': {'size': 489701,
                                                        'session': '5af',
                                                        'last_modified': 1460041262558,
                                                        'download_url': video_url,
                                                        'absolute_path': 'C:\\f4.mp4'}},
                           'current_videos': []}

    with requests_mock.mock() as req_mock:
        req_mock.get(url, json=video_response_json)

        # Get remote video url and check result
        assert utils._get_remote_video_url('10.20.30.40', '5af') == video_url
        assert url == req_mock.request_history[0].url


def test_get_remote_video_url_no_videos(utils):
    # Configure mock
    url = 'http://{}:{}/video'.format('10.20.30.40', 3000)
    video_response_json = {'exit_code': 1, 'out': [],
                           'error': ['Cannot call this endpoint without required parameters: session and action'],
                           'available_videos': {},
                           'current_videos': []}

    with requests_mock.mock() as req_mock:
        req_mock.get(url, json=video_response_json)

        # Get remote video url and check result
        assert utils._get_remote_video_url('10.20.30.40', '5af') is None
        assert url == req_mock.request_history[0].url


def test_is_remote_video_enabled(utils):
    # Configure mock
    url = 'http://{}:{}/config'.format('10.20.30.40', 3000)
    config_response_json = {'out': [], 'error': [], 'exit_code': 0,
                            'filename': ['selenium_grid_extras_config.json'],
                            'config_runtime': {'theConfigMap': {
                                'video_recording_options': {'width': '1024', 'videos_to_keep': '5',
                                                            'frames': '30',
                                                            'record_test_videos': 'true'}}}}

    with requests_mock.mock() as req_mock:
        req_mock.get(url, json=config_response_json)

        # Get remote video configuration and check result
        assert utils.is_remote_video_enabled('10.20.30.40') is True
        assert url == req_mock.request_history[0].url


def test_is_remote_video_enabled_disabled(utils):
    # Configure mock
    url = 'http://{}:{}/config'.format('10.20.30.40', 3000)
    config_response_json = {'out': [], 'error': [], 'exit_code': 0,
                            'filename': ['selenium_grid_extras_config.json'],
                            'config_runtime': {'theConfigMap': {
                                'video_recording_options': {'width': '1024', 'videos_to_keep': '5',
                                                            'frames': '30',
                                                            'record_test_videos': 'false'}}}}

    with requests_mock.mock() as req_mock:
        req_mock.get(url, json=config_response_json)

        # Get remote video configuration and check result
        assert utils.is_remote_video_enabled('10.20.30.40') is False
        assert url == req_mock.request_history[0].url


@mock.patch('toolium.utils.driver_utils.requests.get')
def test_is_remote_video_enabled_non_grid_extras(req_get_mock, utils):
    # Configure mock
    req_get_mock.side_effect = ConnectionError('exception error')

    # Get remote video configuration and check result
    assert utils.is_remote_video_enabled('10.20.30.40') is False


@pytest.mark.parametrize("driver_type, appium_app, appium_browser_name, bar_height", navigation_bar_tests)
def test_get_safari_navigation_bar_height(driver_type, appium_app, appium_browser_name, bar_height, driver_wrapper,
                                          utils):
    driver_wrapper.config.set('Driver', 'type', driver_type)
    if appium_app:
        driver_wrapper.config.set('AppiumCapabilities', 'app', appium_app)
    if appium_browser_name:
        driver_wrapper.config.set('AppiumCapabilities', 'browserName', appium_browser_name)
    assert utils.get_safari_navigation_bar_height() == bar_height


def test_get_window_size_android_native(driver_wrapper, utils):
    # Configure driver mock
    window_size = {'width': 375, 'height': 667}
    driver_wrapper.driver.get_window_size.return_value = window_size
    driver_wrapper.config.set('Driver', 'type', 'android')
    driver_wrapper.config.set('AppiumCapabilities', 'app', 'C:/Demo.apk')

    assert utils.get_window_size() == window_size
    driver_wrapper.driver.get_window_size.assert_called_once_with()


def test_get_window_size_android_native_two_times(driver_wrapper, utils):
    # Configure driver mock
    window_size = {'width': 375, 'height': 667}
    driver_wrapper.driver.get_window_size.return_value = window_size
    driver_wrapper.config.set('Driver', 'type', 'android')
    driver_wrapper.config.set('AppiumCapabilities', 'app', 'C:/Demo.apk')

    assert utils.get_window_size() == window_size
    assert utils.get_window_size() == window_size
    # Check that window size is calculated only one time
    driver_wrapper.driver.get_window_size.assert_called_once_with()


def test_get_window_size_android_web(driver_wrapper, utils):
    # Configure driver mock
    window_size = {'width': 375, 'height': 667}
    driver_wrapper.driver.current_context = 'WEBVIEW'
    driver_wrapper.driver.execute_script.side_effect = [window_size['width'], window_size['height']]
    driver_wrapper.config.set('Driver', 'type', 'android')
    driver_wrapper.config.set('AppiumCapabilities', 'browserName', 'chrome')

    assert utils.get_window_size() == window_size
    driver_wrapper.driver.execute_script.assert_has_calls(
        [mock.call('return window.innerWidth'), mock.call('return window.innerHeight')])


def test_get_window_size_android_web_two_times(driver_wrapper, utils):
    # Configure driver mock
    window_size = {'width': 375, 'height': 667}
    driver_wrapper.driver.current_context = 'WEBVIEW'
    driver_wrapper.driver.execute_script.side_effect = [window_size['width'], window_size['height']]
    driver_wrapper.config.set('Driver', 'type', 'android')
    driver_wrapper.config.set('AppiumCapabilities', 'browserName', 'chrome')

    assert utils.get_window_size() == window_size
    assert utils.get_window_size() == window_size
    # Check that window size is calculated only one time
    driver_wrapper.driver.execute_script.assert_has_calls(
        [mock.call('return window.innerWidth'), mock.call('return window.innerHeight')])


def test_get_native_coords_android_web(driver_wrapper, utils):
    # Configure driver mock
    web_window_size = {'width': 500, 'height': 667}
    native_window_size = {'width': 250, 'height': 450}
    driver_wrapper.driver.current_context = 'WEBVIEW'
    driver_wrapper.driver.execute_script.side_effect = [web_window_size['width'], web_window_size['height']]
    driver_wrapper.driver.get_window_size.side_effect = [native_window_size]
    driver_wrapper.config.set('Driver', 'type', 'android')
    driver_wrapper.config.set('AppiumCapabilities', 'browserName', 'chrome')

    web_coords = {'x': 105, 'y': 185}
    native_coords = {'x': 52.5, 'y': 92.5}
    assert utils.get_native_coords(web_coords) == native_coords


def test_get_native_coords_ios_web(driver_wrapper, utils):
    # Configure driver mock
    web_window_size = {'width': 500, 'height': 667}
    native_window_size = {'width': 250, 'height': 450}
    driver_wrapper.driver.get_window_size.side_effect = [web_window_size, native_window_size]
    driver_wrapper.config.set('Driver', 'type', 'ios')
    driver_wrapper.config.set('AppiumCapabilities', 'browserName', 'safari')

    web_coords = {'x': 105, 'y': 185}
    native_coords = {'x': 52.5, 'y': 156.5}
    assert utils.get_native_coords(web_coords) == native_coords


def test_swipe_android_native(driver_wrapper, utils):
    # Configure driver mock
    web_window_size = {'width': 500, 'height': 667}
    native_window_size = {'width': 250, 'height': 450}
    driver_wrapper.driver.get_window_size.side_effect = [web_window_size, native_window_size]
    driver_wrapper.driver.current_context = 'NATIVE_APP'
    driver_wrapper.config.set('Driver', 'type', 'android')
    driver_wrapper.config.set('AppiumCapabilities', 'app', 'C:/Demo.apk')

    # Create element mock
    element = get_mock_element(x=250, y=40, height=40, width=300)

    utils.swipe(element, 50, 100)
    driver_wrapper.driver.swipe.assert_called_once_with(400, 60, 450, 160, None)


def test_swipe_android_web(driver_wrapper, utils):
    # Configure driver mock
    web_window_size = {'width': 500, 'height': 667}
    native_window_size = {'width': 250, 'height': 450}
    driver_wrapper.driver.current_context = 'WEBVIEW'
    driver_wrapper.driver.execute_script.side_effect = [web_window_size['width'], web_window_size['height']]
    driver_wrapper.driver.get_window_size.side_effect = [native_window_size]
    driver_wrapper.config.set('Driver', 'type', 'android')
    driver_wrapper.config.set('AppiumCapabilities', 'browserName', 'chrome')

    # Create element mock
    element = get_mock_element(x=250, y=40, height=40, width=300)

    utils.swipe(element, 50, 100)
    driver_wrapper.driver.swipe.assert_called_once_with(200, 30, 250, 130, None)


def test_swipe_android_hybrid(driver_wrapper, utils):
    # Configure driver mock
    web_window_size = {'width': 500, 'height': 667}
    native_window_size = {'width': 250, 'height': 450}
    # driver_wrapper.utils
    driver_wrapper.driver.get_window_size.side_effect = [web_window_size, native_window_size]
    driver_wrapper.driver.current_context = 'WEBVIEW'
    driver_wrapper.config.set('Driver', 'type', 'android')
    driver_wrapper.config.set('AppiumCapabilities', 'app', 'C:/Demo.apk')

    # Create element mock
    element = get_mock_element(x=250, y=40, height=40, width=300)

    utils.swipe(element, 50, 100)
    driver_wrapper.driver.swipe.assert_called_once_with(200, 30, 250, 130, None)


def test_swipe_ios_web(driver_wrapper, utils):
    # Configure driver mock
    web_window_size = {'width': 500, 'height': 667}
    native_window_size = {'width': 250, 'height': 450}
    driver_wrapper.driver.get_window_size.side_effect = [web_window_size, native_window_size]
    driver_wrapper.config.set('Driver', 'type', 'ios')
    driver_wrapper.config.set('AppiumCapabilities', 'browserName', 'safari')

    # Create element mock
    element = get_mock_element(x=250, y=40, height=40, width=300)

    utils.swipe(element, 50, 100)
    driver_wrapper.driver.swipe.assert_called_once_with(200, 94, 50, 100, None)


def test_swipe_web(driver_wrapper, utils):
    # Configure driver mock
    driver_wrapper.config.set('Driver', 'type', 'firefox')

    # Create element mock
    element = get_mock_element(x=250, y=40, height=40, width=300)

    with pytest.raises(Exception) as excinfo:
        utils.swipe(element, 50, 100)
    assert 'Swipe method is not implemented in Selenium' == str(excinfo.value)


def test_get_web_element_from_web_element(utils):
    element = WebElement(None, 1)
    web_element = utils.get_web_element(element)
    assert element == web_element


def test_get_web_element_from_page_element(driver_wrapper, utils):
    # Mock Driver.save_web_element = True
    driver_wrapper.config = mock.MagicMock()
    driver_wrapper.config.getboolean_optional.return_value = True
    element = PageElement(By.ID, 'element_id')
    element._web_element = 'mock_element'

    web_element = utils.get_web_element(element)
    assert 'mock_element' == web_element


def test_get_web_element_from_locator(driver_wrapper, utils):
    # Configure driver mock
    driver_wrapper.driver.find_element.return_value = 'mock_element'
    element_locator = (By.ID, 'element_id')

    # Get element and assert response
    web_element = utils.get_web_element(element_locator)
    assert 'mock_element' == web_element
    driver_wrapper.driver.find_element.assert_called_once_with(*element_locator)


def test_get_web_element_from_none(utils):
    web_element = utils.get_web_element(None)
    assert web_element is None


def test_get_web_element_from_unknown(utils):
    web_element = utils.get_web_element(dict())
    assert web_element is None


def test_wait_until_first_element_is_found_locator(driver_wrapper, utils):
    # Configure driver mock
    driver_wrapper.driver.find_element.return_value = 'mock_element'
    element_locator = (By.ID, 'element_id')

    element = utils.wait_until_first_element_is_found([element_locator])

    assert element_locator == element
    driver_wrapper.driver.find_element.assert_called_once_with(*element_locator)


@pytest.mark.usefixtures('driver_wrapper')
def test_wait_until_first_element_is_found_page_element(utils):
    # Mock Driver.save_web_element = True
    driver_wrapper.config = mock.MagicMock()
    driver_wrapper.config.getboolean_optional.return_value = True
    page_element = PageElement(By.ID, 'element_id')
    page_element._web_element = 'mock_element'

    element = utils.wait_until_first_element_is_found([page_element])

    assert page_element == element


@pytest.mark.usefixtures('driver_wrapper')
def test_wait_until_first_element_is_found_none(utils):
    # Mock Driver.save_web_element = True
    driver_wrapper.config = mock.MagicMock()
    driver_wrapper.config.getboolean_optional.return_value = True
    page_element = PageElement(By.ID, 'element_id')
    page_element._web_element = 'mock_element'

    element = utils.wait_until_first_element_is_found([None, page_element])

    assert page_element == element


def test_wait_until_first_element_is_found_timeout(driver_wrapper, utils):
    # Configure driver mock
    driver_wrapper.driver.find_element.side_effect = NoSuchElementException('Unknown')
    element_locator = (By.ID, 'element_id')

    start_time = time.time()
    with pytest.raises(TimeoutException) as excinfo:
        utils.wait_until_first_element_is_found([element_locator])
    end_time = time.time()

    assert 'None of the page elements has been found after 10 seconds' in str(excinfo.value)
    # find_element has been called more than one time
    driver_wrapper.driver.find_element.assert_called_with(*element_locator)
    # Execution time must be greater than timeout
    assert end_time - start_time > 10


def test_wait_until_first_element_is_found_custom_timeout(driver_wrapper, utils):
    # Configure driver mock
    driver_wrapper.driver.find_element.side_effect = NoSuchElementException('Unknown')
    element_locator = (By.ID, 'element_id')

    start_time = time.time()
    with pytest.raises(TimeoutException) as excinfo:
        utils.wait_until_first_element_is_found([element_locator], timeout=15)
    end_time = time.time()

    assert 'None of the page elements has been found after 15 seconds' in str(excinfo.value)
    # find_element has been called more than one time
    driver_wrapper.driver.find_element.assert_called_with(*element_locator)
    # Execution time must be greater than timeout
    assert end_time - start_time > 15


def test_utils_compatibility():
    # Check that utils works with old import
    from toolium.utils import Utils
    old_import_utils = Utils()
    assert hasattr(old_import_utils, 'get_web_element')
