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
import six
from nose.tools import assert_equal
from selenium.webdriver.common.by import By

from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.pageelements import PageElement
from toolium.pageobjects.page_object import PageObject

child_element = 'child_element'
mock_element = None


@mock.patch('selenium.webdriver.remote.webelement.WebElement', spec=True)
def get_mock_element(WebElement):
    element = WebElement.return_value
    element.find_element.return_value = child_element
    return element


class LoginPageObject(PageObject):
    username = PageElement(By.NAME, 'username')
    password = PageElement(By.ID, 'password', username)


class RegisterPageObject(PageObject):
    username = PageElement(By.NAME, 'username')
    password = PageElement(By.ID, 'password', username)

    def init_page_elements(self):
        self.language = PageElement(By.ID, 'language')
        self.email = PageElement(By.ID, 'email', mock_element)
        self.address = PageElement(By.ID, 'address', (By.ID, 'parent'))


class TestGenericPageElement(unittest.TestCase):
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

        assert_equal(page_object.username.locator, (By.NAME, 'username'))
        assert_equal(page_object.password.locator, (By.ID, 'password'))

    def test_get_element(self):
        LoginPageObject().username.element

        assert_equal(self.driver_wrapper.driver.find_element.mock_calls, [mock.call(By.NAME, 'username')])

    def test_get_element_init_page(self):
        RegisterPageObject().language.element

        assert_equal(self.driver_wrapper.driver.find_element.mock_calls, [mock.call(By.ID, 'language')])

    def test_get_element_with_parent(self):
        self.driver_wrapper.driver.find_element.return_value = mock_element
        web_element = LoginPageObject().password.element

        assert_equal(web_element, child_element)
        assert_equal(self.driver_wrapper.driver.find_element.mock_calls, [mock.call(By.NAME, 'username')])
        assert_equal(mock_element.find_element.mock_calls, [mock.call(By.ID, 'password')])

    def test_get_element_with_parent_locator(self):
        self.driver_wrapper.driver.find_element.return_value = mock_element
        web_element = RegisterPageObject().address.element

        assert_equal(web_element, child_element)
        assert_equal(self.driver_wrapper.driver.find_element.mock_calls, [mock.call(By.ID, 'parent')])
        assert_equal(mock_element.find_element.mock_calls, [mock.call(By.ID, 'address')])

    def test_get_element_with_parent_webelement(self):
        web_element = RegisterPageObject().email.element

        assert_equal(web_element, child_element)
        assert_equal(self.driver_wrapper.driver.find_element.mock_calls, [])
        assert_equal(mock_element.find_element.mock_calls, [mock.call(By.ID, 'email')])

    def test_get_element_in_test(self):
        PageElement(By.NAME, 'username').element

        assert_equal(self.driver_wrapper.driver.find_element.mock_calls, [mock.call(By.NAME, 'username')])

    def test_get_element_two_times(self):
        login_page = LoginPageObject()
        login_page.username.element
        login_page.username.element

        # find_element is not called the second time
        if six.PY2:
            second_call = mock.call().__nonzero__()
        else:
            second_call = mock.call().__bool__()
        assert_equal(self.driver_wrapper.driver.find_element.mock_calls, [mock.call(By.NAME, 'username'), second_call])
