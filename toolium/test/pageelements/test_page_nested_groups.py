# -*- coding: utf-8 -*-
"""
Copyright 2017 Telefónica Investigación y Desarrollo, S.A.U.
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

import mock
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.pageelements import Group, InputText
from toolium.pageobjects.page_object import PageObject


class InnerGroup(Group):
    def init_page_elements(self):
        self.input = InputText(By.XPATH, './/input')
        self.input_with_parent = InputText(By.XPATH, './/input', parent=self.input)


class OuterGroup(Group):
    def init_page_elements(self):
        self.inner = InnerGroup(By.XPATH, './/div')


class NestedPageObject(PageObject):
    def init_page_elements(self):
        self.outer = OuterGroup(By.XPATH, '//div')


@pytest.fixture
def driver_wrapper():
    # Reset wrappers pool values
    DriverWrappersPool._empty_pool()
    DriverWrapper.config_properties_filenames = None

    # Create a new wrapper
    driver_wrapper = DriverWrappersPool.get_default_wrapper()
    driver_wrapper.driver = mock.MagicMock()

    return driver_wrapper


def test_reset_object_nested_groups(driver_wrapper):
    # Mock Driver.save_web_element = True
    driver_wrapper.config = mock.MagicMock()
    driver_wrapper.config.getboolean_optional.return_value = True
    # Create mock element
    mock_element = mock.MagicMock(spec=WebElement)
    driver_wrapper.driver.find_element.return_value = mock_element

    nested_page = NestedPageObject()

    # Check that web elements are empty
    assert nested_page.outer._web_element is None
    assert nested_page.outer.inner._web_element is None
    assert nested_page.outer.inner.input._web_element is None
    assert nested_page.outer.inner.input_with_parent._web_element is None
    assert nested_page.outer.inner.parent == nested_page.outer
    assert nested_page.outer.inner.input.parent == nested_page.outer.inner
    assert nested_page.outer.inner.input_with_parent.parent == nested_page.outer.inner.input

    nested_page.outer.inner.input.web_element
    nested_page.outer.inner.input_with_parent.web_element

    # Check that web elements are filled
    assert nested_page.outer._web_element is not None
    assert nested_page.outer.inner._web_element is not None
    assert nested_page.outer.inner.input._web_element is not None
    assert nested_page.outer.inner.input_with_parent._web_element is not None
    assert nested_page.outer.inner.parent == nested_page.outer
    assert nested_page.outer.inner.input.parent == nested_page.outer.inner
    assert nested_page.outer.inner.input_with_parent.parent == nested_page.outer.inner.input

    nested_page.outer.reset_object()

    # Check that web elements are empty
    assert nested_page.outer._web_element is None
    assert nested_page.outer.inner._web_element is None
    assert nested_page.outer.inner.input._web_element is None
    assert nested_page.outer.inner.input_with_parent._web_element is None
    assert nested_page.outer.inner.parent == nested_page.outer
    assert nested_page.outer.inner.input.parent == nested_page.outer.inner
    assert nested_page.outer.inner.input_with_parent.parent == nested_page.outer.inner.input
