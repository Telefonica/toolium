# -*- coding: utf-8 -*-
"""
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

import logging
import os
import requests
import time
from datetime import datetime
from io import open
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from urllib.parse import urlparse

from toolium.selenoid import Selenoid
from toolium.utils.driver_wait_utils import WaitUtils
from toolium.utils.path_utils import get_valid_filename, makedirs_safe


class Utils(WaitUtils):
    _window_size = None  #: dict with window width and height

    def get_driver_name(self):
        """
        Get driver name
        :return: driver name
        """
        return self.driver_wrapper.config.get('Driver', 'type').split('-')[0]

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
                    "\n{} '{}' test logs with driver = {}\n\n".format(datetime.now(), test_name, driver_type))
                for entry in logs:
                    timestamp = datetime.fromtimestamp(float(entry['timestamp']) / 1000.).strftime(
                        '%Y-%m-%d %H:%M:%S.%f')
                    log_file.write('{}\t{}\t{}\n'.format(timestamp, entry['level'], entry['message'].rstrip()))

    def discard_logcat_logs(self):
        """Discard previous logcat logs"""
        if self.driver_wrapper.is_android_test():
            try:
                self.driver_wrapper.driver.get_log('logcat')
            except Exception:
                pass

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
                url = '{}/grid/api/testsession?session={}'.format(self.get_server_url(), session_id)
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

    def download_remote_video(self, server_type, video_name):
        """Download the video recorded in the remote node and save it in videos folder

        :param server_type: server type (grid, ggr, selenoid)
        :param video_name: video name
        """
        video_name = get_valid_filename(video_name)
        if server_type == 'grid':
            # Download video from Grid Extras
            try:
                video_url = self._get_remote_video_url(self.driver_wrapper.remote_node, self.driver_wrapper.session_id)
            except requests.exceptions.ConnectionError:
                self.logger.warning("Remote server seems not to have video capabilities")
                return

            if not video_url:
                self.logger.warning("Test video not found in node '%s'", self.driver_wrapper.remote_node)
                return

            self._download_video(video_url, video_name)
        elif server_type in ['ggr', 'selenoid']:
            Selenoid(self.driver_wrapper).download_session_video(video_name)

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

    def is_remote_video_enabled(self, server_type, remote_node):
        """Check if the remote node has the video recorder enabled

        :param server_type: server type (grid, ggr, selenoid)
        :param remote_node: remote node name
        :returns: true if it has the video recorder enabled
        """
        enabled = False
        if server_type == 'grid' and remote_node:
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
        elif server_type in ['ggr', 'selenoid']:
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
        """Generic method to get window size using a javascript workaround for mobile web tests

        :returns: dict with window width and height
        """
        if not self._window_size:
            is_mobile_web = self.driver_wrapper.is_android_web_test() or self.driver_wrapper.is_ios_web_test()
            if is_mobile_web and self.driver_wrapper.driver.current_context != 'NATIVE_APP':
                window_width = self.driver_wrapper.driver.execute_script("return window.screen.width")
                window_height = self.driver_wrapper.driver.execute_script("return window.screen.height")
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

    def swipe(self, element, x, y, duration=0):
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
