# -*- coding: utf-8 -*-
"""
Copyright 2022 Telefónica Investigación y Desarrollo, S.A.U.
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

import logging
import time
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait


class WaitUtils(object):
    def __init__(self, driver_wrapper=None):
        """Initialize WaitUtils instance

        :param driver_wrapper: driver wrapper instance
        """
        from toolium.driver_wrappers_pool import DriverWrappersPool
        self.driver_wrapper = driver_wrapper if driver_wrapper else DriverWrappersPool.get_default_wrapper()
        # Configure logger
        self.logger = logging.getLogger(__name__)

    def get_implicitly_wait(self):
        """Read implicitly timeout from configuration properties"""
        return self.driver_wrapper.config.get_optional('Driver', 'implicitly_wait')

    def set_implicitly_wait(self):
        """Read implicitly timeout from configuration properties and configure driver implicitly wait"""
        implicitly_wait = self.get_implicitly_wait()
        if implicitly_wait:
            self.driver_wrapper.driver.implicitly_wait(implicitly_wait)

    def get_explicitly_wait(self):
        """Read explicitly timeout from configuration properties

        :returns: configured explicitly timeout (default timeout 10 seconds)
        """
        return int(self.driver_wrapper.config.get_optional('Driver', 'explicitly_wait', '10'))

    def _expected_condition_find_element(self, element):
        """Tries to find the element, but does not thrown an exception if the element is not found

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :returns: the web element if it has been found or False
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        """
        from toolium.pageelements.page_element import PageElement
        web_element = False
        try:
            if isinstance(element, PageElement):
                # Use _find_web_element() instead of web_element to avoid logging error message
                element._web_element = None
                element._find_web_element()
                web_element = element._web_element
            elif isinstance(element, tuple):
                web_element = self.driver_wrapper.driver.find_element(*element)
        except NoSuchElementException:
            pass
        return web_element

    def _expected_condition_find_element_visible(self, element):
        """Tries to find the element and checks that it is visible, but does not thrown an exception if the element is
            not found

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :returns: the web element if it is visible or False
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        """
        web_element = self._expected_condition_find_element(element)
        try:
            return web_element if web_element and web_element.is_displayed() else False
        except StaleElementReferenceException:
            return False

    def _expected_condition_find_element_not_visible(self, element):
        """Tries to find the element and checks that it is visible, but does not thrown an exception if the element is
            not found

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :returns: True if the web element is not found or it is not visible
        """
        web_element = self._expected_condition_find_element(element)
        try:
            return True if not web_element or not web_element.is_displayed() else False
        except StaleElementReferenceException:
            return False

    def _expected_condition_find_first_element(self, elements):
        """Try to find sequentially the elements of the list and return the first element found

        :param elements: list of PageElements or element locators as a tuple (locator_type, locator_value) to be found
                         sequentially
        :returns: first element found or None
        :rtype: toolium.pageelements.PageElement or tuple
        """
        from toolium.pageelements.page_element import PageElement
        element_found = None
        for element in elements:
            try:
                if isinstance(element, PageElement):
                    element._web_element = None
                    element._find_web_element()
                else:
                    self.driver_wrapper.driver.find_element(*element)
                element_found = element
                break
            except (NoSuchElementException, TypeError):
                pass
        return element_found

    def _expected_condition_find_element_clickable(self, element):
        """Tries to find the element and checks that it is clickable, but does not thrown an exception if the element
            is not found

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :returns: the web element if it is clickable or False
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        """
        web_element = self._expected_condition_find_element_visible(element)
        try:
            return web_element if web_element and web_element.is_enabled() else False
        except StaleElementReferenceException:
            return False

    def _expected_condition_find_element_stopped(self, element_times):
        """Tries to find the element and checks that it has stopped moving, but does not thrown an exception if the
            element is not found

        :param element_times: Tuple with 2 items where:
            [0] element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
            [1] times: number of iterations checking the element's location that must be the same for all of them
            in order to considering the element has stopped
        :returns: the web element if it is clickable or False
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        """
        element, times = element_times
        web_element = self._expected_condition_find_element(element)
        try:
            locations_list = [tuple(web_element.location.values()) for i in range(int(times)) if not time.sleep(0.001)]
            return web_element if set(locations_list) == set(locations_list[-1:]) else False
        except StaleElementReferenceException:
            return False

    def _expected_condition_find_element_containing_text(self, element_text_pair):
        """Tries to find the element and checks that it contains the specified text, but does not thrown an exception if
            the element is not found

        :param element_text_pair: Tuple with 2 items where:
            [0] element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
            [1] text: text to be contained into the element
        :returns: the web element if it contains the text or False
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        """
        element, text = element_text_pair
        web_element = self._expected_condition_find_element(element)
        try:
            return web_element if web_element and text in web_element.text else False
        except StaleElementReferenceException:
            return False

    def _expected_condition_find_element_not_containing_text(self, element_text_pair):
        """Tries to find the element and checks that it does not contain the specified text,
            but does not thrown an exception if the element is found

        :param element_text_pair: Tuple with 2 items where:
            [0] element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
            [1] text: text to not be contained into the element
        :returns: the web element if it does not contain the text or False
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        """
        element, text = element_text_pair
        web_element = self._expected_condition_find_element(element)
        try:
            return web_element if web_element and text not in web_element.text else False
        except StaleElementReferenceException:
            return False

    def _expected_condition_value_in_element_attribute(self, element_attribute_value):
        """Tries to find the element and checks that it contains the requested attribute with the expected value,
           but does not thrown an exception if the element is not found

        :param element_attribute_value: Tuple with 3 items where:
            [0] element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
            [1] attribute: element's attribute where to check its value
            [2] value: expected value for the element's attribute
        :returns: the web element if it contains the expected value for the requested attribute or False
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        """
        element, attribute, value = element_attribute_value
        web_element = self._expected_condition_find_element(element)
        try:
            return web_element if web_element and web_element.get_attribute(attribute) == value else False
        except StaleElementReferenceException:
            return False

    def _expected_condition_ajax_request_completed(self, element):
        """Load all ajax request

        :returns: the ajax request is completed
        """
        return self.driver_wrapper.driver.execute_script("return jQuery.active == 0")

    def _wait_until(self, condition_method, condition_input, timeout=None):
        """
        Common method to wait until condition met

        :param condition_method: method to check the condition
        :param condition_input: parameter that will be passed to the condition method
        :param timeout: max time to wait
        :returns: condition method response
        """
        # Remove implicitly wait timeout
        implicitly_wait = self.get_implicitly_wait()
        if implicitly_wait != 0:
            self.driver_wrapper.driver.implicitly_wait(0)
        try:
            # Get explicitly wait timeout
            timeout = timeout if timeout else self.get_explicitly_wait()
            # Wait for condition
            condition_response = WebDriverWait(self.driver_wrapper.driver, timeout).until(
                lambda s: condition_method(condition_input))
        finally:
            # Restore implicitly wait timeout from properties
            if implicitly_wait != 0:
                self.set_implicitly_wait()
        return condition_response

    def wait_until_element_present(self, element, timeout=None):
        """Search element and wait until it is found

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :param timeout: max time to wait
        :returns: the web element if it is present
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        :raises TimeoutException: If the element is not found after the timeout
        """
        return self._wait_until(self._expected_condition_find_element, element, timeout)

    def wait_until_element_visible(self, element, timeout=None):
        """Search element and wait until it is visible

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :param timeout: max time to wait
        :returns: the web element if it is visible
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        :raises TimeoutException: If the element is still not visible after the timeout
        """
        return self._wait_until(self._expected_condition_find_element_visible, element, timeout)

    def wait_until_element_not_visible(self, element, timeout=None):
        """Search element and wait until it is not visible

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :param timeout: max time to wait
        :returns: the web element if it exists but is not visible
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        :raises TimeoutException: If the element is still visible after the timeout
        """
        return self._wait_until(self._expected_condition_find_element_not_visible, element, timeout)

    def wait_until_first_element_is_found(self, elements, timeout=None):
        """Search list of elements and wait until one of them is found

        :param elements: list of PageElements or element locators as a tuple (locator_type, locator_value) to be found
                         sequentially
        :param timeout: max time to wait
        :returns: first element found
        :rtype: toolium.pageelements.PageElement or tuple
        :raises TimeoutException: If no element in the list is found after the timeout
        """
        try:
            return self._wait_until(self._expected_condition_find_first_element, elements, timeout)
        except TimeoutException as exception:
            msg = 'None of the page elements has been found after %s seconds'
            timeout = timeout if timeout else self.get_explicitly_wait()
            self.logger.error(msg, timeout)
            exception.msg += "\n  {}".format(msg % timeout)
            raise exception

    def wait_until_element_clickable(self, element, timeout=None):
        """Search element and wait until it is clickable

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :param timeout: max time to wait
        :returns: the web element if it is clickable
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        :raises TimeoutException: If the element is not clickable after the timeout
        """
        return self._wait_until(self._expected_condition_find_element_clickable, element, timeout)

    def wait_until_element_stops(self, element, times=1000, timeout=None):
        """Search element and wait until it has stopped moving

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :param times: number of iterations checking the element's location that must be the same for all of them
         in order to considering the element has stopped
        :returns: the web element if the element is stopped
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        :raises TimeoutException: If the element does not stop after the timeout
        """
        return self._wait_until(self._expected_condition_find_element_stopped, (element, times), timeout)

    def wait_until_element_contains_text(self, element, text, timeout=None):
        """Search element and wait until it contains the expected text

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :param text: text expected to be contained into the element
        :param timeout: max time to wait
        :returns: the web element if it contains the expected text
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        :raises TimeoutException: If the element does not contain the expected text after the timeout
        """
        return self._wait_until(self._expected_condition_find_element_containing_text, (element, text), timeout)

    def wait_until_element_not_contain_text(self, element, text, timeout=None):
        """Search element and wait until it does not contain the expected text

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :param text: text expected to be contained into the element
        :param timeout: max time to wait
        :returns: the web element if it does not contain the given text
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        :raises TimeoutException: If the element contains the expected text after the timeout
        """
        return self._wait_until(self._expected_condition_find_element_not_containing_text, (element, text), timeout)

    def wait_until_element_attribute_is(self, element, attribute, value, timeout=None):
        """Search element and wait until the requested attribute contains the expected value

        :param element: PageElement or element locator as a tuple (locator_type, locator_value) to be found
        :param attribute: attribute belonging to the element
        :param value: expected value for the attribute of the element
        :param timeout: max time to wait
        :returns: the web element if the element's attribute contains the expected value
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        :raises TimeoutException: If the element's attribute does not contain the expected value after the timeout
        """
        return self._wait_until(self._expected_condition_value_in_element_attribute, (element, attribute, value),
                                timeout)

    def wait_until_ajax_request_completed(self, timeout=None):
        """
        Wait for all ajax requests completed
        :param timeout: max time to wait
        """
        return self._wait_until(self._expected_condition_ajax_request_completed, None, timeout)
