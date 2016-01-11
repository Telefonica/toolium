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

# Python 2 and 3 compatibility
from six.moves.urllib.parse import urlparse

import logging
import os
import time

import requests
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from toolium.driver_wrappers_pool import DriverWrappersPool


class Utils(object):
    def __init__(self, driver_wrapper=None):
        """Initialize Utils instance

        :param driver_wrapper: driver wrapper instance
        """
        self.driver_wrapper = driver_wrapper if driver_wrapper else DriverWrappersPool.get_default_wrapper()
        # Configure logger
        self.logger = logging.getLogger(__name__)

    def set_implicit_wait(self):
        """Read timeout from configuration properties and set the implicit wait"""
        implicitly_wait = self.driver_wrapper.config.get_optional('Common', 'implicitly_wait')
        if implicitly_wait:
            self.driver_wrapper.driver.implicitly_wait(implicitly_wait)

    def capture_screenshot(self, name):
        """Capture screenshot and save it in screenshots folder

        :param name: screenshot name suffix
        """
        filename = '{0:0=2d}_{1}.png'.format(DriverWrappersPool.screenshots_number, name)
        filepath = os.path.join(DriverWrappersPool.screenshots_directory, filename)
        if not os.path.exists(DriverWrappersPool.screenshots_directory):
            os.makedirs(DriverWrappersPool.screenshots_directory)
        if self.driver_wrapper.driver.get_screenshot_as_file(filepath):
            self.logger.info("Screenshot saved in " + filepath)
            DriverWrappersPool.screenshots_number += 1

    def print_all_selenium_logs(self):
        """Print all selenium logs"""
        map(self.print_selenium_logs, {'browser', 'client', 'driver', 'performance', 'server', 'logcat'})

    def print_selenium_logs(self, log_type):
        """Print selenium logs of the specified type

        :param log_type: browser, client, driver, performance, sever or logcat
        """
        for entry in self.driver_wrapper.driver.get_log(log_type):
            message = entry['message'].rstrip().encode('utf-8')
            self.logger.debug('{0} - {1}: {2}'.format(log_type.capitalize(), entry['level'], message))

    def wait_until_element_visible(self, locator, timeout=10):
        """Search element by locator and wait until it is visible

        :param locator: locator element
        :param timeout: max time to wait
        :returns: the element if it is visible or False
        :rtype: selenium.webdriver.remote.webelement.WebElement
        """
        return WebDriverWait(self.driver_wrapper.driver, timeout).until(EC.visibility_of_element_located(locator))

    def wait_until_element_not_visible(self, locator, timeout=10):
        """Search element by locator and wait until it is not visible

        :param locator: locator element
        :param timeout: max time to wait
        :returns: the element if it is not visible or False
        :rtype: selenium.webdriver.remote.webelement.WebElement
        """
        # Remove implicit wait
        self.driver_wrapper.driver.implicitly_wait(0)
        # Wait for invisibility
        element = WebDriverWait(self.driver_wrapper.driver, timeout).until(EC.invisibility_of_element_located(locator))
        # Restore implicit wait from properties
        self.set_implicit_wait()
        return element

    def get_remote_node(self):
        """Return the remote node that it's executing the actual test session

        :returns: remote node name
        """
        logging.getLogger("requests").setLevel(logging.WARNING)
        remote_node = None
        if self.driver_wrapper.config.getboolean_optional('Server', 'enabled'):
            # Request session info from grid hub
            host = self.driver_wrapper.config.get('Server', 'host')
            port = self.driver_wrapper.config.get('Server', 'port')
            session_id = self.driver_wrapper.driver.session_id
            url = 'http://{}:{}/grid/api/testsession?session={}'.format(host, port, session_id)
            try:
                response = requests.get(url).json()
            except ValueError:
                # The remote node is not a grid node
                return remote_node

            # Extract remote node from response
            remote_node = urlparse(response['proxyId']).hostname
            self.logger.debug("Test running in remote node {}".format(remote_node))
        return remote_node

    def get_remote_video_node(self):
        """Return the remote node only if it has video capabilities

        :returns: remote video node name
        """
        remote_node = self.get_remote_node()
        if remote_node and self._is_remote_video_enabled(remote_node):
            # Wait to the video recorder start
            time.sleep(1)
            return remote_node
        return None

    def download_remote_video(self, remote_node, session_id, video_name):
        """Download the video recorded in the remote node during the specified test session and save it in videos folder

        :param remote_node: remote node name
        :param session_id: test session id
        :param video_name: video name
        """
        try:
            video_url = self._get_remote_video_url(remote_node, session_id)
        except requests.exceptions.ConnectionError:
            self.logger.warn("Remote server seems not to have video capabilities")
            return

        if not video_url:
            self.logger.warn("Test video not found in node '{}'".format(remote_node))
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
        filename = '{0:0=2d}_{1}.mp4'.format(DriverWrappersPool.videos_number, video_name)
        filepath = os.path.join(DriverWrappersPool.videos_directory, filename)
        if not os.path.exists(DriverWrappersPool.videos_directory):
            os.makedirs(DriverWrappersPool.videos_directory)
        response = requests.get(video_url)
        open(filepath, 'wb').write(response.content)
        self.logger.info("Video saved in '{}'".format(filepath))
        DriverWrappersPool.videos_number += 1

    def _is_remote_video_enabled(self, remote_node):
        """Check if the remote node has the video recorder enabled

        :param remote_node: remote node name
        :returns: true if it has the video recorder enabled
        """
        url = '{}/config'.format(self._get_remote_node_url(remote_node))
        try:
            response = requests.get(url).json()
            record_videos = response['config_runtime']['theConfigMap']['video_recording_options']['record_test_videos']
        except (requests.exceptions.ConnectionError, KeyError):
            record_videos = 'false'
        return True if record_videos == 'true' else False

    @staticmethod
    def get_center(element):
        """Get center coordinates of an element

        :param element: webdriver element
        :returns: dict with center coordinates
        """
        return {'x': element.location['x'] + (element.size['width'] / 2),
                'y': element.location['y'] + (element.size['height'] / 2)}

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

        :returns: dict with window size
        """
        if self.driver_wrapper.is_android_web_test() and self.driver_wrapper.driver.current_context != 'NATIVE_APP':
            window_width = self.driver_wrapper.driver.execute_script("return window.innerWidth")
            window_height = self.driver_wrapper.driver.execute_script("return window.innerHeight")
            window_size = {'width': window_width, 'height': window_height}
        else:
            window_size = self.driver_wrapper.driver.get_window_size()
        return window_size

    def get_native_coords(self, coords):
        """Convert web coords into native coords. Assumes that the initial context is WEBVIEW and switches to
         NATIVE_APP context.

        :param coords: dict with web coords, e.g. {'x': 10, 'y': 10}
        :returns: dict with native coords
        """
        web_window_size = self.get_window_size()
        self.driver_wrapper.driver.switch_to.context('NATIVE_APP')
        native_window_size = self.get_window_size()
        scale = native_window_size['width'] / web_window_size['width']
        offset = self.get_safari_navigation_bar_height()
        native_coords = {'x': coords['x'] * scale, 'y': coords['y'] * scale + offset}
        self.logger.debug('Converted web coords {} into native coords {}'.format(coords, native_coords))
        return native_coords

    def swipe(self, element_or_locator, x, y, duration=None):
        """Swipe over an element

        :param element_or_locator: either a WebElement, a PageElement or an element locator as a tuple (locator_type,
                                   locator_value).
        :param x: horizontal movement
        :param y: vertical movement
        :param duration: time to take the swipe, in ms.
        """
        center = self.get_center(self.get_element(element_or_locator))
        if not self.driver_wrapper.is_mobile_test():
            raise Exception('Swipe method is not implemented in Selenium')
        elif self.driver_wrapper.is_web_test() or self.driver_wrapper.driver.current_context != 'NATIVE_APP':
            current_context = self.driver_wrapper.driver.current_context
            center = self.get_native_coords(center)
            self.driver_wrapper.driver.swipe(center['x'], center['y'], center['x'] + x, center['y'] + y, duration)
            self.driver_wrapper.driver.switch_to.context(current_context)
        else:
            self.driver_wrapper.driver.swipe(center['x'], center['y'], center['x'] + x, center['y'] + y, duration)

    def get_element(self, element_or_locator):
        """Return the web element from a page element or its locator

        :param element_or_locator: either a WebElement, a PageElement or an element locator as a tuple (locator_type,
                                   locator_value).
        :returns: WebElement object
        """
        if element_or_locator is None:
            element = None
        elif isinstance(element_or_locator, WebElement):
            element = element_or_locator
        else:
            try:
                # PageElement
                element = element_or_locator.element()
            except AttributeError:
                element = self.driver_wrapper.driver.find_element(*element_or_locator)
        return element


class classproperty(property):
    """Subclass property to make classmethod properties possible"""

    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()
