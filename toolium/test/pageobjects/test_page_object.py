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
from nose.tools import assert_equal, assert_is_not_none, assert_is_none
from selenium.webdriver.common.by import By

from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.pageelements import PageElement
from toolium.pageobjects.page_object import PageObject

child_element = 'child_element'
mock_element = None


@mock.patch('selenium.webdriver.remote.webelement.WebElement', spec=True)
def get_mock_element(WebElement):
    web_element = WebElement.return_value
    web_element.find_element.return_value = child_element
    return web_element


class RegisterPageObject(PageObject):
    username = PageElement(By.XPATH, '//input[0]')
    password = PageElement(By.ID, 'password', username)

    def init_page_elements(self):
        self.language = PageElement(By.ID, 'language')
        self.email = PageElement(By.ID, 'email', mock_element)
        self.address = PageElement(By.ID, 'address', (By.ID, 'parent'))
        self.menu = MenuPageObject()


class MenuPageObject(PageObject):
    register = PageElement(By.ID, 'register')

    def init_page_elements(self):
        self.logo = PageElement(By.ID, 'image')


class TestPageObject(unittest.TestCase):
    def setUp(self):
        """Create a new mock element and a new driver before each test"""
        global mock_element
        mock_element = get_mock_element()

        # Reset wrappers pool values
        DriverWrappersPool._empty_pool()
        DriverWrappersPool.output_directory = ''
        DriverWrapper.config_properties_filenames = None

        # Create a new wrapper
        self.driver_wrapper = DriverWrappersPool.get_default_wrapper()
        self.driver_wrapper.driver = mock.MagicMock()

    def test_driver_wrapper(self):
        page_object = RegisterPageObject()

        # Check that the page object and its page elements have the same driver wrapper
        assert_equal(page_object.driver_wrapper, self.driver_wrapper)
        assert_equal(page_object.username.driver_wrapper, self.driver_wrapper)
        assert_equal(page_object.password.driver_wrapper, self.driver_wrapper)
        assert_equal(page_object.language.driver_wrapper, self.driver_wrapper)
        assert_equal(page_object.email.driver_wrapper, self.driver_wrapper)
        assert_equal(page_object.address.driver_wrapper, self.driver_wrapper)

        # Check that the child page object and its page elements have the same driver wrapper
        assert_equal(page_object.menu.driver_wrapper, self.driver_wrapper)
        assert_equal(page_object.menu.register.driver_wrapper, self.driver_wrapper)
        assert_equal(page_object.menu.logo.driver_wrapper, self.driver_wrapper)

    def test_two_driver_wrappers(self):
        page_object = RegisterPageObject()
        second_driver_wrapper = DriverWrapper()
        second_page_object = RegisterPageObject(second_driver_wrapper)

        # Check that the page object and its instance page elements have the same driver wrapper
        assert_equal(page_object.driver_wrapper, self.driver_wrapper)
        assert_equal(page_object.language.driver_wrapper, self.driver_wrapper)
        assert_equal(page_object.email.driver_wrapper, self.driver_wrapper)
        assert_equal(page_object.address.driver_wrapper, self.driver_wrapper)
        assert_equal(page_object.menu.driver_wrapper, self.driver_wrapper)
        assert_equal(page_object.menu.logo.driver_wrapper, self.driver_wrapper)

        # Check that the second page object and its instance page elements have the second driver wrapper
        assert_equal(second_page_object.driver_wrapper, second_driver_wrapper)
        assert_equal(second_page_object.language.driver_wrapper, second_driver_wrapper)
        assert_equal(second_page_object.email.driver_wrapper, second_driver_wrapper)
        assert_equal(second_page_object.address.driver_wrapper, second_driver_wrapper)
        assert_equal(second_page_object.menu.driver_wrapper, second_driver_wrapper)
        assert_equal(second_page_object.menu.logo.driver_wrapper, second_driver_wrapper)

        # Check that the class elements have the last driver wrapper
        # This kind of elements could not be used with multiple drivers
        assert_equal(page_object.username.driver_wrapper, second_driver_wrapper)
        assert_equal(page_object.password.driver_wrapper, second_driver_wrapper)
        assert_equal(page_object.menu.register.driver_wrapper, second_driver_wrapper)
        assert_equal(second_page_object.username.driver_wrapper, second_driver_wrapper)
        assert_equal(second_page_object.password.driver_wrapper, second_driver_wrapper)
        assert_equal(second_page_object.menu.register.driver_wrapper, second_driver_wrapper)

    def test_reset_web_elements(self):
        login_page = RegisterPageObject()
        # Serach page elements
        login_page.username.web_element
        login_page.password.web_element
        login_page.language.web_element
        login_page.email.web_element
        login_page.address.web_element
        login_page.menu.register.web_element
        login_page.menu.logo.web_element

        # Check that all page elements have a web element
        assert_is_not_none(login_page.username._web_element)
        assert_is_not_none(login_page.password._web_element)
        assert_is_not_none(login_page.language._web_element)
        assert_is_not_none(login_page.email._web_element)
        assert_is_not_none(login_page.address._web_element)
        assert_is_not_none(login_page.menu.register._web_element)
        assert_is_not_none(login_page.menu.logo._web_element)

        login_page.reset_web_elements()

        # Check that all page elements are reset
        assert_is_none(login_page.username._web_element)
        assert_is_none(login_page.password._web_element)
        assert_is_none(login_page.language._web_element)
        assert_is_none(login_page.email._web_element)
        assert_is_none(login_page.address._web_element)
        assert_is_none(login_page.menu.register._web_element)
        assert_is_none(login_page.menu.logo._web_element)
