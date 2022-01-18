# -*- coding: utf-8 -*-
"""
Copyright 2021 Telefónica Investigación y Desarrollo, S.A.U.
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
import time
import requests

from configparser import NoOptionError
from urllib.request import URLopener
from toolium.utils.dataset import map_param

"""
====================
PROJECT REQUIREMENTS
====================

Set the language used to get the POEditor texts in the toolium config file ([TestExecution] language):

[TestExecution]
language: es-es

In your project configuration dictionary (context.project_config), add this entry:

"poeditor": {
    "base_url": "https://api.poeditor.com",
    "api_token": "XXXXX",
    "project_name": "Aura-Bot",
    "prefixes": [],
    "key_field": "reference",
    "search_type": "contains",
    "file_path": "output/poeditor_terms.json"
}

If the file_path property is not configured as above, the file name will default to "poeditor_terms.json" and
the path will default to the value of context.config_files.output_directory (so this attribute would need to be set).

NOTE: The api_token can be generated from POEditor in this url: https://poeditor.com/account/api
"""

# POEDITOR ENDPOINTS

ENDPOINT_POEDITOR_LIST_PROJECTS = "v2/projects/list"
ENDPOINT_POEDITOR_LIST_LANGUAGES = "v2/languages/list"
ENDPOINT_POEDITOR_LIST_TERMS = "v2/terms/list"
ENDPOINT_POEDITOR_EXPORT_PROJECT = "v2/projects/export"
ENDPOINT_POEDITOR_DOWNLOAD_FILE = "v2/download/file"


def download_poeditor_texts(context, file_type):
    """
    Executes all steps to download texts from POEditor and saves them to a file in output dir
    :param context: behave context
    :param file_type: only json supported in this first version
    :return: N/A
    """
    get_poeditor_project_info_by_name(context)
    get_poeditor_language_codes(context)
    export_poeditor_project(context, file_type)
    save_downloaded_file(context)


def get_poeditor_project_info_by_name(context, project_name=None):
    """
    Get POEditor project info from project name from config or parameter
    :param context: behave context
    :param project_name: POEditor project name
    :return: N/A (saves it to context.poeditor_project)
    """
    projects = get_poeditor_projects(context)
    project_name = project_name if project_name else map_param('[CONF:poeditor.project_name]', context)
    projects_by_name = [project for project in projects if project['name'] == project_name]

    assert len(projects_by_name) == 1, "ERROR: Project name %s not found, available projects: %s" % \
                                       (project_name, [project['name'] for project in projects])
    context.poeditor_project = projects_by_name[0]


def get_poeditor_language_codes(context):
    """
    Get language codes available for a given project ID
    :param context: behave context
    :return: N/A (saves it to context.poeditor_language_list)
    """
    params = {"api_token": get_poeditor_api_token(context),
              "id": context.poeditor_project['id']}

    r = send_poeditor_request(context, ENDPOINT_POEDITOR_LIST_LANGUAGES, "POST", params, 200)
    response_data = r.json()
    assert_poeditor_response_code(response_data, "200")

    poeditor_language_list = [lang['code'] for lang in response_data['result']['languages']]
    assert not len(poeditor_language_list) == 0, "ERROR: Not languages found in POEditor"
    context.logger.info('POEditor languages in "%s" project: %s %s' % (context.poeditor_project['name'],
                                                                       len(poeditor_language_list),
                                                                       poeditor_language_list))

    context.poeditor_language_list = poeditor_language_list


def search_terms_with_string(context, lang=None):
    """
    Saves POEditor terms for a given existing language in that project
    :param context: behave context
    :param lang: a valid language existing in that POEditor project
    :return: N/A (saves it to context.poeditor_terms)
    """
    lang = get_valid_lang(context, lang)
    context.poeditor_terms = get_all_terms(context, lang)


def export_poeditor_project(context, file_type, lang=None):
    """
    Export all texts in project to a given file type
    :param context: behave context
    :param file_type: There are more available formats to download but only one is supported now: json
    :param lang: if provided, should be a valid language configured in POEditor project
    :return: N/A (saves it to context.poeditor_export)
    """
    lang = get_valid_lang(context, lang)
    assert file_type in ['json'], "Only json file type is supported at this moment"
    context.poeditor_file_type = file_type

    params = {"api_token": get_poeditor_api_token(context),
              "id": context.poeditor_project['id'],
              "language": lang,
              "type": file_type}

    r = send_poeditor_request(context, ENDPOINT_POEDITOR_EXPORT_PROJECT, "POST", params, 200)
    response_data = r.json()
    assert_poeditor_response_code(response_data, "200")

    context.poeditor_download_url = response_data['result']['url']
    filename = context.poeditor_download_url.split('/')[-1]

    r = send_poeditor_request(context, ENDPOINT_POEDITOR_DOWNLOAD_FILE + '/' + filename, "GET", {}, 200)
    context.poeditor_export = r.json()
    context.logger.info('POEditor terms in "%s" project with "%s" language: %s' % (context.poeditor_project['name'],
                                                                                   lang, len(context.poeditor_export)))


def save_downloaded_file(context):
    """
    Saves POEditor terms to a file in output dir
    :param context: behave context
    :return: N/A
    """
    file_path = get_poeditor_file_path(context)
    saved_file = URLopener()
    saved_file.retrieve(context.poeditor_download_url, file_path)
    context.logger.info('POEditor terms have been saved in "%s" file' % file_path)


def assert_poeditor_response_code(response_data, status_code):
    """
    Check status code returned in POEditor response
    :param response_data: data received in poeditor API response as a dictionary
    :param status_code: expected status code 
    """
    assert response_data['response']['code'] == status_code, f"{response_data['response']['code']} status code \
        has been received instead of {status_code} in POEditor response body. Response body: {r.json()}"


def get_country_from_config_file(context):
    """
    Gets the country to use later from config checking if it's a valid one in POEditor
    :param context: behave context
    :return: country
    """
    try:
        country = context.toolium_config.get('TestExecution', 'language').lower()
    except NoOptionError:
        assert False, "There is no language configured in test, add it to config or use step with parameter lang_id"

    return country


def get_valid_lang(context, lang):
    """
    Check if language provided is a valid one configured and returns the POEditor matched lang
    :param context: behave context
    :param lang: a language from config or from lang parameter
    :return: lang matched from POEditor
    """
    lang = lang if lang else get_country_from_config_file(context)
    if lang in context.poeditor_language_list:
        matching_lang = lang
    elif lang.split('-')[0] in context.poeditor_language_list:
        matching_lang = lang.split('-')[0]
    else:
        assert False, "Language %s in config is not valid, use one of %s:" % (lang, context.poeditor_language_list)
    return matching_lang


def get_poeditor_projects(context):
    """
    Get the list of the projects configured in POEditor
    :param context: behave context
    :return: the list of the projects
    """
    params = {"api_token": get_poeditor_api_token(context)}
    r = send_poeditor_request(context, ENDPOINT_POEDITOR_LIST_PROJECTS, "POST", params, 200)
    response_data = r.json()
    assert_poeditor_response_code(response_data, "200")
    projects = response_data['result']['projects']
    projects_names = [project['name'] for project in projects]
    context.logger.info('POEditor projects: %s %s' % (len(projects_names), projects_names))
    return projects


def send_poeditor_request(context, endpoint, method, params, status_code):
    """
    Send a request to the POEditor API
    :param context: behave context
    :param endpoint: endpoint path
    :param method: HTTP method to be used in the request
    :param params: parameters to be sent in the request
    :param code: expected status code
    :return: response
    """
    url = "/".join([map_param('[CONF:poeditor.base_url]', context), endpoint])
    r = requests.request(method, url, data=params)
    assert r.status_code == status_code, f"{r.status_code} status code has been received instead of {status_code} \
        in POEditor response. Response body: {r.json()}"
    return r


def get_all_terms(context, lang):
    """
    Get all terms for a given language configured in POEditor
    :param context: behave context
    :param lang: a valid language configured in POEditor project
    :return: the list of terms
    """
    params = {"api_token": get_poeditor_api_token(context),
              "id": context.poeditor_project['id'],
              "language": lang}

    r = send_poeditor_request(context, ENDPOINT_POEDITOR_LIST_TERMS, "POST", params, 200)
    response_data = r.json()
    assert_poeditor_response_code(response_data, "200")
    terms = response_data['result']['terms']
    context.logger.info('POEditor terms in "%s" project with "%s" language: %s' % (context.poeditor_project['name'],
                                                                                   lang, len(terms)))

    return terms


def load_poeditor_texts(context):
    """
    Download POEditor texts and save in output folder if the config exists or use previously downloaded texts
    :param context: behave context
    """
    if get_poeditor_api_token(context):
        # Try to get poeditor mode param from toolium config first
        poeditor_mode = context.toolium_config.get_optional('TestExecution', 'poeditor_mode')
        if poeditor_mode:
            context.project_config['poeditor']['mode'] = poeditor_mode
        if 'mode' in context.project_config['poeditor'] and map_param('[CONF:poeditor.mode]', context) == 'offline':
            file_path = get_poeditor_file_path(context)

            # With offline POEditor mode, file must exist
            if not os.path.exists(file_path):
                error_message = 'You are using offline POEditor mode but poeditor file has not been found in %s' % \
                                file_path
                context.logger.error(error_message)
                assert False, error_message

            with open(file_path, 'r') as f:
                context.poeditor_export = json.load(f)
                last_mod_time = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(os.path.getmtime(file_path)))
                context.logger.info('Using local POEditor file "%s" with date: %s' % (file_path, last_mod_time))
        else:  # without mode configured or mode = 'online'
            download_poeditor_texts(context, 'json')
    else:
        context.logger.info("POEditor is not configured")


def get_poeditor_file_path(context):
    """
    Get POEditor file path
    :param context: behave context
    :return: poeditor file path
    """
    try:
        file_path = context.project_config['poeditor']['file_path']
    except KeyError:
        file_type = context.poeditor_file_type if hasattr(context, 'poeditor_file_type') else 'json'
        file_path = os.path.join(context.config_files.output_directory, 'poeditor_terms.%s' % file_type)
    return file_path


def get_poeditor_api_token(context):
    """
    Get POEditor api token from environment property or configuration property
    :return: poeditor api token
    """
    try:
        api_token = os.environ['poeditor_api_token']
    except KeyError:
        api_token = map_param('[CONF:poeditor.api_token]', context)
    return api_token
