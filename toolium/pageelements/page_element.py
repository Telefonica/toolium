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

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By

from toolium.driver_wrapper import DriverWrappersPool
from toolium.pageobjects.common_object import CommonObject
from toolium.visual_test import VisualTest


class PageElement(CommonObject):
    """Class to represent a web or a mobile page element

    :type locator: (selenium.webdriver.common.by.By or appium.webdriver.common.mobileby.MobileBy, str)
    :type parent: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
                  or toolium.pageelements.PageElement
                  or (selenium.webdriver.common.by.By or appium.webdriver.common.mobileby.MobileBy, str)
    """
    native_context = "NATIVE_APP"
    webview_context_prefix = "WEBVIEW"

    def __init__(self, by, value, parent=None, order=None, wait=False, shadowroot=None, webview=False,
                 webview_context_selection_callback=None, webview_csc_args=None):
        """Initialize the PageElement object with the given locator components.

        If parent is not None, find_element will be performed over it, instead of
        using the driver's method, so it can find nested elements.

        :param by: locator type
        :param value: locator value
        :param parent: parent element (WebElement, PageElement or locator tuple)
        :param order: index value if the locator returns more than one element
        :param wait: True if the page element must be loaded in wait_until_loaded method of the container page object
        :param shadowroot: CSS SELECTOR of JS element where shadowroot tag appears
        :param webview: True if the element is in a mobile webiew
        :param webview_context_selection_callback: method provided to select the desired webview context if
        automatic_context_selection is enabled. Must return a tuple (context, window_handle) for android, and a context
        for ios
        :param webview_csc_args: arguments list for webview_context_selection_callback
        """
        super(PageElement, self).__init__()
        self.locator = (by, value)  #: tuple with locator type and locator value
        self.parent = parent  #: element from which to find actual elements
        self.order = order  #: index value if the locator returns more than one element
        self.wait = wait  #: True if it must be loaded in wait_until_loaded method of the container page object
        self.shadowroot = shadowroot  #: CSS SELECTOR of the shadowroot for encapsulated element
        self.webview = webview  #: True if element is in a mobile webview
        self.webview_context_selection_callback = webview_context_selection_callback  #: callback for selection of the
        # webview context with automatic_context_selection
        self.webview_csc_args = webview_csc_args  #: arguments list for the context selection callback method
        self.driver_wrapper = DriverWrappersPool.get_default_wrapper()  #: driver wrapper instance
        self.reset_object(self.driver_wrapper)

    def reset_object(self, driver_wrapper=None):
        """Reset each page element object

        :param driver_wrapper: driver wrapper instance
        """
        if driver_wrapper:
            self.driver_wrapper = driver_wrapper
        self._web_element = None

    @property
    def web_element(self):
        """Find WebElement using element locator

        :returns: web element object
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        """
        try:
            self._find_web_element()
        except NoSuchElementException as exception:
            parent_msg = " and parent locator '{}'".format(self.parent) if self.parent else ''
            msg = "Page element of type '%s' with locator %s%s not found"
            self.logger.error(msg, type(self).__name__, self.locator, parent_msg)
            exception.msg += "\n  {}".format(msg % (type(self).__name__, self.locator, parent_msg))
            raise exception
        return self._web_element

    def _find_web_element(self):
        """Find WebElement using element locator and save it in _web_element attribute"""
        if not self._web_element or not self.driver_wrapper.config.getboolean_optional('Driver', 'save_web_element'):
            # check context for mobile webviews
            if self.driver_wrapper.config.getboolean_optional('Driver', 'automatic_context_selection'):
                if self.driver_wrapper.is_android_test():
                    self._android_automatic_context_selection()
                elif self.driver_wrapper.is_ios_test():
                    self._ios_automatic_context_selection()

            # If the element is encapsulated we use the shadowroot tag in yaml (eg. Shadowroot: root_element_name)
            if self.shadowroot:
                if self.locator[0] != By.CSS_SELECTOR:
                    raise Exception('Locator type should be CSS_SELECTOR using shadowroot but found: '
                                    '%s' % self.locator[0])
                # querySelector only support CSS SELECTOR locator
                self._web_element = self.driver.execute_script('return document.querySelector("%s").shadowRoot.'
                                                               'querySelector("%s")' % (self.shadowroot,
                                                                                        self.locator[1]))
            else:
                # Element will be finded from parent element or from driver
                base = self.utils.get_web_element(self.parent) if self.parent else self.driver
                # Find elements and get the correct index or find a single element
                self._web_element = base.find_elements(*self.locator)[self.order] if self.order else base.find_element(
                    *self.locator)

    def _android_automatic_context_selection(self):
        """Change context selection depending if the element is a webview for android devices"""
        # we choose the appPackage webview context, and select the first window returned by mobile: getContexts
        if self.webview:
            context = None
            window_handle = None
            if self.webview_context_selection_callback:
                context, window_handle = self.webview_context_selection_callback(*self.webview_csc_args)
            else:
                app_web_context = "{}_{}".format(PageElement.webview_context_prefix, self.driver.capabilities['appPackage'])
                contexts = self.driver.execute_script('mobile: getContexts')
                context_dict = next(
                    (item for item in contexts if 'webviewName' in item and item['webviewName'] == app_web_context),
                    None)
                if context_dict:
                    context = app_web_context
                    window_handle = 'CDwindow-{}'.format(context_dict['pages'][0]['id'])
            if context:
                if self.driver.context != context:
                    self.driver.switch_to.context(context)
                if self.driver.current_window_handle != window_handle:
                    self.driver.switch_to.window(window_handle)
            else:
                raise KeyError("WEBVIEW context not found")
        else:
            if self.driver.context != PageElement.native_context:
                self.driver.switch_to.context(PageElement.native_context)

    def _ios_automatic_context_selection(self):
        """Change context selection depending if the element is a webview for ios devices"""
        # we choose the last webview context returned by mobile: getContexts for the bundleid
        if self.webview:
            if self.webview_context_selection_callback:
                context_id = self.webview_context_selection_callback(*self.webview_csc_args)
            else:
                contexts = self.driver.execute_script('mobile: getContexts')
                context_id = next(
                    (item['id'] for item in reversed(contexts) if
                     'bundleId' in item and item['bundleId'] == self.driver.capabilities['bundleId']),
                    None)
            if context_id:
                if self.driver.context != context_id:
                    self.driver.switch_to.context(context_id)
            else:
                raise KeyError("WEBVIEW context not found")
        else:
            if self.driver.context != PageElement.native_context:
                self.driver.switch_to.context(PageElement.native_context)

    def scroll_element_into_view(self):
        """Scroll element into view

        :returns: page element instance
        """
        x = self.web_element.location['x']
        y = self.web_element.location['y']
        self.driver.execute_script('window.scrollTo({0}, {1})'.format(x, y))
        return self

    def is_present(self):
        """Find element and return True if it is present

        :returns: True if element is located
        """
        try:
            # Use _find_web_element() instead of web_element to avoid logging error message
            self._web_element = None
            self._find_web_element()
            return True
        except NoSuchElementException:
            return False

    def is_visible(self):
        """Find element and return True if it is visible

        :returns: True if element is visible
        """
        return self.is_present() and self.web_element.is_displayed()

    def wait_until_visible(self, timeout=None):
        """Search element and wait until it is visible

        :param timeout: max time to wait
        :returns: page element instance
        """
        try:
            self.utils.wait_until_element_visible(self, timeout)
        except TimeoutException as exception:
            parent_msg = " and parent locator '{}'".format(self.parent) if self.parent else ''
            msg = "Page element of type '%s' with locator %s%s not found or is not visible after %s seconds"
            timeout = timeout if timeout else self.utils.get_explicitly_wait()
            self.logger.error(msg, type(self).__name__, self.locator, parent_msg, timeout)
            exception.msg += "\n  {}".format(msg % (type(self).__name__, self.locator, parent_msg, timeout))
            raise exception
        return self

    def wait_until_not_visible(self, timeout=None):
        """Search element and wait until it is not visible

        :param timeout: max time to wait
        :returns: page element instance
        """
        try:
            self.utils.wait_until_element_not_visible(self, timeout)
        except TimeoutException as exception:
            parent_msg = " and parent locator '{}'".format(self.parent) if self.parent else ''
            msg = "Page element of type '%s' with locator %s%s is still visible after %s seconds"
            timeout = timeout if timeout else self.utils.get_explicitly_wait()
            self.logger.error(msg, type(self).__name__, self.locator, parent_msg, timeout)
            exception.msg += "\n  {}".format(msg % (type(self).__name__, self.locator, parent_msg, timeout))
            raise exception
        return self

    def wait_until_clickable(self, timeout=None):
        """Search element and wait until it is clickable

        :param timeout: max time to wait
        :returns: page element instance
        """
        try:
            self.utils.wait_until_element_clickable(self, timeout)
        except TimeoutException as exception:
            parent_msg = " and parent locator '{}'".format(self.parent) if self.parent else ''
            msg = "Page element of type '%s' with locator %s%s not found or is not clickable after %s seconds"
            timeout = timeout if timeout else self.utils.get_explicitly_wait()
            self.logger.error(msg, type(self).__name__, self.locator, parent_msg, timeout)
            exception.msg += "\n  {}".format(msg % (type(self).__name__, self.locator, parent_msg, timeout))
            raise exception
        return self

    def assert_screenshot(self, filename, threshold=0, exclude_elements=[], force=False):
        """Assert that a screenshot of the element is the same as a screenshot on disk, within a given threshold.

        :param filename: the filename for the screenshot, which will be appended with ``.png``
        :param threshold: percentage threshold for triggering a test failure (value between 0 and 1)
        :param exclude_elements: list of WebElements, PageElements or element locators as a tuple (locator_type,
                                 locator_value) that must be excluded from the assertion
        :param force: if True, the screenshot is compared even if visual testing is disabled by configuration
        """
        VisualTest(self.driver_wrapper, force).assert_screenshot(self.web_element, filename, self.__class__.__name__,
                                                                 threshold, exclude_elements)

    def get_attribute(self, name):
        """Get the given attribute or property of the element

        :param name: name of the attribute/property to retrieve
        :returns: attribute value
        """
        return self.web_element.get_attribute(name)

    def set_focus(self):
        """
        Set the focus over the element

        :returns: page element instance
        """
        self.utils.focus_element(self.web_element)
        return self
