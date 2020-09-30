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

import mock
import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.pageelements import PageElement, Group, PageElements
from toolium.pageobjects.page_object import PageObject

child_element = 'child_element'
mock_element = None


class MenuPageObject(PageObject):
    register = PageElement(By.ID, 'register')

    def init_page_elements(self):
        self.logo = PageElement(By.ID, 'image', wait=True)


class MenuGroup(Group):
    def init_page_elements(self):
        self.logo = PageElement(By.ID, 'image')
        self.logo_wait = PageElement(By.ID, 'image2', wait=True)


class RegisterPageObject(PageObject):
    username = PageElement(By.XPATH, '//input[0]', wait=True)
    password = PageElement(By.ID, 'password', username)

    def init_page_elements(self):
        self.language = PageElement(By.ID, 'language')
        self.email = PageElement(By.ID, 'email', mock_element)
        self.address = PageElement(By.ID, 'address', (By.ID, 'parent'))
        self.inputs = PageElements(By.XPATH, '//input')
        self.menu = MenuPageObject(wait=True)
        self.menu_group = MenuGroup(By.ID, 'menu', wait=True)


@pytest.fixture
def driver_wrapper():
    """Create a new mock element and a new driver before each test"""
    global mock_element
    mock_element = mock.MagicMock(spec=WebElement)
    mock_element.find_element.return_value = child_element

    # Reset wrappers pool values
    DriverWrappersPool._empty_pool()
    DriverWrappersPool.output_directory = ''
    DriverWrapper.config_properties_filenames = None

    # Create a new wrapper
    driver_wrapper = DriverWrappersPool.get_default_wrapper()
    driver_wrapper.driver = mock.MagicMock()

    return driver_wrapper


def test_driver_wrapper(driver_wrapper):
    page_object = RegisterPageObject()

    # Check that the page object and its page elements have the same driver wrapper
    assert page_object.driver_wrapper == driver_wrapper
    assert page_object.username.driver_wrapper == driver_wrapper
    assert page_object.password.driver_wrapper == driver_wrapper
    assert page_object.language.driver_wrapper == driver_wrapper
    assert page_object.email.driver_wrapper == driver_wrapper
    assert page_object.address.driver_wrapper == driver_wrapper
    assert page_object.inputs.driver_wrapper == driver_wrapper

    # Check that the child page object and its page elements have the same driver wrapper
    assert page_object.menu.driver_wrapper == driver_wrapper
    assert page_object.menu.register.driver_wrapper == driver_wrapper
    assert page_object.menu.logo.driver_wrapper == driver_wrapper
    assert page_object.menu_group.driver_wrapper == driver_wrapper
    assert page_object.menu_group.logo.driver_wrapper == driver_wrapper
    assert page_object.menu_group.logo_wait.driver_wrapper == driver_wrapper


def test_two_driver_wrappers(driver_wrapper):
    page_object = RegisterPageObject()
    second_driver_wrapper = DriverWrapper()
    second_page_object = RegisterPageObject(second_driver_wrapper)

    # Check that the page object and its instance page elements have the same driver wrapper
    assert page_object.driver_wrapper == driver_wrapper
    assert page_object.language.driver_wrapper == driver_wrapper
    assert page_object.email.driver_wrapper == driver_wrapper
    assert page_object.address.driver_wrapper == driver_wrapper
    assert page_object.inputs.driver_wrapper == driver_wrapper
    assert page_object.menu.driver_wrapper == driver_wrapper
    assert page_object.menu.logo.driver_wrapper == driver_wrapper
    assert page_object.menu_group.driver_wrapper == driver_wrapper
    assert page_object.menu_group.logo.driver_wrapper == driver_wrapper
    assert page_object.menu_group.logo_wait.driver_wrapper == driver_wrapper

    # Check that the second page object and its instance page elements have the second driver wrapper
    assert second_page_object.driver_wrapper == second_driver_wrapper
    assert second_page_object.language.driver_wrapper == second_driver_wrapper
    assert second_page_object.email.driver_wrapper == second_driver_wrapper
    assert second_page_object.address.driver_wrapper == second_driver_wrapper
    assert second_page_object.inputs.driver_wrapper == second_driver_wrapper
    assert second_page_object.menu.driver_wrapper == second_driver_wrapper
    assert second_page_object.menu.logo.driver_wrapper == second_driver_wrapper
    assert second_page_object.menu_group.driver_wrapper == second_driver_wrapper
    assert second_page_object.menu_group.logo.driver_wrapper == second_driver_wrapper
    assert second_page_object.menu_group.logo_wait.driver_wrapper == second_driver_wrapper

    # Check that the class elements have the last driver wrapper
    # This kind of elements could not be used with multiple drivers
    assert page_object.username.driver_wrapper == second_driver_wrapper
    assert page_object.password.driver_wrapper == second_driver_wrapper
    assert page_object.menu.register.driver_wrapper == second_driver_wrapper
    assert second_page_object.username.driver_wrapper == second_driver_wrapper
    assert second_page_object.password.driver_wrapper == second_driver_wrapper
    assert second_page_object.menu.register.driver_wrapper == second_driver_wrapper


def test_reset_object(driver_wrapper):
    mock_element_11 = mock.MagicMock(spec=WebElement)
    mock_element_12 = mock.MagicMock(spec=WebElement)
    driver_wrapper.driver.find_elements.side_effect = [[mock_element_11, mock_element_12]]
    driver_wrapper.is_mobile_test = mock.MagicMock(return_value=False)

    page_object = RegisterPageObject(driver_wrapper)

    # Search page elements
    page_object.username.web_element
    page_object.password.web_element
    page_object.language.web_element
    page_object.email.web_element
    page_object.address.web_element
    page_object.inputs.web_elements
    page_object.menu.register.web_element
    page_object.menu.logo.web_element
    page_object.menu_group.web_element
    page_object.menu_group.logo.web_element
    page_object.menu_group.logo_wait.web_element

    # Check that all page elements have a web element
    assert page_object.username._web_element is not None
    assert page_object.password._web_element is not None
    assert page_object.language._web_element is not None
    assert page_object.email._web_element is not None
    assert page_object.address._web_element is not None
    assert len(page_object.inputs._web_elements) == 2
    assert page_object.menu.register._web_element is not None
    assert page_object.menu.logo._web_element is not None
    assert page_object.menu_group._web_element is not None
    assert page_object.menu_group.logo._web_element is not None
    assert page_object.menu_group.logo_wait._web_element is not None

    page_object.reset_object()

    # Check that all page elements are reset
    assert page_object.username._web_element is None
    assert page_object.password._web_element is None
    assert page_object.language._web_element is None
    assert page_object.email._web_element is None
    assert page_object.address._web_element is None
    assert len(page_object.inputs._web_elements) == 0
    assert page_object.menu.register._web_element is None
    assert page_object.menu.logo._web_element is None
    assert page_object.menu_group._web_element is None
    assert page_object.menu_group.logo._web_element is None
    assert page_object.menu_group.logo_wait._web_element is None


def test_wait_until_loaded(driver_wrapper):
    driver_wrapper.is_mobile_test = mock.MagicMock(return_value=False)
    page_object = RegisterPageObject(driver_wrapper).wait_until_loaded()

    # Check that all page elements with wait=True have a web element
    assert page_object.username._web_element is not None
    assert page_object.menu.logo._web_element is not None
    assert page_object.menu_group._web_element is not None
    assert page_object.menu_group.logo_wait._web_element is not None

    # Check that all page elements with wait=False have no web element value
    assert page_object.password._web_element is None
    assert page_object.language._web_element is None
    assert page_object.email._web_element is None
    assert page_object.address._web_element is None
    assert page_object.menu.register._web_element is None
    assert page_object.menu_group.logo._web_element is None

    # Check that pageelements have no web elements
    assert len(page_object.inputs._web_elements) == 0


def test_wait_until_loaded_exception(driver_wrapper):
    driver_wrapper.utils.wait_until_element_visible = mock.MagicMock()
    driver_wrapper.utils.wait_until_element_visible.side_effect = TimeoutException('Unknown')

    page_object = MenuPageObject(driver_wrapper)
    with pytest.raises(TimeoutException) as excinfo:
        page_object.wait_until_loaded()
    assert "Page element of type 'PageElement' with locator ('id', 'image') not found or is not " \
           "visible after 10 seconds" in str(excinfo.value)


def test_wait_until_loaded_exception_custom_timeout(driver_wrapper):
    driver_wrapper.utils.wait_until_element_visible = mock.MagicMock()
    driver_wrapper.utils.wait_until_element_visible.side_effect = TimeoutException('Unknown')

    page_object = MenuPageObject(driver_wrapper)
    with pytest.raises(TimeoutException) as excinfo:
        page_object.wait_until_loaded(timeout=15)
    assert "Page element of type 'PageElement' with locator ('id', 'image') not found or is not " \
           "visible after 15 seconds" in str(excinfo.value)
