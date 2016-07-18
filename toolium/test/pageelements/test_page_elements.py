# -*- coding: utf-8 -*-
u"""
Copyright 2016 Telefónica Investigación y Desarrollo, S.A.U.
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
from toolium.pageelements import PageElement, PageElements
from toolium.pageobjects.page_object import PageObject

child_elements = ['child_element_1', 'child_element_2']
other_child_elements = ['child_element_3', 'child_element_4']


class LoginPageObject(PageObject):
    inputs = PageElements(By.XPATH, '//input')
    links = PageElements(By.XPATH, '//a')
    inputs_parent = PageElements(By.XPATH, '//input', (By.ID, 'parent'))


@pytest.fixture
def driver_wrapper():
    # Reset wrappers pool values
    DriverWrappersPool._empty_pool()
    DriverWrapper.config_properties_filenames = None

    # Create a new wrapper
    driver_wrapper = DriverWrappersPool.get_default_wrapper()
    driver_wrapper.driver = mock.MagicMock()

    return driver_wrapper


def test_get_web_elements(driver_wrapper):
    LoginPageObject().inputs.web_elements

    driver_wrapper.driver.find_elements.assert_called_once_with(By.XPATH, '//input')


def test_get_web_elements_with_parent_locator(driver_wrapper):
    # Create a mock element
    mock_element = mock.MagicMock(spec=WebElement)
    mock_element.find_elements.return_value = child_elements

    driver_wrapper.driver.find_element.return_value = mock_element
    web_elements = LoginPageObject().inputs_parent.web_elements

    assert web_elements == child_elements
    driver_wrapper.driver.find_element.assert_called_once_with(By.ID, 'parent')
    mock_element.find_elements.assert_called_once_with(By.XPATH, '//input')


def test_get_page_elements(driver_wrapper):
    driver_wrapper.driver.find_elements.return_value = child_elements
    page_elements = LoginPageObject().inputs.page_elements

    # Check that find_elements has been called just one time
    driver_wrapper.driver.find_elements.assert_called_once_with(By.XPATH, '//input')
    driver_wrapper.driver.find_element.assert_not_called()

    # Check that the response is a list of 2 PageElement with the expected web element
    assert len(page_elements) == 2
    assert isinstance(page_elements[0], PageElement)
    assert page_elements[0]._web_element == child_elements[0]
    assert isinstance(page_elements[1], PageElement)
    assert page_elements[1]._web_element == child_elements[1]


def test_get_page_elements_and_web_elements(driver_wrapper):
    driver_wrapper.driver.find_elements.return_value = child_elements
    inputs = LoginPageObject().inputs
    page_elements = inputs.page_elements
    web_elements = inputs.web_elements

    # Check that find_elements has been called just one time
    driver_wrapper.driver.find_elements.assert_called_once_with(By.XPATH, '//input')
    driver_wrapper.driver.find_element.assert_not_called()

    # Check that the response is a list of 2 PageElement with the expected web element
    assert len(page_elements) == 2
    assert isinstance(page_elements[0], PageElement)
    assert page_elements[0]._web_element == child_elements[0]
    assert isinstance(page_elements[1], PageElement)
    assert page_elements[1]._web_element == child_elements[1]

    # Check that web_elements are the same elements as page_element._web_element
    assert web_elements[0] is page_elements[0]._web_element
    assert web_elements[1] is page_elements[1]._web_element


def test_multiple_page_elements(driver_wrapper):
    driver_wrapper.driver.find_elements.side_effect = [child_elements, other_child_elements]
    input_page_elements = LoginPageObject().inputs.page_elements
    links_page_elements = LoginPageObject().links.page_elements

    # Check that the response is a list of 2 PageElement with the expected web element
    assert len(input_page_elements) == 2
    assert isinstance(input_page_elements[0], PageElement)
    assert input_page_elements[0]._web_element == child_elements[0]
    assert isinstance(input_page_elements[1], PageElement)
    assert input_page_elements[1]._web_element == child_elements[1]

    # Check that the response is a list of 2 PageElement with the expected web element
    assert len(links_page_elements) == 2
    assert isinstance(links_page_elements[0], PageElement)
    assert links_page_elements[0]._web_element == other_child_elements[0]
    assert isinstance(links_page_elements[1], PageElement)
    assert links_page_elements[1]._web_element == other_child_elements[1]


def test_reset_object(driver_wrapper):
    driver_wrapper.driver.find_elements.side_effect = [child_elements, other_child_elements]
    login_page = LoginPageObject()
    login_page.inputs.web_elements
    login_page.links.web_elements

    # Check that web elements are filled
    assert len(login_page.inputs._web_elements) == 2
    assert len(login_page.links._web_elements) == 2

    login_page.inputs.reset_object()

    # Check that only username is reset
    assert len(login_page.inputs._web_elements) == 0
    assert len(login_page.links._web_elements) == 2
