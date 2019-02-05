# -*- coding: utf-8 -*-
u"""
Copyright 2019 Telefónica Investigación y Desarrollo, S.A.U.
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
import requests

from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.format_utils import get_valid_filename

# constants
STATUS_OK = 200
DOWNLOADS_PATH = u'downloads'
MP4_EXTENSION = u'mp4'
LOG_EXTENSION = u'log'


class Selenoid(object):
    """
    toolium.cfg properties:
    -----------------------
    [Capabilities]
    # capabilities to selenoid
    selenoid: true           --> MANDATORY
    enableVideo: true        --> MANDATORY
    enableVNC: true          --> MANDATORY


    [Server]
    enabled: true            --> MANDATORY
    host: <hostname or ip>   --> MANDATORY
    port: <numeric>          --> MANDATORY
    username: <string>       --> MANDATORY
    password: <string>       --> MANDATORY
    logs_enabled: true       --> MANDATORY

    Example in environment.py:
       def after_scenario(context, scenario):
            toolium_after_scenario(context, scenario)
            ggr = Selenoid(context, hub=True)
            ggr.download_video_if_the_scenario_fails(scenario)
            ggr.download_session_log()

    Comments:
       the files are always removed in the selenoid server
    """
    def __init__(self, context, hub=True):
        """
        get data from properties file and session
        :param context: It’s a clever place where you and behave can store information to share around, automatically managed by behave.
        :param hub: determine if the server is a node (Selenoid-False) or a hub (GGR-True)
        """
        self.context = context
        self.hub = hub

        self.context.logger.info("Selenoid download is beginning, using GGR as hub: {}...".format(self.hub))
        self.selenoid_flag = context.driver_wrapper.config.getboolean_optional('Capabilities', 'selenoid', False)
        self.browser_remote = context.driver_wrapper.config.getboolean_optional('Server', 'enabled', False)
        self.enabled_logs = context.driver_wrapper.config.getboolean_optional('Server', 'logs_enabled', False)

        if self.selenoid_flag and self.browser_remote:
            try:
                self.session_id = context.driver.session_id
                self.username = context.driver_wrapper.config.get('Server', 'username')
                self.password = context.driver_wrapper.config.get('Server', 'password')
                self.ggr_host = context.driver_wrapper.config.get('Server', 'host')
                self.ggr_port = context.driver_wrapper.config.get('Server', 'port')
            except Exception as e:
                context.logger.warn("verify 'username' and 'password', 'host' and 'port' properties below 'Server' in the toolium.cfg: \n  %s" % e)
            self.context.logger.info("Selenoid host info: \n %s" % self.get_selenoid_info())

    def __download_file(self, url, path_file, timeout):
        """
        download a file from the server using a request with retries policy
        :param url: server url to request
        :param path_file: path and file where to download
        :param timeout: threshold until the video file is downloaded
        :return boolean
        """
        status_code = 0
        init_time = time.time()
        # retries policy
        while status_code != STATUS_OK and time.time() - init_time < float(timeout):
            body = requests.get(url)
            status_code = body.status_code
        took = time.time() - init_time    # time used to download the file
        # create the folders and store the file downloaded
        if status_code == STATUS_OK:
            path, name = os.path.split(path_file)
            if not os.path.exists(path):
                os.makedirs(path)
            try:
                fp = open(path_file, 'wb')
                fp.write(body.content)
                fp.close()
                self.context.logger.info('the %s file has been downloaded successfully and took %d seconds' % (path_file, took))
                return True
            except IOError as e:
                self.context.logger.warn('the %s file has a problem; \n %s' % (path_file, e))
        else:
            self.context.logger.warn('the file to download does not exist in the server after %s s (timeout).' % timeout)
        return False

    def __remove_file(self, url):
        """
        remove a file in the Selenoid node
        """
        requests.delete(url)

    def get_selenoid_info(self):
        """
        retrieve the current selenoid host info. Used only in hub mode (GGR)
        request: http://<username>:<password>@<ggr_host>:<ggr_port>/host/<ggr_session_id>
        :return: dict
        """
        if self.hub:
            url = 'http://{0}:{1}@{2}:{3}/host/{4}'.\
                format(self.username, self.password, self.ggr_host, self.ggr_port, self.session_id)
            try:
                response = requests.get(url)
            except Exception as e:
                self.context.logger.warn("the GGR request to get the node host is failed: \n  %s" % e)
                return None
            return response.json()
        return None

    def download_video_if_the_scenario_fails(self, scenario, timeout=10):
        """
        download the execution video file if the scenario fails, renaming the file to scenario name from remote selenoid and
        removing the session file in the server.
             GGR request: http://<username>:<password>@<ggr_host>:<ggr_port>/video/<session_id>
        selenoid request: http://<username>:<password>@<ggr_host>:<ggr_port>/video/<session_id>.mp4
        :param scenario: scenario object to get scenario name
        :param timeout: threshold until the video file is downloaded
        """
        if self.selenoid_flag:
            name = get_valid_filename(scenario.name)
            path_file = os.path.join(DriverWrappersPool.videos_directory, '%s.%s' % (name, MP4_EXTENSION))
            if not self.hub:
                filename = "%s.%s" % (self.session_id, MP4_EXTENSION)
            else:
                filename = self.session_id
            server_url = 'http://{}:{}@{}:{}/video/{}'.\
                format(self.username, self.password, self.ggr_host, self.ggr_port, filename)
            # download the execution video file if the scenario is failed
            if scenario.status == 'failed' and self.browser_remote:
                self.__download_file(server_url, path_file, timeout)
            # remove the video file if it does exist
            self.__remove_file(server_url)

    def download_session_log(self, timeout=10):
        """
        download the session log file from remote selenoid and removing the file in the server.
             GGR request: http://<username>:<password>@<ggr_host>:<ggr_port>/logs/<ggr_session_id>
        selenoid request: http://<username>:<password>@<ggr_host>:<ggr_port>/logs/<ggr_session_id>.log
        :param timeout: threshold until the video file is downloaded
        """
        if self.selenoid_flag:
            path_file = os.path.join(DriverWrappersPool.logs_directory, '%s.%s' % (self.session_id, LOG_EXTENSION))
            if not self.hub:
                filename = "%s.%s" % (self.session_id, LOG_EXTENSION)
            else:
                filename = self.session_id
            server_url = 'http://{}:{}@{}:{}/logs/{}'.\
                format(self.username, self.password, self.ggr_host, self.ggr_port, filename)
            # download the session log file
            if self.enabled_logs and self.browser_remote:
                self.__download_file(server_url, path_file, timeout)
            # remove the video file if it does exist
            self.__remove_file(server_url)

    def download_file(self, filename, timeout=10):
        """
        download a file from from remote selenoid and removing the file in the server.
        request: http://<username>:<password>@<ggr_host>:<ggr_port>/download/<ggr_session_id>/<filename>
        :param filename: file name with extension to download
        """
        if self.selenoid_flag:
            path_file = os.path.join(DriverWrappersPool.output_directory, DOWNLOADS_PATH, self.session_id[-8:], filename)
            server_url = 'http://{}:{}@{}:{}/download/{}/{}'.\
                format(self.username, self.password, self.ggr_host, self.ggr_port, self.session_id, filename)
            # download the session log file
            if self.browser_remote:
                self.__download_file(server_url, path_file, timeout)
