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

import unittest

import mock
from nose.tools import assert_equal
from selenium.webdriver.common.by import By

from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.pageelements import *
from toolium.pageelements import select_page_element
from toolium.pageobjects.page_object import PageObject

child_element = 'child_element'
mock_element = None


@mock.patch('selenium.webdriver.remote.webelement.WebElement', spec=True)
def get_mock_element(WebElement):
    web_element = WebElement.return_value
    web_element.find_element.return_value = child_element
    web_element.text = 'text value'
    web_element.get_attribute.return_value = 'input text value'
    return web_element


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


class LoginPageObject(PageObject):
    title = Text(By.ID, 'title')
    username = InputText(By.ID, 'username')
    password = InputText(By.ID, 'password')
    language = Select(By.ID, 'language')
    login = Button(By.ID, 'login')


class TestPageElements(unittest.TestCase):
    def setUp(self):
        """Create a new mock element and a new driver before each test"""
        global mock_element
        mock_element = get_mock_element()

        # Reset wrappers pool values
        DriverWrappersPool._empty_pool()
        DriverWrapper.config_properties_filenames = None

        # Create a new wrapper
        self.driver_wrapper = DriverWrappersPool.get_default_wrapper()
        self.driver_wrapper.driver = mock.MagicMock()

    def test_locator(self):
        page_object = LoginPageObject()

        assert_equal(page_object.title.locator, (By.ID, 'title'))
        assert_equal(page_object.username.locator, (By.ID, 'username'))
        assert_equal(page_object.password.locator, (By.ID, 'password'))
        assert_equal(page_object.language.locator, (By.ID, 'language'))
        assert_equal(page_object.login.locator, (By.ID, 'login'))

    def test_get_text(self):
        self.driver_wrapper.driver.find_element.return_value = mock_element

        title_value = LoginPageObject().title.text

        assert_equal(title_value, 'text value')

    def test_get_input_text(self):
        self.driver_wrapper.driver.find_element.return_value = mock_element

        username_value = LoginPageObject().username.text

        assert_equal(username_value, 'input text value')

    def test_set_input_text(self):
        # Configure driver mock
        self.driver_wrapper.driver.find_element.return_value = mock_element
        self.driver_wrapper.is_ios_test = mock.MagicMock(return_value=False)

        LoginPageObject().username.text = 'new input value'

        assert_equal(mock_element.send_keys.mock_calls, [mock.call('new input value')])

    def test_get_selected_option(self):
        select_page_element.SeleniumSelect = get_mock_select()

        option = LoginPageObject().language.option

        assert_equal(option, 'option value')

    def test_select_option(self):
        select_page_element.SeleniumSelect = get_mock_select()

        LoginPageObject().language.option = 'new option value'

        assert_equal(len(select_page_element.SeleniumSelect.mock_calls), 1)
        assert_equal(select_page_element.SeleniumSelect().mock_calls,
                     [mock.call.select_by_visible_text('new option value')])

    def test_click_button(self):
        self.driver_wrapper.driver.find_element.return_value = mock_element
        LoginPageObject().login.click()

        assert_equal(mock_element.click.mock_calls, [mock.call()])
