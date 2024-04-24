# -*- coding: utf-8 -*-
"""
Copyright 2022 Telefónica Investigación y Desarrollo, S.A.U.
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

import json
import logging
import os
import requests
import time
from configparser import NoOptionError

from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.utils import dataset
from toolium.utils.dataset import map_param

"""
====================
PROJECT REQUIREMENTS
====================

Set the language used to get the POEditor texts in the toolium config file ([TestExecution] language):

[TestExecution]
language: es-es

In your project configuration dictionary (saved in dataset.project_config), add an entry like this:

"poeditor": {
    "base_url": "https://api.poeditor.com",
    "api_token": "XXXXX",
    "project_name": "My-Bot",
    "prefixes": [],
    "key_field": "reference",
    "search_type": "contains",
    "ignore_empty": False,
    "file_path": "output/poeditor_terms.json",
    "mode": "online"
}

Only api_token and project_name parameters are mandatory.

If the file_path property is not configured as above, the file name will default to "poeditor_terms.json"
and the path will default to DriverWrappersPool.output_directory ("output" by default).

Call to load_poeditor_texts method to load POEditor terms. The method will download terms from POEditor or load them
from file, and save them in dataset.poeditor_terms.

NOTE: The api_token can be generated from POEditor in this url: https://poeditor.com/account/api
"""

# POEDITOR ENDPOINTS

ENDPOINT_POEDITOR_LIST_PROJECTS = "v2/projects/list"
ENDPOINT_POEDITOR_LIST_LANGUAGES = "v2/languages/list"
ENDPOINT_POEDITOR_LIST_TERMS = "v2/terms/list"
ENDPOINT_POEDITOR_EXPORT_PROJECT = "v2/projects/export"
ENDPOINT_POEDITOR_DOWNLOAD_FILE = "v2/download/file"

# Configure logger
logger = logging.getLogger(__name__)


def download_poeditor_texts(file_type='json'):
    """
    Executes all steps to download texts from POEditor and saves them to a file in output dir

    :param file_type: file type (only json supported)
    :return: N/A
    """
    project_info = get_poeditor_project_info_by_name()
    language_codes = get_poeditor_language_codes(project_info)
    language = get_valid_lang(language_codes)
    poeditor_terms = export_poeditor_project(project_info, language, file_type)
    save_downloaded_file(poeditor_terms)
    # Save terms in dataset to be used in [POE:] map_param replacements
    dataset.poeditor_terms = poeditor_terms


def get_poeditor_project_info_by_name(project_name=None):
    """
    Get POEditor project info from project name from config or parameter

    :param project_name: POEditor project name
    :return: project info
    """
    projects = get_poeditor_projects()
    project_name = project_name if project_name else map_param('[CONF:poeditor.project_name]')
    projects_by_name = [project for project in projects if project['name'] == project_name]

    if len(projects_by_name) != 1:
        project_names = [project['name'] for project in projects]
        if len(projects_by_name) > 1:
            message = f"There are more than one POEditor project with name \"{project_name}\": {project_names}"
        else:
            message = f"There are no POEditor projects with name \"{project_name}\": {project_names}"
        raise Exception(message)
    return projects_by_name[0]


def get_poeditor_language_codes(project_info):
    """
    Get language codes available for a given project ID

    :param project_info: project info
    :return: project language codes
    """
    params = {"api_token": get_poeditor_api_token(),
              "id": project_info['id']}

    r = send_poeditor_request(ENDPOINT_POEDITOR_LIST_LANGUAGES, "POST", params, 200)
    response_data = r.json()
    assert_poeditor_response_code(response_data, "200")

    language_codes = [lang['code'] for lang in response_data['result']['languages']]
    assert not len(language_codes) == 0, "ERROR: Not languages found in POEditor"
    logger.info('POEditor languages in "%s" project: %s %s' % (project_info['name'], len(language_codes),
                                                               language_codes))
    return language_codes


def search_terms_with_string(lang=None):
    """
    Saves POEditor terms for a given existing language in that project

    :param lang: a valid language existing in that POEditor project
    :return: N/A (saves it to context.poeditor_terms)
    """
    project_info = get_poeditor_project_info_by_name()
    language_codes = get_poeditor_language_codes(project_info)
    language = get_valid_lang(language_codes, lang)
    dataset.poeditor_terms = get_all_terms(project_info, language)


def export_poeditor_project(project_info, lang, file_type):
    """
    Export all texts in project to a given file type

    :param project_info: project info
    :param lang: language configured in POEditor project that will be exported
    :param file_type: There are more available formats to download but only one is supported now: json
    :return: poeditor terms
    """
    assert file_type in ['json'], "Only json file type is supported at this moment"

    params = {"api_token": get_poeditor_api_token(),
              "id": project_info['id'],
              "language": lang,
              "type": file_type}

    r = send_poeditor_request(ENDPOINT_POEDITOR_EXPORT_PROJECT, "POST", params, 200)
    response_data = r.json()
    assert_poeditor_response_code(response_data, "200")

    filename = response_data['result']['url'].split('/')[-1]

    r = send_poeditor_request(ENDPOINT_POEDITOR_DOWNLOAD_FILE + '/' + filename, "GET", {}, 200)
    poeditor_terms = r.json() if r.content else []
    logger.info('POEditor terms in "%s" project with "%s" language: %s' % (project_info['name'], lang,
                                                                           len(poeditor_terms)))
    return poeditor_terms


def save_downloaded_file(poeditor_terms):
    """
    Saves POEditor terms to a file in output dir

    :param poeditor_terms: POEditor terms
    """
    file_path = get_poeditor_file_path()
    with open(file_path, 'w') as f:
        json.dump(poeditor_terms, f, indent=4)
    logger.info('POEditor terms have been saved in "%s" file' % file_path)


def assert_poeditor_response_code(response_data, status_code):
    """
    Check status code returned in POEditor response

    :param response_data: data received in poeditor API response as a dictionary
    :param status_code: expected status code
    """
    assert response_data['response']['code'] == status_code, f"{response_data['response']['code']} status code \
        has been received instead of {status_code} in POEditor response body. Response body: {response_data}"


def get_country_from_config_file():
    """
    Gets the country to use later from config checking if it's a valid one in POEditor

    :return: country
    """
    try:
        country = dataset.toolium_config.get('TestExecution', 'language').lower()
    except NoOptionError:
        assert False, "There is no language configured in test, add it to config or use step with parameter lang_id"
    return country


def get_valid_lang(language_codes, lang=None):
    """
    Check if language provided is a valid one configured and returns the POEditor matched lang

    :param language_codes: valid POEditor language codes
    :param lang: a language from config or from lang parameter
    :return: lang matched from POEditor
    """
    lang = lang if lang else get_country_from_config_file()
    if lang in language_codes:
        matching_lang = lang
    elif lang.split('-')[0] in language_codes:
        matching_lang = lang.split('-')[0]
    else:
        assert False, f"Language {lang} is not included in valid codes: {', '.join(language_codes)}"
    return matching_lang


def get_poeditor_projects():
    """
    Get the list of the projects configured in POEditor

    :return: POEditor projects list
    """
    params = {"api_token": get_poeditor_api_token()}
    r = send_poeditor_request(ENDPOINT_POEDITOR_LIST_PROJECTS, "POST", params, 200)
    response_data = r.json()
    assert_poeditor_response_code(response_data, "200")
    projects = response_data['result']['projects']
    projects_names = [project['name'] for project in projects]
    logger.info('POEditor projects: %s %s' % (len(projects_names), projects_names))
    return projects


def send_poeditor_request(endpoint, method, params, status_code):
    """
    Send a request to the POEditor API

    :param endpoint: endpoint path
    :param method: HTTP method to be used in the request
    :param params: parameters to be sent in the request
    :param code: expected status code
    :return: response
    """
    try:
        base_url = dataset.project_config['poeditor']['base_url']
    except KeyError:
        base_url = 'https://api.poeditor.com'
    url = f'{base_url}/{endpoint}'
    r = requests.request(method, url, data=params)
    assert r.status_code == status_code, f"{r.status_code} status code has been received instead of {status_code} \
        in POEditor response calling to {url}. Response body: {r.json()}"
    return r


def get_all_terms(project_info, lang):
    """
    Get all terms for a given language configured in POEditor

    :param project_info: project_info
    :param lang: a valid language configured in POEditor project
    :return: the list of terms
    """
    params = {"api_token": get_poeditor_api_token(),
              "id": project_info['id'],
              "language": lang}

    r = send_poeditor_request(ENDPOINT_POEDITOR_LIST_TERMS, "POST", params, 200)
    response_data = r.json()
    assert_poeditor_response_code(response_data, "200")
    terms = response_data['result']['terms']
    logger.info('POEditor terms in "%s" project with "%s" language: %s' % (project_info['name'], lang, len(terms)))
    return terms


def load_poeditor_texts():
    """
    Download POEditor texts and save in output folder if the config exists or use previously downloaded texts
    """
    if get_poeditor_api_token():
        # Try to get poeditor mode param from toolium config first
        poeditor_mode = dataset.toolium_config.get_optional('TestExecution', 'poeditor_mode')
        if poeditor_mode:
            dataset.project_config['poeditor']['mode'] = poeditor_mode
        if 'mode' in dataset.project_config['poeditor'] and map_param('[CONF:poeditor.mode]') == 'offline':
            file_path = get_poeditor_file_path()

            # With offline POEditor mode, file must exist
            if not os.path.exists(file_path):
                error_message = 'You are using offline POEditor mode but poeditor file has not been found in %s' % \
                                file_path
                logger.error(error_message)
                assert False, error_message

            with open(file_path, 'r') as f:
                dataset.poeditor_terms = json.load(f)
                last_mod_time = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(os.path.getmtime(file_path)))
                logger.info('Using local POEditor file "%s" with date: %s' % (file_path, last_mod_time))
        else:  # without mode configured or mode = 'online'
            download_poeditor_texts()
    else:
        logger.info("POEditor is not configured")


def get_poeditor_file_path():
    """
    Get configured POEditor file path or default file path

    :return: POEditor file path
    """
    try:
        file_path = dataset.project_config['poeditor']['file_path']
    except KeyError:
        file_path = os.path.join(DriverWrappersPool.output_directory, 'poeditor_terms.json')
    return file_path


def get_poeditor_api_token():
    """
    Get POEditor API token from environment property or configuration property

    :return: POEditor API token
    """
    try:
        api_token = os.environ['poeditor_api_token']
    except KeyError:
        try:
            api_token = dataset.project_config['poeditor']['api_token']
        except (AttributeError, KeyError):
            api_token = None
    return api_token
