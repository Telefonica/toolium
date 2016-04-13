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

import unittest

import mock
from nose.tools import assert_equal, assert_is_instance, assert_is
from selenium.webdriver.common.by import By

from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.pageelements import PageElement, PageElements
from toolium.pageobjects.page_object import PageObject

child_elements = ['child_element_1', 'child_element_2']
other_child_elements = ['child_element_3', 'child_element_4']
mock_element = None


@mock.patch('selenium.webdriver.remote.webelement.WebElement', spec=True)
def get_mock_element(WebElement):
    web_element = WebElement.return_value
    web_element.find_elements.return_value = child_elements
    return web_element


class LoginPageObject(PageObject):
    inputs = PageElements(By.XPATH, '//input')
    links = PageElements(By.XPATH, '//a')
    inputs_parent = PageElements(By.XPATH, '//input', (By.ID, 'parent'))


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

    def test_get_web_elements(self):
        LoginPageObject().inputs.web_elements

        assert_equal(self.driver_wrapper.driver.find_elements.mock_calls, [mock.call(By.XPATH, '//input')])

    def test_get_web_elements_with_parent_locator(self):
        self.driver_wrapper.driver.find_element.return_value = mock_element
        web_elements = LoginPageObject().inputs_parent.web_elements

        assert_equal(web_elements, child_elements)
        assert_equal(self.driver_wrapper.driver.find_element.mock_calls, [mock.call(By.ID, 'parent')])
        assert_equal(mock_element.find_elements.mock_calls, [mock.call(By.XPATH, '//input')])

    def test_get_page_elements(self):
        self.driver_wrapper.driver.find_elements.return_value = child_elements
        page_elements = LoginPageObject().inputs.page_elements

        # Check that find_elements has been called just one time
        assert_equal(self.driver_wrapper.driver.find_elements.mock_calls, [mock.call(By.XPATH, '//input')])
        assert_equal(self.driver_wrapper.driver.find_element.mock_calls, [])

        # Check that the response is a list of 2 PageElement with the expected web element
        assert_equal(len(page_elements), 2)
        assert_is_instance(page_elements[0], PageElement)
        assert_equal(page_elements[0]._web_element, child_elements[0])
        assert_is_instance(page_elements[1], PageElement)
        assert_equal(page_elements[1]._web_element, child_elements[1])

    def test_get_page_elements_and_web_elements(self):
        self.driver_wrapper.driver.find_elements.return_value = child_elements
        inputs = LoginPageObject().inputs
        page_elements = inputs.page_elements
        web_elements = inputs.web_elements

        # Check that find_elements has been called just one time
        assert_equal(self.driver_wrapper.driver.find_elements.mock_calls, [mock.call(By.XPATH, '//input')])
        assert_equal(self.driver_wrapper.driver.find_element.mock_calls, [])

        # Check that the response is a list of 2 PageElement with the expected web element
        assert_equal(len(page_elements), 2)
        assert_is_instance(page_elements[0], PageElement)
        assert_equal(page_elements[0]._web_element, child_elements[0])
        assert_is_instance(page_elements[1], PageElement)
        assert_equal(page_elements[1]._web_element, child_elements[1])

        # Check that web_elements are the same elements as page_element._web_element
        assert_is(web_elements[0], page_elements[0]._web_element)
        assert_is(web_elements[1], page_elements[1]._web_element)

    def test_multiple_page_elements(self):
        self.driver_wrapper.driver.find_elements.side_effect = [child_elements, other_child_elements]
        input_page_elements = LoginPageObject().inputs.page_elements
        links_page_elements = LoginPageObject().links.page_elements

        # Check that the response is a list of 2 PageElement with the expected web element
        assert_equal(len(input_page_elements), 2)
        assert_is_instance(input_page_elements[0], PageElement)
        assert_equal(input_page_elements[0]._web_element, child_elements[0])
        assert_is_instance(input_page_elements[1], PageElement)
        assert_equal(input_page_elements[1]._web_element, child_elements[1])

        # Check that the response is a list of 2 PageElement with the expected web element
        assert_equal(len(links_page_elements), 2)
        assert_is_instance(links_page_elements[0], PageElement)
        assert_equal(links_page_elements[0]._web_element, other_child_elements[0])
        assert_is_instance(links_page_elements[1], PageElement)
        assert_equal(links_page_elements[1]._web_element, other_child_elements[1])

    def test_reset_object(self):
        self.driver_wrapper.driver.find_elements.side_effect = [child_elements, other_child_elements]
        login_page = LoginPageObject()
        login_page.inputs.web_elements
        login_page.links.web_elements

        # Check that web elements are filled
        assert_equal(len(login_page.inputs._web_elements), 2)
        assert_equal(len(login_page.links._web_elements), 2)

        login_page.inputs.reset_object()

        # Check that only username is reset
        assert_equal(len(login_page.inputs._web_elements), 0)
        assert_equal(len(login_page.links._web_elements), 2)
