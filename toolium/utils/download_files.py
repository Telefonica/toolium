# -*- coding: utf-8 -*-
u"""
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
import difflib
import filecmp
import os
import time

try:
    from urllib import urlretrieve, urlopen   # Py2
    from urlparse import urljoin
except ImportError:
    from urllib.request import urlretrieve, urlopen  # Py3
    from urllib.parse import urljoin

import requests
from lxml import html

from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.path_utils import makedirs_safe


DOWNLOADS_SERVICE_PORT = 8001
DOWNLOADS_FOLDER = 'downloads'


def get_download_directory_base(context):
    """
    Get base folder to download files
    :param context: behave context
    :returns: base folder
    """
    if context.download_directory is None:
        base = None
    elif context.driver_wrapper.config.getboolean_optional('Server', 'enabled'):
        try:
            platform = context.driver_wrapper.config.get('Driver', 'type').split('-')[3]
        except IndexError:
            platform = 'linux'
        if platform.lower().startswith('win'):
            # Windows node
            base = 'C:\\tmp\\%s\\' % DOWNLOADS_FOLDER
        else:
            # Linux or Mac node
            base = '/tmp/%s/' % DOWNLOADS_FOLDER
    else:
        # Local folder
        destination_folder = os.path.join(DriverWrappersPool.output_directory, DOWNLOADS_FOLDER, '')
        makedirs_safe(destination_folder)
        base = str(destination_folder)
    return base


def get_downloaded_file_path(context, file_name):
    """
    Get local downloaded file path and retrieve remote file if necessary
    :param context: behave context
    :param file_name: downloaded file name
    :returns: local file path
    """
    # TODO: use Selenoid method when it works in any node
    # if context.driver_wrapper.server_type in ['ggr', 'selenoid']:
    #     downloaded_file = Selenoid(context.driver_wrapper).download_file(file_name)
    # elif context.driver_wrapper.server_type == 'grid':
    if context.driver_wrapper.server_type in ['ggr', 'selenoid', 'grid']:
        downloaded_file = retrieve_remote_downloaded_file(context, file_name)
    else:
        downloaded_file = os.path.join(context.download_directory_base, context.download_directory, file_name)
    return downloaded_file


def retrieve_remote_downloaded_file(context, filename, destination_filename=None):
    """
    Retrieves a file downloaded in a remote node and saves it in the output folder
    :param context: behave context
    :param filename: downloaded file
    :param destination_filename: local destination name
    :returns: destination file path
    """
    destination_filepath = None
    if context.download_directory is not None and context.driver_wrapper.config.getboolean_optional('Server',
                                                                                                    'enabled'):
        url = _get_download_directory_url(context)
        file_url = '%s/%s' % (url, filename)
        destination_folder = os.path.join(DriverWrappersPool.output_directory, DOWNLOADS_FOLDER,
                                          context.download_directory)
        makedirs_safe(destination_folder)
        destination_filename = destination_filename if destination_filename else filename
        destination_filepath = os.path.join(destination_folder, destination_filename)
        context.logger.info('Retrieving downloaded file from "%s" to "%s"', file_url, destination_filepath)

        urlretrieve(file_url.encode('utf-8').decode(), destination_filepath)

    return destination_filepath


def get_downloaded_files_list(context):
    if context.download_directory is not None and context.driver_wrapper.config.getboolean_optional('Server',
                                                                                                    'enabled'):
        url = _get_download_directory_url(context)

        context.logger.info("Getting downloads list from '%s'", url)

        content = urlopen(url).read()

        return html.fromstring(content).xpath('//li/a/text()')

    if context.download_directory is None:
        destination_folder = os.path.join(DriverWrappersPool.output_directory, DOWNLOADS_FOLDER)
    else:
        destination_folder = os.path.join(DriverWrappersPool.output_directory, DOWNLOADS_FOLDER,
                                          context.download_directory)

    return os.listdir(destination_folder)


def _get_remote_node_for_download(context):
    remote_node = context.driver_wrapper.remote_node
    return remote_node


def _get_download_directory_url(context):
    remote_node = _get_remote_node_for_download(context)
    if context.download_directory:
        host = 'http://{}:{}'.format(remote_node, DOWNLOADS_SERVICE_PORT)
        url = urljoin(host, context.download_directory)
    else:
        url = 'http://{}:{}'.format(remote_node, DOWNLOADS_SERVICE_PORT)
    return url


def compare_downloaded_file(context, file_name, expected_folder, max_wait):
    """
    Compare downloaded file with the expected file
    :param context: behave context
    :param file_name: downloaded file
    :param expected_folder: folder with expected files
    :param max_wait: max time to wait
    """
    # Get downloaded file and compare with expected file
    template_file = os.path.join(os.getcwd(), expected_folder, file_name)
    start_time = time.time()
    while time.time() < start_time + max_wait:
        downloaded_file = get_downloaded_file_path(context, file_name)
        try:
            equals = filecmp.cmp(template_file, downloaded_file)
        except Exception:
            # File not found
            equals = False
        if equals:
            break
        time.sleep(1)
    end_time = time.time()

    # Show different lines in txt files
    delta = ''
    if not equals and file_name.endswith('.txt'):
        with open(downloaded_file) as downloaded, open(template_file) as template:
            diff = difflib.ndiff(downloaded.readlines(), template.readlines())
            delta = ''.join(x[2:] for x in diff if x.startswith('- '))
            delta = ':\n%s' % delta

    assert equals, ('The downloaded file "%s" is not equal to the expected file "%s" %s' % (
        file_name, os.path.join(expected_folder, file_name), delta))
    context.logger.debug('File downloaded in %f seconds', end_time - start_time)


def wait_until_remote_file_downloaded(context, filename, wait_sec=15):
    """
    Wait until remote file is downloaded.
    :param context: where you and behave can store information to share around. Automatically managed by behave.
    :param filename: (string) name of the file.
    :param wait_sec: time to wait in seconds
    """
    url = _get_download_directory_url(context)
    file_url = u'{url}/{filename}'.format(url=url, filename=filename)

    response = u'ERROR'
    end_time = time.time() + wait_sec
    while 'ERROR' in response:
        assert time.time() <= end_time, u'File "{}" has not been downloaded in {} seconds: {}' \
            .format(file_url, wait_sec, response)
        time.sleep(1)
        try:
            response = requests.get(file_url).text
        except Exception as e:
            response = u'ERROR Exception in get method: \n %s' % e


def delete_remote_downloaded_file(context, file_dwn):
    """
    Delete from url given file name.
    :param context: where you and behave can store information to share around. Automatically managed by behave.
    :param file_dwn: (string) name of the file downloaded.
    """
    if context.driver_wrapper.config.getboolean_optional('Server', 'enabled'):
        url = _get_download_directory_url(context)
        file_dwn_url = u'{url}/{filename}'.format(url=url, filename=file_dwn)
        r_dwn = requests.delete(file_dwn_url)
        print(r_dwn.status_code)
        assert r_dwn.status_code == 200, u'ERROR deleting file "{}": "{}"'.format(file_dwn_url, r_dwn.text)


def delete_retrieved_downloaded_file(context, file_dwn, file_retr):
    """
    Delete from local directory given file name.
    :param context: where you and behave can store information to share around. Automatically managed by behave.
    :param file_dwn: (string) name of the file downloaded.
    :param file_retr: (string) name of the file.
    """

    destination_filename = file_retr if file_retr else file_dwn
    destination_filepath = os.path.join(DriverWrappersPool.output_directory, DOWNLOADS_FOLDER,
                                        context.download_directory)
    try:
        os.remove(os.path.join(destination_filepath, destination_filename))
        if len(destination_filepath.split(DOWNLOADS_FOLDER)[1]) > 2:  # only used in case of session folder
            os.rmdir(destination_filepath)
    except Exception as e:
        context.logger.warning(e)
