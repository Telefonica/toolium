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

# Python 2.7
from __future__ import division

import logging
import os
import time
from io import open

import requests
from datetime import datetime
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from six.moves.urllib.parse import urlparse  # Python 2 and 3 compatibility

from toolium.utils.path_utils import get_valid_filename, makedirs_safe


class Utils(object):
    _window_size = None  #: dict with window width and height

    def __init__(self, driver_wrapper=None):
        """Initialize Utils instance

        :param driver_wrapper: driver wrapper instance
        """
        from toolium.driver_wrappers_pool import DriverWrappersPool
        self.driver_wrapper = driver_wrapper if driver_wrapper else DriverWrappersPool.get_default_wrapper()
        # Configure logger
        self.logger = logging.getLogger(__name__)

    def get_driver_name(self):
        """
        Get driver name
        :return: driver name
        """
        return self.driver_wrapper.config.get('Driver', 'type').split('-')[0]

    def get_implicitly_wait(self):
        """Read implicitly timeout from configuration properties"""
        return self.driver_wrapper.config.get_optional('Driver', 'implicitly_wait')

    def set_implicitly_wait(self):
        """Read implicitly timeout from configuration properties and configure driver implicitly wait"""
        implicitly_wait = self.get_implicitly_wait()
        if implicitly_wait:
            self.driver_wrapper.driver.implicitly_wait(implicitly_wait)

    def get_explicitly_wait(self):
        """Read explicitly timeout from configuration properties

        :returns: configured explicitly timeout (default timeout 10 seconds)
        """
        return int(self.driver_wrapper.config.get_optional('Driver', 'explicitly_wait', '10'))

    def capture_screenshot(self, name):
        """Capture screenshot and save it in screenshots folder

        :param name: screenshot name suffix
        :returns: screenshot path
        """
        from toolium.driver_wrappers_pool import DriverWrappersPool
        filename = '{0:0=2d}_{1}'.format(DriverWrappersPool.screenshots_number, name)
        filename = '{}.png'.format(get_valid_filename(filename))
        filepath = os.path.join(DriverWrappersPool.screenshots_directory, filename)
        makedirs_safe(DriverWrappersPool.screenshots_directory)
        if self.driver_wrapper.driver.get_screenshot_as_file(filepath):
            self.logger.info('Screenshot saved in %s', filepath)
            DriverWrappersPool.screenshots_number += 1
            return filepath
        return None

    def save_webdriver_logs(self, test_name):
        """Get webdriver logs and write them to log files

        :param test_name: test that has generated these logs
        """
        log_types = self.get_available_log_types()
        self.logger.debug("Reading driver logs of types '%s' and writing them to log files", ', '.join(log_types))
        for log_type in log_types:
            try:
                self.save_webdriver_logs_by_type(log_type, test_name)
            except Exception as exc:
                # Capture exceptions to avoid errors in teardown method
                self.logger.debug("Logs of type '%s' can not be read from driver due to '%s'" % (log_type, str(exc)))

    def get_available_log_types(self):
        """Get log types that are configured in log_types variable or available in current driver

        :returns: log types list
        """
        configured_log_types = self.driver_wrapper.config.get_optional('Server', 'log_types')
        if configured_log_types is None or configured_log_types == 'all':
            if self.driver_wrapper.server_type == 'local':
                log_types = ['browser', 'driver']
            else:
                try:
                    log_types = self.driver_wrapper.driver.log_types
                except Exception as exc:
                    self.logger.debug("Available log types can not be read from driver due to '%s'" % str(exc))
                    log_types = ['client', 'server']
        else:
            log_types = [log_type.strip() for log_type in configured_log_types.split(',') if log_type.strip() != '']
        return log_types

    def save_webdriver_logs_by_type(self, log_type, test_name):
        """Get webdriver logs of the specified type and write them to a log file

        :param log_type: browser, client, driver, performance, server, syslog, crashlog or logcat
        :param test_name: test that has generated these logs
        """
        logs = self.driver_wrapper.driver.get_log(log_type)

        if len(logs) > 0:
            from toolium.driver_wrappers_pool import DriverWrappersPool
            makedirs_safe(DriverWrappersPool.logs_directory)
            log_file_name = '{}_{}.txt'.format(get_valid_filename(test_name), log_type)
            log_file_name = os.path.join(DriverWrappersPool.logs_directory, log_file_name)
            with open(log_file_name, 'a+', encoding='utf-8') as log_file:
                driver_type = self.driver_wrapper.config.get('Driver', 'type')
                log_file.write(
                    u"\n{} '{}' test logs with driver = {}\n\n".format(datetime.now(), test_name, driver_type))
                for entry in logs:
                    timestamp = datetime.fromtimestamp(float(entry['timestamp']) / 1000.).strftime(
                        '%Y-%m-%d %H:%M:%S.%f')
                    log_file.write(u'{}\t{}\t{}\n'.format(timestamp, entry['level'], entry['message'].rstrip()))

    def discard_logcat_logs(self):
        """Discard previous logcat logs"""
        if self.driver_wrapper.is_android_test():
            try:
                self.driver_wrapper.driver.get_log('logcat')
            except Exception:
                pass

    def _expected_condition_find_element(self, element):
        """Tries to find the element, but does not thrown an exception if the element is not found

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :returns: the web element if it has been found or False
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        """
        from toolium.pageelements.page_element import PageElement
        web_element = False
        try:
            if isinstance(element, PageElement):
                # Use _find_web_element() instead of web_element to avoid logging error message
                element._web_element = None
                element._find_web_element()
                web_element = element._web_element
            elif isinstance(element, tuple):
                web_element = self.driver_wrapper.driver.find_element(*element)
        except NoSuchElementException:
            pass
        return web_element

    def _expected_condition_find_element_visible(self, element):
        """Tries to find the element and checks that it is visible, but does not thrown an exception if the element is
            not found

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :returns: the web element if it is visible or False
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        """
        web_element = self._expected_condition_find_element(element)
        try:
            return web_element if web_element and web_element.is_displayed() else False
        except StaleElementReferenceException:
            return False

    def _expected_condition_find_element_not_visible(self, element):
        """Tries to find the element and checks that it is visible, but does not thrown an exception if the element is
            not found

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :returns: True if the web element is not found or it is not visible
        """
        web_element = self._expected_condition_find_element(element)
        try:
            return True if not web_element or not web_element.is_displayed() else False
        except StaleElementReferenceException:
            return False

    def _expected_condition_find_first_element(self, elements):
        """Try to find sequentially the elements of the list and return the first element found

        :param elements: list of PageElements or element locators as a tuple (locator_type, locator_value) to be found
                         sequentially
        :returns: first element found or None
        :rtype: toolium.pageelements.PageElement or tuple
        """
        from toolium.pageelements.page_element import PageElement
        element_found = None
        for element in elements:
            try:
                if isinstance(element, PageElement):
                    element._web_element = None
                    element._find_web_element()
                else:
                    self.driver_wrapper.driver.find_element(*element)
                element_found = element
                break
            except (NoSuchElementException, TypeError):
                pass
        return element_found

    def _expected_condition_find_element_clickable(self, element):
        """Tries to find the element and checks that it is clickable, but does not thrown an exception if the element
            is not found

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :returns: the web element if it is clickable or False
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        """
        web_element = self._expected_condition_find_element_visible(element)
        try:
            return web_element if web_element and web_element.is_enabled() else False
        except StaleElementReferenceException:
            return False

    def _expected_condition_find_element_stopped(self, element_times):
        """Tries to find the element and checks that it has stopped moving, but does not thrown an exception if the element
            is not found

        :param element_times: Tuple with 2 items where:
            [0] element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
            [1] times: number of iterations checking the element's location that must be the same for all of them
            in order to considering the element has stopped
        :returns: the web element if it is clickable or False
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        """
        element, times = element_times
        web_element = self._expected_condition_find_element(element)
        try:
            locations_list = [tuple(web_element.location.values()) for i in range(int(times)) if not time.sleep(0.001)]
            return web_element if set(locations_list) == set(locations_list[-1:]) else False
        except StaleElementReferenceException:
            return False

    def _expected_condition_find_element_containing_text(self, element_text_pair):
        """Tries to find the element and checks that it contains the specified text, but does not thrown an exception if the element is
            not found

        :param element_text_pair: Tuple with 2 items where:
            [0] element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
            [1] text: text to be contained into the element
        :returns: the web element if it contains the text or False
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        """
        element, text = element_text_pair
        web_element = self._expected_condition_find_element(element)
        try:
            return web_element if web_element and text in web_element.text else False
        except StaleElementReferenceException:
            return False

    def _expected_condition_find_element_not_containing_text(self, element_text_pair):
        """Tries to find the element and checks that it does not contain the specified text,
            but does not thrown an exception if the element is found

        :param element_text_pair: Tuple with 2 items where:
            [0] element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
            [1] text: text to not be contained into the element
        :returns: the web element if it does not contain the text or False
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        """
        element, text = element_text_pair
        web_element = self._expected_condition_find_element(element)
        try:
            return web_element if web_element and text not in web_element.text else False
        except StaleElementReferenceException:
            return False

    def _expected_condition_value_in_element_attribute(self, element_attribute_value):
        """Tries to find the element and checks that it contains the requested attribute with the expected value,
           but does not thrown an exception if the element is not found

        :param element_attribute_value: Tuple with 3 items where:
            [0] element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
            [1] attribute: element's attribute where to check its value
            [2] value: expected value for the element's attribute
        :returns: the web element if it contains the expected value for the requested attribute or False
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        """
        element, attribute, value = element_attribute_value
        web_element = self._expected_condition_find_element(element)
        try:
            return web_element if web_element and web_element.get_attribute(attribute) == value else False
        except StaleElementReferenceException:
            return False

    def _wait_until(self, condition_method, condition_input, timeout=None):
        """
        Common method to wait until condition met

        :param condition_method: method to check the condition
        :param condition_input: parameter that will be passed to the condition method
        :param timeout: max time to wait
        :returns: condition method response
        """
        # Remove implicitly wait timeout
        implicitly_wait = self.get_implicitly_wait()
        if implicitly_wait != 0:
            self.driver_wrapper.driver.implicitly_wait(0)
        try:
            # Get explicitly wait timeout
            timeout = timeout if timeout else self.get_explicitly_wait()
            # Wait for condition
            condition_response = WebDriverWait(self.driver_wrapper.driver, timeout).until(
                lambda s: condition_method(condition_input))
        finally:
            # Restore implicitly wait timeout from properties
            if implicitly_wait != 0:
                self.set_implicitly_wait()
        return condition_response

    def wait_until_element_present(self, element, timeout=None):
        """Search element and wait until it is found

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :param timeout: max time to wait
        :returns: the web element if it is present
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        :raises TimeoutException: If the element is not found after the timeout
        """
        return self._wait_until(self._expected_condition_find_element, element, timeout)

    def wait_until_element_visible(self, element, timeout=None):
        """Search element and wait until it is visible

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :param timeout: max time to wait
        :returns: the web element if it is visible
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        :raises TimeoutException: If the element is still not visible after the timeout
        """
        return self._wait_until(self._expected_condition_find_element_visible, element, timeout)

    def wait_until_element_not_visible(self, element, timeout=None):
        """Search element and wait until it is not visible

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :param timeout: max time to wait
        :returns: the web element if it exists but is not visible
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        :raises TimeoutException: If the element is still visible after the timeout
        """
        return self._wait_until(self._expected_condition_find_element_not_visible, element, timeout)

    def wait_until_first_element_is_found(self, elements, timeout=None):
        """Search list of elements and wait until one of them is found

        :param elements: list of PageElements or element locators as a tuple (locator_type, locator_value) to be found
                         sequentially
        :param timeout: max time to wait
        :returns: first element found
        :rtype: toolium.pageelements.PageElement or tuple
        :raises TimeoutException: If no element in the list is found after the timeout
        """
        try:
            return self._wait_until(self._expected_condition_find_first_element, elements, timeout)
        except TimeoutException as exception:
            msg = 'None of the page elements has been found after %s seconds'
            timeout = timeout if timeout else self.get_explicitly_wait()
            self.logger.error(msg, timeout)
            exception.msg += "\n  {}".format(msg % timeout)
            raise exception

    def wait_until_element_clickable(self, element, timeout=None):
        """Search element and wait until it is clickable

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :param timeout: max time to wait
        :returns: the web element if it is clickable
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        :raises TimeoutException: If the element is not clickable after the timeout
        """
        return self._wait_until(self._expected_condition_find_element_clickable, element, timeout)

    def wait_until_element_stops(self, element, times=1000, timeout=None):
        """Search element and wait until it has stopped moving

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :param times: number of iterations checking the element's location that must be the same for all of them
        in order to considering the element has stopped
        :returns: the web element if the element is stopped
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        :raises TimeoutException: If the element does not stop after the timeout
        """
        return self._wait_until(self._expected_condition_find_element_stopped, (element, times), timeout)

    def wait_until_element_contains_text(self, element, text, timeout=None):
        """Search element and wait until it contains the expected text

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :param text: text expected to be contained into the element
        :param timeout: max time to wait
        :returns: the web element if it contains the expected text
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        :raises TimeoutException: If the element does not contain the expected text after the timeout
        """
        return self._wait_until(self._expected_condition_find_element_containing_text, (element, text), timeout)

    def wait_until_element_not_contain_text(self, element, text, timeout=None):
        """Search element and wait until it does not contain the expected text

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :param text: text expected to be contained into the element
        :param timeout: max time to wait
        :returns: the web element if it does not contain the given text
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        :raises TimeoutException: If the element contains the expected text after the timeout
        """
        return self._wait_until(self._expected_condition_find_element_not_containing_text, (element, text), timeout)

    def wait_until_element_attribute_is(self, element, attribute, value, timeout=None):
        """Search element and wait until the requested attribute contains the expected value

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :param attribute: attribute belonging to the element
        :param value: expected value for the attribute of the element
        :param timeout: max time to wait
        :returns: the web element if the element's attribute contains the expected value
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        :raises TimeoutException: If the element's attribute does not contain the expected value after the timeout
        """
        return self._wait_until(self._expected_condition_value_in_element_attribute, (element, attribute, value),
                                timeout)

    def get_remote_node(self):
        """Return the remote node that it's executing the actual test session

        :returns: tuple with server type (local, grid, ggr, selenium) and remote node name
        """
        logging.getLogger("requests").setLevel(logging.WARNING)
        remote_node = None
        server_type = 'local'
        if self.driver_wrapper.config.getboolean_optional('Server', 'enabled'):
            # Request session info from grid hub
            session_id = self.driver_wrapper.driver.session_id
            self.logger.debug("Trying to identify remote node")
            try:
                # Request session info from grid hub and extract remote node
                url = '{}/grid/api/testsession?session={}'.format(self.get_server_url(),
                                                                  session_id)
                proxy_id = requests.get(url).json()['proxyId']
                remote_node = urlparse(proxy_id).hostname if urlparse(proxy_id).hostname else proxy_id
                server_type = 'grid'
                self.logger.debug("Test running in remote node %s", remote_node)
            except (ValueError, KeyError):
                try:
                    # Request session info from GGR and extract remote node
                    from toolium.selenoid import Selenoid
                    remote_node = Selenoid(self.driver_wrapper).get_selenoid_info()['Name']
                    server_type = 'ggr'
                    self.logger.debug("Test running in a GGR remote node %s", remote_node)
                except Exception:
                    try:
                        # The remote node is a Selenoid node
                        url = '{}/status'.format(self.get_server_url())
                        requests.get(url).json()['total']
                        remote_node = self.driver_wrapper.config.get('Server', 'host')
                        server_type = 'selenoid'
                        self.logger.debug("Test running in a Selenoid node %s", remote_node)
                    except Exception:
                        # The remote node is not a grid node or the session has been closed
                        remote_node = self.driver_wrapper.config.get('Server', 'host')
                        server_type = 'selenium'
                        self.logger.debug("Test running in a Selenium node %s", remote_node)

        return server_type, remote_node

    def get_server_url(self):
        """Return the configured server url

        :returns: server url
        """
        server_host = self.driver_wrapper.config.get('Server', 'host')
        server_port = self.driver_wrapper.config.get('Server', 'port')
        server_ssl = 'https' if self.driver_wrapper.config.getboolean_optional('Server', 'ssl') else 'http'
        server_username = self.driver_wrapper.config.get_optional('Server', 'username')
        server_password = self.driver_wrapper.config.get_optional('Server', 'password')
        server_auth = '{}:{}@'.format(server_username, server_password) if server_username and server_password else ''
        server_url = '{}://{}{}:{}'.format(server_ssl, server_auth, server_host, server_port)
        return server_url

    def download_remote_video(self, remote_node, session_id, video_name):
        """Download the video recorded in the remote node during the specified test session and save it in videos folder

        :param remote_node: remote node name
        :param session_id: test session id
        :param video_name: video name
        """
        try:
            video_url = self._get_remote_video_url(remote_node, session_id)
        except requests.exceptions.ConnectionError:
            self.logger.warning("Remote server seems not to have video capabilities")
            return

        if not video_url:
            self.logger.warning("Test video not found in node '%s'", remote_node)
            return

        self._download_video(video_url, video_name)

    def _get_remote_node_url(self, remote_node):
        """Get grid-extras url of a node

        :param remote_node: remote node name
        :returns: grid-extras url
        """
        logging.getLogger("requests").setLevel(logging.WARNING)
        gridextras_port = 3000
        return 'http://{}:{}'.format(remote_node, gridextras_port)

    def _get_remote_video_url(self, remote_node, session_id):
        """Get grid-extras url to download videos

        :param remote_node: remote node name
        :param session_id: test session id
        :returns: grid-extras url to download videos
        """
        url = '{}/video'.format(self._get_remote_node_url(remote_node))
        timeout = time.time() + 5  # 5 seconds from now

        # Requests videos list until timeout or the video url is found
        video_url = None
        while time.time() < timeout:
            response = requests.get(url).json()
            try:
                video_url = response['available_videos'][session_id]['download_url']
                break
            except KeyError:
                time.sleep(1)
        return video_url

    def _download_video(self, video_url, video_name):
        """Download a video from the remote node

        :param video_url: video url
        :param video_name: video name
        """
        from toolium.driver_wrappers_pool import DriverWrappersPool
        filename = '{0:0=2d}_{1}'.format(DriverWrappersPool.videos_number, video_name)
        filename = '{}.mp4'.format(get_valid_filename(filename))
        filepath = os.path.join(DriverWrappersPool.videos_directory, filename)
        makedirs_safe(DriverWrappersPool.videos_directory)
        response = requests.get(video_url)
        open(filepath, 'wb').write(response.content)
        self.logger.info("Video saved in '%s'", filepath)
        DriverWrappersPool.videos_number += 1

    def is_remote_video_enabled(self, remote_node):
        """Check if the remote node has the video recorder enabled

        :param remote_node: remote node name
        :returns: true if it has the video recorder enabled
        """
        enabled = False
        if remote_node:
            url = '{}/config'.format(self._get_remote_node_url(remote_node))
            try:
                response = requests.get(url, timeout=5).json()
                record_videos = response['config_runtime']['theConfigMap']['video_recording_options'][
                    'record_test_videos']
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout, KeyError):
                record_videos = 'false'
            if record_videos == 'true':
                # Wait to the video recorder start
                time.sleep(1)
                enabled = True
        return enabled

    def get_center(self, element):
        """Get center coordinates of an element

        :param element: either a WebElement, PageElement or element locator as a tuple (locator_type, locator_value)
        :returns: dict with center coordinates
        """
        web_element = self.get_web_element(element)
        location = web_element.location
        size = web_element.size
        return {'x': location['x'] + (size['width'] / 2), 'y': location['y'] + (size['height'] / 2)}

    def get_safari_navigation_bar_height(self):
        """Get the height of Safari navigation bar

        :returns: height of navigation bar
        """
        status_bar_height = 0
        if self.driver_wrapper.is_ios_test() and self.driver_wrapper.is_web_test():
            # ios 7.1, 8.3
            status_bar_height = 64
        return status_bar_height

    def get_window_size(self):
        """Generic method to get window size using a javascript workaround for Android web tests

        :returns: dict with window width and height
        """
        if not self._window_size:
            if self.driver_wrapper.is_android_web_test() and self.driver_wrapper.driver.current_context != 'NATIVE_APP':
                window_width = self.driver_wrapper.driver.execute_script("return window.innerWidth")
                window_height = self.driver_wrapper.driver.execute_script("return window.innerHeight")
                self._window_size = {'width': window_width, 'height': window_height}
            else:
                self._window_size = self.driver_wrapper.driver.get_window_size()
        return self._window_size

    def get_native_coords(self, coords):
        """Convert web coords into native coords. Assumes that the initial context is WEBVIEW and switches to
         NATIVE_APP context.

        :param coords: dict with web coords, e.g. {'x': 10, 'y': 10}
        :returns: dict with native coords
        """
        web_window_size = self.get_window_size()
        self.driver_wrapper.driver.switch_to.context('NATIVE_APP')
        native_window_size = self.driver_wrapper.driver.get_window_size()
        scale = native_window_size['width'] / web_window_size['width']
        offset_y = self.get_safari_navigation_bar_height()
        native_coords = {'x': coords['x'] * scale, 'y': coords['y'] * scale + offset_y}
        self.logger.debug('Converted web coords %s into native coords %s', coords, native_coords)
        return native_coords

    def swipe(self, element, x, y, duration=None):
        """Swipe over an element

        :param element: either a WebElement, PageElement or element locator as a tuple (locator_type, locator_value)
        :param x: horizontal movement
        :param y: vertical movement
        :param duration: time to take the swipe, in ms
        """
        if not self.driver_wrapper.is_mobile_test():
            raise Exception('Swipe method is not implemented in Selenium')

        # Get center coordinates of element
        center = self.get_center(element)
        initial_context = self.driver_wrapper.driver.current_context
        if self.driver_wrapper.is_web_test() or initial_context != 'NATIVE_APP':
            center = self.get_native_coords(center)

        # Android needs absolute end coordinates and ios needs movement
        end_x = x if self.driver_wrapper.is_ios_test() else center['x'] + x
        end_y = y if self.driver_wrapper.is_ios_test() else center['y'] + y
        self.driver_wrapper.driver.swipe(center['x'], center['y'], end_x, end_y, duration)

        if self.driver_wrapper.is_web_test() or initial_context != 'NATIVE_APP':
            self.driver_wrapper.driver.switch_to.context(initial_context)

    def get_web_element(self, element):
        """Return the web element from a page element or its locator

        :param element: either a WebElement, PageElement or element locator as a tuple (locator_type, locator_value)
        :returns: WebElement object
        """
        from toolium.pageelements.page_element import PageElement
        if isinstance(element, WebElement):
            web_element = element
        elif isinstance(element, PageElement):
            web_element = element.web_element
        elif isinstance(element, tuple):
            web_element = self.driver_wrapper.driver.find_element(*element)
        else:
            web_element = None
        return web_element

    def get_first_webview_context(self):
        """Return the first WEBVIEW context or raise an exception if it is not found

        :returns: first WEBVIEW context
        """
        for context in self.driver_wrapper.driver.contexts:
            if context.startswith('WEBVIEW'):
                return context
        raise Exception('No WEBVIEW context has been found')

    def switch_to_first_webview_context(self):
        """Switch to the first WEBVIEW context"""
        self.driver_wrapper.driver.switch_to.context(self.get_first_webview_context())

    def focus_element(self, element, click=False):
        """
        Set the focus over the given element.
        :param element: either a WebElement, PageElement or element locator as a tuple (locator_type, locator_value)
        :param click: (bool) If true, click on the element after putting the focus over it.
        """

        action_chain = ActionChains(self.driver_wrapper.driver).move_to_element(self.get_web_element(element))
        action_chain.click().perform() if click else action_chain.perform()
