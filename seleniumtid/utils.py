# -*- coding: utf-8 -*-
'''
(c) Copyright 2014 Telefonica, I+D. Printed in Spain (Europe). All Rights
Reserved.

The copyright to the software program(s) is property of Telefonica I+D.
The program(s) may be used and or copied only with the express written
consent of Telefonica I+D or in accordance with the terms and conditions
stipulated in the agreement/contract under which the program(s) have
been supplied.
'''
import logging
import os
from seleniumtid import selenium_driver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from urlparse import urlparse
import time


class Utils(object):
    def __init__(self, driver):
        self.driver = driver
        # Configure logger
        self.logger = logging.getLogger(__name__)

    def set_implicit_wait(self):
        '''
        Read timeout from configuration properties and set the implicit wait
        '''
        implicitly_wait = selenium_driver.config.get_optional('Common', 'implicitly_wait')
        if (implicitly_wait):
            self.driver.implicitly_wait(implicitly_wait)

    def capture_screenshot(self, name):
        '''
        Capture screenshot and save it in screenshots folder
        '''
        filename = '{0:0=2d}_{1}.png'.format(selenium_driver.screenshots_number, name)
        filepath = os.path.join(selenium_driver.screenshots_path, filename)
        if not os.path.exists(selenium_driver.screenshots_path):
            os.makedirs(selenium_driver.screenshots_path)
        if self.driver.get_screenshot_as_file(filepath):
            self.logger.info("Screenshot saved in " + filepath)
            selenium_driver.screenshots_number += 1

    def print_all_selenium_logs(self):
        '''
        Print all selenium logs
        '''
        map(self.print_selenium_logs, {'browser', 'client', 'driver', 'performance', 'server', 'logcat'})

    def print_selenium_logs(self, log_type):
        '''
        Print selenium logs of the specified type (browser, client, driver, performance, sever, logcat)
        '''
        for entry in self.driver.get_log(log_type):
            message = entry['message'].rstrip().encode('utf-8')
            self.logger.debug('{0} - {1}: {2}'.format(log_type.capitalize(), entry['level'], message))

    def wait_until_element_visible(self, locator, timeout=10):
        '''
        Search element by locator and wait until it is visible
        '''
        WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))

    def wait_until_element_not_visible(self, locator, timeout=10):
        '''
        Search element by locator and wait until it is not visible
        '''
        # Remove implicit wait
        self.driver.implicitly_wait(0)
        # Wait for invisibility
        WebDriverWait(self.driver, timeout).until(EC.invisibility_of_element_located(locator))
        # Restore implicit wait from properties
        self.set_implicit_wait()

    def get_remote_node(self):
        '''
        Return the remote node that it's executing the actual test session
        '''
        logging.getLogger("requests").setLevel(logging.WARNING)
        remote_node = None
        if selenium_driver.config.getboolean_optional('Server', 'enabled'):
            # Request session info from grid hub
            host = selenium_driver.config.get('Server', 'host')
            port = selenium_driver.config.get('Server', 'port')
            session_id = self.driver.session_id
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
        '''
        Return the remote node only if it has video capabilities
        '''
        remote_node = self.get_remote_node()
        if remote_node and self._is_remote_video_enabled(remote_node):
            # Wait to the video recorder start
            time.sleep(1)
            return remote_node
        return None

    def download_remote_video(self, remote_node, session_id, video_name):
        '''
        Download the video recorded in the remote node during the specified test session and save it in videos folder
        '''
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
        logging.getLogger("requests").setLevel(logging.WARNING)
        gridextras_port = 3000
        return 'http://{}:{}'.format(remote_node, gridextras_port)

    def _get_remote_video_url(self, remote_node, session_id):
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
        filename = '{0:0=2d}_{1}.mp4'.format(selenium_driver.videos_number, video_name)
        filepath = os.path.join(selenium_driver.videos_path, filename)
        if not os.path.exists(selenium_driver.videos_path):
            os.makedirs(selenium_driver.videos_path)
        response = requests.get(video_url)
        open(filepath, 'wb').write(response.content)
        self.logger.info("Video saved in '{}'".format(filepath))
        selenium_driver.videos_number += 1

    def _is_remote_video_enabled(self, remote_node):
        '''
        Check if the remote node has the video recorder enabled
        '''
        url = '{}/config'.format(self._get_remote_node_url(remote_node))
        try:
            response = requests.get(url).json()
            record_videos = response['config_runtime']['theConfigMap']['video_recording_options']['record_test_videos']
        except (requests.exceptions.ConnectionError, KeyError):
            record_videos = 'false'
        return True if record_videos == 'true' else False


class classproperty(property):
    '''
    Subclass property to make classmethod properties possible
    '''
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()
