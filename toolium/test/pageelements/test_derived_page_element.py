# -*- coding: utf-8 -*-
"""
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
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.pageelements import PageElement, Text, InputText, Button, Select, Group
from toolium.pageelements import select_page_element
from toolium.pageobjects.page_object import PageObject

child_element = 'child_element'
mock_element = None


def get_mock_select():
    # Mock text property
    mock_prop_text = mock.PropertyMock(return_value='option value')
    mock_text = mock.MagicMock()
    type(mock_text).text = mock_prop_text
    # Mock first_selected_option property
    mock_prop_option = mock.PropertyMock(return_value=mock_text)
    mock_option = mock.MagicMock()
    type(mock_option).first_selected_option = mock_prop_option
    # Mock select
    mock_select = mock.MagicMock(return_value=mock_option)
    return mock_select


class Menu(Group):
    logo = PageElement(By.ID, 'image')


class LoginPageObject(PageObject):
    title = Text(By.ID, 'title')
    username = InputText(By.XPATH, '//input[0]')
    password = InputText(By.ID, 'password')
    language = Select(By.ID, 'language')
    login = Button(By.ID, 'login')
    menu = Menu(By.ID, 'menu')
    username_shadowroot = InputText(By.XPATH, '//input[1]', shadowroot='shadowroot_css')


@pytest.fixture
def driver_wrapper():
    # Create a mock element
    global mock_element
    mock_element = mock.MagicMock(spec=WebElement)
    mock_element.find_element.return_value = child_element
    mock_element.text = 'text value'
    mock_element.get_attribute.return_value = 'input text value'

    # Reset wrappers pool values
    DriverWrappersPool._empty_pool()
    DriverWrapper.config_properties_filenames = None

    # Create a new wrapper
    driver_wrapper = DriverWrappersPool.get_default_wrapper()
    driver_wrapper.driver = mock.MagicMock()
    driver_wrapper.is_mobile_test = mock.MagicMock(return_value=False)

    return driver_wrapper


def test_locator(driver_wrapper):
    page_object = LoginPageObject(driver_wrapper)

    assert page_object.title.locator == (By.ID, 'title')
    assert page_object.username.locator == (By.XPATH, '//input[0]')
    assert page_object.password.locator == (By.ID, 'password')
    assert page_object.language.locator == (By.ID, 'language')
    assert page_object.login.locator == (By.ID, 'login')
    assert page_object.menu.locator == (By.ID, 'menu')
    assert page_object.menu.logo.locator == (By.ID, 'image')

    # Check that elements inside a group have the group as parent
    assert page_object.menu.logo.parent == page_object.menu


def test_get_text(driver_wrapper):
    driver_wrapper.driver.find_element.return_value = mock_element

    title_value = LoginPageObject().title.text

    assert title_value == 'text value'


def test_get_input_text(driver_wrapper):
    driver_wrapper.driver.find_element.return_value = mock_element
    driver_wrapper.is_android_test = mock.MagicMock(return_value=False)

    username_value = LoginPageObject().username.text

    mock_element.get_attribute.assert_called_once_with('value')
    assert username_value == 'input text value'


def test_set_input_text(driver_wrapper):
    # Configure driver mock
    driver_wrapper.driver.find_element.return_value = mock_element
    driver_wrapper.is_ios_test = mock.MagicMock(return_value=False)

    LoginPageObject().username.text = 'new input value'

    mock_element.send_keys.assert_called_once_with('new input value')


def test_set_input_text_shadowroot(driver_wrapper):
    # Configure driver mock
    driver_wrapper.driver.find_element.return_value = mock_element
    driver_wrapper.is_ios_test = mock.MagicMock(return_value=False)
    text_value = 'new input value'
    expected_script = 'return document.querySelector("shadowroot_css").shadowRoot.querySelector("//input[1]").value ' \
                      '= "new input value"'

    LoginPageObject().username_shadowroot.text = text_value

    mock_element.send_keys.assert_not_called()
    driver_wrapper.driver.execute_script.assert_called_once_with(expected_script)


def test_set_input_text_shadowroot_quotation_marks(driver_wrapper):
    # Configure driver mock
    driver_wrapper.driver.find_element.return_value = mock_element
    driver_wrapper.is_ios_test = mock.MagicMock(return_value=False)
    text_value = 'new "input" value'
    expected_script = 'return document.querySelector("shadowroot_css").shadowRoot.querySelector("//input[1]").value ' \
                      '= "new \\"input\\" value"'

    LoginPageObject().username_shadowroot.text = text_value

    mock_element.send_keys.assert_not_called()
    driver_wrapper.driver.execute_script.assert_called_once_with(expected_script)


def test_get_selected_option(driver_wrapper):
    select_page_element.SeleniumSelect = get_mock_select()

    option = LoginPageObject().language.option

    assert option == 'option value'


def test_set_option(driver_wrapper):
    driver_wrapper.driver.find_element.return_value = mock_element
    select_page_element.SeleniumSelect = get_mock_select()

    LoginPageObject().language.option = 'new option value'

    select_page_element.SeleniumSelect.assert_called_once_with(mock_element)
    select_page_element.SeleniumSelect().select_by_visible_text.assert_called_once_with('new option value')


def test_click_button(driver_wrapper):
    driver_wrapper.driver.find_element.return_value = mock_element
    LoginPageObject().login.click()

    mock_element.click.assert_called_once_with()


def test_group_reset_object(driver_wrapper):
    login_page = LoginPageObject()

    # Check that web elements are empty
    assert login_page.menu._web_element is None
    assert login_page.menu.logo._web_element is None
    assert login_page.menu.logo.parent == login_page.menu

    login_page.menu.logo.web_element

    # Check that web elements are filled
    assert login_page.menu._web_element is not None
    assert login_page.menu.logo._web_element is not None
    assert login_page.menu.logo.parent == login_page.menu

    login_page.menu.reset_object()

    # Check that web elements are empty
    assert login_page.menu._web_element is None
    assert login_page.menu.logo._web_element is None
    assert login_page.menu.logo.parent == login_page.menu
