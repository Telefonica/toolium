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

from toolium.spec_files_loader.page_element_spec_loader import PageElementSpecLoader

MODEL_LOADED_DATA = {"Name": "the_name",
                     "Locator-Type": "ID",
                     "Locator-Value": "the_locator_id",
                     "Wait-For-Loaded": "True",
                     "Custom-Proerties": {"attr1": "attrvalue2", "attr2": "attrvalue2"}
                     }


def test_page_element_is_built_based_page_element_model():
    loader = PageElementSpecLoader()
    new_page_element_loaded = loader.load_page_element_from_model(MODEL_LOADED_DATA,
                                                                       "PageElement",
                                                                       "toolium.pageelements")
    assert new_page_element_loaded.__class__.__name__ == "PageElement"
    assert hasattr(new_page_element_loaded, "custom_attributes")


def test_page_element_is_built_based_toolium_page_element():
    loader = PageElementSpecLoader()

    new_page_element_loaded = loader.load_page_element_from_model(MODEL_LOADED_DATA,
                                                                       "PageElement",
                                                                       "toolium.pageelements")

    assert not hasattr(new_page_element_loaded, "click")

    new_page_element_loaded = loader.load_page_element_from_model(MODEL_LOADED_DATA,
                                                                       "Button",
                                                                       "toolium.pageelements")
    assert new_page_element_loaded.__class__.__name__ == "Button"
    assert hasattr(new_page_element_loaded, "click")
    assert hasattr(new_page_element_loaded, "custom_attributes")
