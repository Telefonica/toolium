# -*- coding: utf-8 -*-
"""
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
import requests
import time

from ast import literal_eval
from toolium.utils.path_utils import makedirs_safe

# constants
STATUS_OK = 200
STATUS_PORT = '8888'
DOWNLOADS_PATH = 'downloads'
MP4_EXTENSION = 'mp4'
LOG_EXTENSION = 'log'


class Selenoid(object):
    """
    properties.cfg or local-properties.cfg files:
    ---------------------------------------------
    [Capabilities]
    selenoid___options: {'enableVideo': True, 'enableVNC': True, 'enableLog': True}

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
        self.browser = driver_wrapper.driver.capabilities['browserName']

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
        self.driver_wrapper.logger.info('Downloading file from Selenoid node: %s' % url)
        # retries policy
        while status_code != STATUS_OK and time.time() - init_time < float(timeout):
            body = requests.get(url)
            status_code = body.status_code
            if status_code != STATUS_OK:
                time.sleep(1)
        took = time.time() - init_time  # time used to download the file
        # create the folders and store the file downloaded
        if status_code == STATUS_OK:
            path, name = os.path.split(path_file)
            makedirs_safe(path)
            try:
                fp = open(path_file, 'wb')
                fp.write(body.content)
                fp.close()
                self.driver_wrapper.logger.info('File has been downloaded successfully to "%s" and took %d '
                                                'seconds' % (path_file, took))
                return True
            except IOError as e:
                self.driver_wrapper.logger.warning('Error writing downloaded file in "%s":\n %s' % (path_file, e))
        else:
            self.driver_wrapper.logger.warning('File "%s" does not exist in the server after %s seconds' % (url,
                                                                                                            timeout))
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
        self.driver_wrapper.logger.info(f'Selenoid host info: {selenoid_info}')
        return selenoid_info

    def is_the_session_still_active(self):
        """
        Is the GGR session still active? Associated to a browser and the sessionId
        Example of GGR status:

        .. code-block:: json

            {
            "browsers": {
                "MicrosoftEdge": {
                "latest": {}
                },
                "android": {
                "8.1": {}
                },
                "chrome": {
                "70.0": {},
                "latest": {
                    "test_tef": {
                    "count": 1,
                    "sessions": [
                        {
                        "caps": {
                            "browserName": "chrome",
                            "enableVNC": true,
                            "enableVideo": true,
                            "platformName": "ANY",
                            "screenResolution": "1280x1024x24",
                            "browserVersion": "latest",
                            "videoName": "selenoide952e551bb9395e16d060f28c54e5d31.mp4",
                            "videoScreenSize": "1280x1024"
                        },
                        "container": "8489205e28c9781472e99c3921a6240de3894a3603ed9e187ad6360b6b013b8b",
                        "containerInfo": {
                            "id": "8489205e28c9781472e99c3921a6240de3894a3603ed9e187ad6360b6b013b8b",
                            "ip": "172.17.0.4"
                        },
                        "id": "1345506093dfed8dbcef610da476911a228ca315978e5464ae49fb1142bbc49b",
                        "screen": "1280x1024x24",
                        "vnc": true
                        }
                    ]
                    }
                }
                },
                "firefox": {
                "59.0": {},
                "63.0": {},
                "64.0": {},
                "latest": {}
                },
                "internet explorer": {
                "11": {}
                },
                "safari": {
                "latest": {}
                }
            },
            "pending": 0,
            "queued": 0,
            "total": 30,
            "used": 1
            }

        :return boolean (although in case of error in the request will be returned None)
        """
        server_url_splitted = self.server_url.split(':')
        host_url = '{}:{}:{}:{}/status'.format(server_url_splitted[0], server_url_splitted[1], server_url_splitted[2],
                                               STATUS_PORT)

        try:
            response = requests.get(host_url).json()['browsers'][self.browser]
        except Exception as e:
            self.driver_wrapper.logger.warning('the GGR status request has failed: \nResponse:  %s \n'
                                               'Error message: %s\n' % (response.content, e))
            return None
        for browser in response:
            if response[browser] != {}:
                sessions = response[browser][server_url_splitted[1].split('@')[0].replace('//', '')]['sessions']
                for session in sessions:
                    if session['id'] == self.session_id:
                        return True
        return False

    def get_selenoid_option(self, option_name):
        """
        Get selenoid option value from configured capabilities
        :param option_name: option name
        :returns: option value
        """
        try:
            option_value = literal_eval(self.driver_wrapper.config.get('Capabilities', 'selenoid:options'))[option_name]
        except Exception:
            option_value = None
        return option_value

    def download_session_video(self, scenario_name, timeout=5):
        """
        download the execution video file if the scenario fails or the video is enabled,
        renaming the file to scenario name and removing the video file in the server.
        GGR request: http://<username>:<password>@<ggr_host>:<ggr_port>/video/<session_id>
        selenoid request: http://<username>:<password>@<ggr_host>:<ggr_port>/video/<session_id>.mp4
        :param scenario_name: scenario name
        :param timeout: threshold until the video file is downloaded
        """
        # Download video only in linux nodes with video enabled
        if self.driver_wrapper.get_driver_platform() != 'linux' or not self.get_selenoid_option('enableVideo'):
            return

        path_file = os.path.join(self.videos_directory, '%s.%s' % (scenario_name, MP4_EXTENSION))
        if self.driver_wrapper.server_type == 'selenoid':
            filename = '%s.%s' % (self.session_id, MP4_EXTENSION)
        else:
            filename = self.session_id
        video_url = '{}/video/{}'.format(self.server_url, filename)
        # download the execution video file
        if self.browser_remote:
            self.__download_file(video_url, path_file, timeout)
        # remove the video file if it does exist
        self.__remove_file(video_url)

    def download_session_log(self, scenario_name, timeout=5):
        """
        download the session log file from remote selenoid,
        renaming the file to scenario name and removing the log file in the server.
        GGR request: http://<username>:<password>@<ggr_host>:<ggr_port>/logs/<ggr_session_id>
        selenoid request: http://<username>:<password>@<ggr_host>:<ggr_port>/logs/<ggr_session_id>.log
        :param scenario_name: scenario name
        :param timeout: threshold until the log file is downloaded
        """
        # Download logs only in linux nodes with logs enabled
        if self.driver_wrapper.get_driver_platform() != 'linux' or not self.get_selenoid_option('enableLog'):
            return

        path_file = os.path.join(self.logs_directory, '%s_ggr.%s' % (scenario_name, LOG_EXTENSION))
        if self.driver_wrapper.server_type == 'selenoid':
            filename = '%s.%s' % (self.session_id, LOG_EXTENSION)
        else:
            filename = self.session_id
        logs_url = '{}/logs/{}'.format(self.server_url, filename)
        # download the session log file
        if self.browser_remote:
            self.__download_file(logs_url, path_file, timeout)
        # remove the log file if it does exist
        self.__remove_file(logs_url)

    def download_file(self, filename, timeout=5):
        """
        download a file from remote selenoid and removing the file in the server.
        request: http://<username>:<password>@<ggr_host>:<ggr_port>/download/<ggr_session_id>/<filename>
        :param filename: file name with extension to download
        :param timeout: threshold until the video file is downloaded
        :return: downloaded file path or None
        """
        path_file = os.path.join(self.output_directory, DOWNLOADS_PATH, self.session_id[-8:], filename)
        file_url = '{}/download/{}/{}'.format(self.server_url, self.session_id, filename)
        # download the file
        if self.browser_remote:
            self.__download_file(file_url, path_file, timeout)
            return path_file
        return None
