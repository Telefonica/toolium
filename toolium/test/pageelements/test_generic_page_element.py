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
from selenium.webdriver.common.by import By

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


class TestGenericPageElement(unittest.TestCase):
    def setUp(self):
        """Create a new mock element and a new driver before each test"""
        global mock_element
        mock_element = get_mock_element()

    @mock.patch('toolium.toolium_driver.driver')
    def test_locator(self, driver):
        page_object = LoginPageObject()

        self.assertEqual(page_object.username.locator, (By.NAME, 'username'))
        self.assertEqual(page_object.password.locator, (By.ID, 'password'))

    @mock.patch('toolium.toolium_driver.driver')
    def test_get_element(self, driver):
        LoginPageObject().username.element()

        self.assertEqual(driver.find_element.mock_calls, [mock.call(By.NAME, 'username')])

    @mock.patch('toolium.toolium_driver.driver')
    def test_get_element_with_parent(self, driver):
        driver.find_element.return_value = mock_element
        web_element = LoginPageObject().password.element()

        self.assertEqual(web_element, child_element)
        self.assertEqual(driver.find_element.mock_calls, [mock.call(By.NAME, 'username')])
        self.assertEqual(mock_element.find_element.mock_calls, [mock.call(By.ID, 'password')])

    @mock.patch('toolium.toolium_driver.driver')
    def test_get_element_init_page(self, driver):
        RegisterPageObject().language.element()

        self.assertEqual(driver.find_element.mock_calls, [mock.call(By.ID, 'language')])

    @mock.patch('toolium.toolium_driver.driver')
    def test_get_element_with_parent_webelement(self, driver):
        web_element = RegisterPageObject().email.element()

        self.assertEqual(web_element, child_element)
        self.assertEqual(driver.find_element.mock_calls, [])
        self.assertEqual(mock_element.find_element.mock_calls, [mock.call(By.ID, 'email')])

    @mock.patch('toolium.toolium_driver.driver')
    def test_get_element_in_test(self, driver):
        PageElement(By.NAME, 'username').element()

        self.assertEqual(driver.find_element.mock_calls, [mock.call(By.NAME, 'username')])
