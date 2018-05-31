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

import os

import pytest

from toolium.config_parser import ExtendedConfigParser
from toolium.spec_files_loader.config_spec_files_loader import ConfigSpecFilesLoader


@pytest.fixture
def config():
    root_path = os.path.dirname(os.path.realpath(__file__))
    yaml_spec_file = os.path.join(root_path, 'resources', 'pageobject_spec_files',
                                  'example_spec_file_1.yaml')

    config_parser = ExtendedConfigParser()
    config_parser.add_section('PageObjectSpecFiles')
    config_parser.set('PageObjectSpecFiles', 'enabled', 'true')
    config_parser.set('PageObjectSpecFiles', 'spec_files_path', yaml_spec_file)
    return config_parser


@pytest.fixture
def config_dir():
    root_path = os.path.dirname(os.path.realpath(__file__))
    yaml_spec_file = os.path.join(root_path, 'resources', 'pageobject_spec_files')

    config_parser = ExtendedConfigParser()
    config_parser.add_section('PageObjectSpecFiles')
    config_parser.set('PageObjectSpecFiles', 'enabled', 'true')
    config_parser.set('PageObjectSpecFiles', 'spec_files_path', yaml_spec_file)
    return config_parser


def test_load_one_page_object_spec_file(config):
    config_loader = ConfigSpecFilesLoader(config)
    config_loader.load_page_object_definition()

    assert "Login" in config_loader.loaded_page_object_models
    assert "Dashboard" in config_loader.loaded_page_object_models
    assert "Profile" in config_loader.loaded_page_object_models

    assert "Text" in config_loader.loaded_page_object_models["Login"][0]
    assert "InputText" in config_loader.loaded_page_object_models["Login"][1]
    assert "InputText" in config_loader.loaded_page_object_models["Login"][2]
    assert "Button" in config_loader.loaded_page_object_models["Dashboard"][0]
    assert "InputText" in config_loader.loaded_page_object_models["Profile"][0]


def test_load_page_object_definition_from_multiple_files(config_dir):
    config_loader = ConfigSpecFilesLoader(config_dir)
    config_loader.load_page_object_definition()

    assert "Login" in config_loader.loaded_page_object_models
    assert "Dashboard" in config_loader.loaded_page_object_models
    assert "Profile" in config_loader.loaded_page_object_models
    assert "Login2" in config_loader.loaded_page_object_models
    assert "Login3" in config_loader.loaded_page_object_models

    assert "Text" in config_loader.loaded_page_object_models["Login"][0]
    assert "InputText" in config_loader.loaded_page_object_models["Login"][1]
    assert "InputText" in config_loader.loaded_page_object_models["Login"][2]
    assert "Button" in config_loader.loaded_page_object_models["Dashboard"][0]
    assert "InputText" in config_loader.loaded_page_object_models["Profile"][0]
    assert "Text" in config_loader.loaded_page_object_models["Login2"][0]
    assert "Text" in config_loader.loaded_page_object_models["Login3"][0]


def test_load_and_init_page_object(config):
    config_loader = ConfigSpecFilesLoader(config)
    config_loader.load_page_object_definition()

    page_object = config_loader.init_page_object("Dashboard")
    assert page_object.page_name == "Dashboard"
    assert hasattr(page_object, "logout")

    page_object = config_loader.init_page_object("Login")
    assert page_object.page_name == "Login"
    assert hasattr(page_object, "form")
    assert hasattr(page_object, "username")
    assert hasattr(page_object, "password")

    page_object = config_loader.init_page_object("Profile")
    assert page_object.page_name == "Profile"
    assert hasattr(page_object, "name")
