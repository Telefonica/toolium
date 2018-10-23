# -*- coding: utf-8 -*-
u"""
Copyright 2018 Telefónica Investigación y Desarrollo, S.A.U.
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

from toolium.pageelements import Text, InputTexts
from toolium.pageobjects.page_object_model import PageObjectModel
from toolium.spec_files_loader.page_object_spec_loader import PageObjectSpecLoader

MODEL_LOADED_DATA = {'Login': [{'Text': {'Locator-Value': 'd0f81d3c-d8b0-476b-bcd5-d22ab0153cad',
                                         'Locator-Type': 'ID', 'Name': 'the_name_element_1',
                                         'Wait-For-Loaded': False}},
                               {'InputTexts': {'Locator-Value': '//div/ul', 'Locator-Type': 'XPATH',
                                               'Name': 'the_name_element_2', 'Wait-For-Loaded': True}}]}


def test_page_object_is_built():
    loader = PageObjectSpecLoader()
    new_page_object_loaded = loader.load_page_object_from_model("Login", MODEL_LOADED_DATA["Login"])

    assert new_page_object_loaded.page_name == "Login"
    assert isinstance(new_page_object_loaded, PageObjectModel)


def test_page_elements_in_page_object_are_built():
    loader = PageObjectSpecLoader()
    new_page_object_loaded = loader.load_page_object_from_model("Login", MODEL_LOADED_DATA["Login"])

    assert hasattr(new_page_object_loaded, "the_name_element_1")
    assert isinstance(new_page_object_loaded.the_name_element_1, Text)
    assert new_page_object_loaded.the_name_element_1.locator == ('id', 'd0f81d3c-d8b0-476b-bcd5-d22ab0153cad')

    assert hasattr(new_page_object_loaded, "the_name_element_2")
    assert isinstance(new_page_object_loaded.the_name_element_2, InputTexts)
    assert new_page_object_loaded.the_name_element_2.locator == ('xpath', '//div/ul')
