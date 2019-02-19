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

# constants
STATUS_OK = 200
DOWNLOADS_PATH = u'downloads'
MP4_EXTENSION = u'mp4'
LOG_EXTENSION = u'log'


class Selenoid(object):
    """
    properties.cfg or local-properties.cfg files:
    ---------------------------------------------
    [Capabilities]
    # capabilities to selenoid
    enableVideo: true
    enableVNC: true

    [Server]
    enabled: true            --> MANDATORY
    host: <hostname or ip>   --> MANDATORY
    port: <numeric>          --> MANDATORY
    username: <string>       --> MANDATORY
    password: <string>       --> MANDATORY
    video_enabled: true
    logs_enabled: true

    Comments:
       the files are always removed in the selenoid server
    """

    def __init__(self, driver_wrapper, **kwargs):
        """
        get data from properties file and session
        :param driver_wrapper: driver_wrapper instance from toolium
        dynamic parameters:
        :param videos_dir: videos directory to download
        :param logs_dir: logs directory to download
        :param output_dir: general directory to download
        """
        self.driver_wrapper = driver_wrapper
        from toolium.driver_wrappers_pool import DriverWrappersPool
        self.videos_directory = kwargs.get('videos_dir', DriverWrappersPool.videos_directory)
        self.logs_directory = kwargs.get('logs_dir', DriverWrappersPool.logs_directory)
        self.output_directory = kwargs.get('output_dir', DriverWrappersPool.output_directory)
        self.browser_remote = driver_wrapper.config.getboolean_optional('Server', 'enabled', False)
        self.enabled_logs = driver_wrapper.config.getboolean_optional('Server', 'logs_enabled', False)

        if self.browser_remote:
            self.session_id = driver_wrapper.driver.session_id
            self.server_url = driver_wrapper.utils.get_server_url()

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
        took = time.time() - init_time  # time used to download the file
        # create the folders and store the file downloaded
        if status_code == STATUS_OK:
            path, name = os.path.split(path_file)
            if not os.path.exists(path):
                os.makedirs(path)
            try:
                fp = open(path_file, 'wb')
                fp.write(body.content)
                fp.close()
                self.driver_wrapper.logger.info('the %s file has been downloaded successfully and took %d'
                                                ' seconds' % (path_file, took))
                return True
            except IOError as e:
                self.driver_wrapper.logger.warn('the %s file has a problem; \n %s' % (path_file, e))
        else:
            self.driver_wrapper.logger.warn('the file to download does not exist in the server after %s seconds'
                                            ' (timeout).' % timeout)
        return False

    def __remove_file(self, url):
        """
        remove a file in the Selenoid node
        """
        requests.delete(url)

    def get_selenoid_info(self):
        """
        retrieve the current selenoid host info
        request: http://<username>:<password>@<ggr_host>:<ggr_port>/host/<ggr_session_id>
        :return: dict
        """
        host_url = '{}/host/{}'.format(self.server_url, self.session_id)
        try:
            selenoid_info = requests.get(host_url).json()
        except Exception:
            return None
        self.driver_wrapper.logger.info('Selenoid host info: \n %s' % selenoid_info)
        return selenoid_info

    def download_session_video(self, scenario_name, timeout=10):
        """
        download the execution video file if the scenario fails or the video is enabled,
        renaming the file to scenario name and removing the video file in the server.
             GGR request: http://<username>:<password>@<ggr_host>:<ggr_port>/video/<session_id>
        selenoid request: http://<username>:<password>@<ggr_host>:<ggr_port>/video/<session_id>.mp4
        :param scenario_name: scenario name
        :param timeout: threshold until the video file is downloaded
        """
        path_file = os.path.join(self.videos_directory, '%s.%s' % (scenario_name, MP4_EXTENSION))
        if self.driver_wrapper.server_type == 'selenoid':
            filename = '%s.%s' % (self.session_id, MP4_EXTENSION)
        else:
            filename = self.session_id
        video_url = '{}/video/{}'.format(self.server_url, filename)
        # download the execution video file if the scenario is failed
        if self.browser_remote:
            self.__download_file(video_url, path_file, timeout)
        # remove the video file if it does exist
        self.__remove_file(video_url)

    def download_session_log(self, scenario_name, timeout=10):
        """
        download the session log file from remote selenoid,
        renaming the file to scenario name and removing the video file in the server.
             GGR request: http://<username>:<password>@<ggr_host>:<ggr_port>/logs/<ggr_session_id>
        selenoid request: http://<username>:<password>@<ggr_host>:<ggr_port>/logs/<ggr_session_id>.log
        :param scenario_name: scenario name
        :param timeout: threshold until the video file is downloaded
        """
        path_file = os.path.join(self.logs_directory, '%s_ggr.%s' % (scenario_name, LOG_EXTENSION))
        if self.driver_wrapper.server_type == 'selenoid':
            filename = '%s.%s' % (self.session_id, LOG_EXTENSION)
        else:
            filename = self.session_id
        logs_url = '{}/logs/{}'.format(self.server_url, filename)
        # download the session log file
        if self.enabled_logs and self.browser_remote:
            self.__download_file(logs_url, path_file, timeout)
        # remove the log file if it does exist
        self.__remove_file(logs_url)

    def download_file(self, filename, timeout=10):
        """
        download a file from remote selenoid and removing the file in the server.
        request: http://<username>:<password>@<ggr_host>:<ggr_port>/download/<ggr_session_id>/<filename>
        :param filename: file name with extension to download
        :param timeout: threshold until the video file is downloaded
        :return: downloaded file path or None
        """
        path_file = os.path.join(self.output_directory, DOWNLOADS_PATH, self.session_id[-8:], filename)
        file_url = '{}/download/{}/{}'.format(self.server_url, self.session_id, filename)
        # download the session log file
        if self.browser_remote:
            self.__download_file(file_url, path_file, timeout)
            return path_file
        return None
