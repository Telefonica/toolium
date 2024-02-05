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
import inspect
from typing import Any, List

from toolium.driver_wrapper import DriverWrappersPool
from toolium.pageelements.button_page_element import Button
from toolium.pageelements.checkbox_page_element import Checkbox
from toolium.pageelements.group_page_element import Group
from toolium.pageelements.input_radio_page_element import InputRadio
from toolium.pageelements.input_text_page_element import InputText
from toolium.pageelements.link_page_element import Link
from toolium.pageelements.page_element import PageElement
from toolium.pageelements.select_page_element import Select
from toolium.pageelements.text_page_element import Text
from toolium.pageobjects.common_object import CommonObject


class PageElements(CommonObject):
    """Class to represent multiple web or mobile page elements

    :type locator: (selenium.webdriver.common.by.By or appium.webdriver.common.mobileby.MobileBy, str)
    :type parent: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
                  or toolium.pageelements.PageElement
                  or (selenium.webdriver.common.by.By or appium.webdriver.common.mobileby.MobileBy, str)
    :type page_element_class: class
    """
    page_element_class = PageElement  #: class of page elements (PageElement, Button...)

    def __init__(self, by, value, parent=None, page_element_class=None, order=None, webview=False,
                 webview_context_selection_callback=None, webview_csc_args=None):
        """Initialize the PageElements object with the given locator components.

        If parent is not None, find_elements will be performed over it, instead of
        using the driver's method, so it can find nested elements.

        :param by: locator type
        :param value: locator value
        :param parent: parent element (WebElement, PageElement or locator tuple)
        :param order: index value if the locator returns more than one element
        :param page_element_class: class of page elements (PageElement, Button...)
        :param shadowroot: CSS SELECTOR of JS element where shadowroot tag appears
        :param webview: True if the element is in a mobile webiew
        :param webview_context_selection_callback: method provided to select the desired webview context if
        automatic_context_selection is enabled. Must return a tuple (context, window_handle) for android, and a context
        for ios
        :param webview_csc_args: arguments list for webview_context_selection_callback
        """
        super(PageElements, self).__init__()
        self.locator = (by, value)  #: tuple with locator type and locator value
        self.parent = parent  #: element from which to find actual elements
        self.order = order  #: index value if the locator returns more than one element
        self.shadowroot = None  #: Not implemented for PageElements yet
        self.driver_wrapper = DriverWrappersPool.get_default_wrapper()  #: driver wrapper instance
        # update instance element class or use PageElement class
        self.webview = webview
        self.webview_context_selection_callback = webview_context_selection_callback  #: callback for selection of the
        # webview context with automatic_context_selection
        self.webview_csc_args = webview_csc_args  #: arguments list for the context selection callback method
        if page_element_class:
            self.page_element_class = page_element_class
        self._page_elements = []
        self.reset_object(self.driver_wrapper)

    def reset_object(self, driver_wrapper=None):
        """Reset each page element object

        :param driver_wrapper: driver wrapper instance
        """
        if driver_wrapper:
            self.driver_wrapper = driver_wrapper
        for element in self._page_elements:
            element.reset_object(driver_wrapper)
        self._web_elements = []
        self._page_elements = []

    @property
    def web_elements(self):
        """Find multiple WebElements using element locator

        :returns: list of web element objects
        :rtype: list of selenium.webdriver.remote.webelement.WebElement
                or list of appium.webdriver.webelement.WebElement
        """
        if not self._web_elements or not self.config.getboolean_optional('Driver', 'save_web_element'):
            if self.parent:
                self._web_elements = self.utils.get_web_element(self.parent).find_elements(*self.locator)
            else:
                # check context for mobile webviews
                if self.driver_wrapper.config.getboolean_optional('Driver', 'automatic_context_selection'):
                    if self.driver_wrapper.is_android_test():
                        self._android_automatic_context_selection()
                    elif self.driver_wrapper.is_ios_test():
                        self._ios_automatic_context_selection()
                self._web_elements = self.driver.find_elements(*self.locator)
        return self._web_elements

    @property
    def page_elements(self) -> List[Any]:
        """Find multiple PageElement using element locator

        :returns: list of page element objects
        :rtype: list of toolium.pageelements.PageElement
        """
        if not self._page_elements or not self.config.getboolean_optional('Driver', 'save_web_element'):
            self._page_elements = []
            for order, web_element in enumerate(self.web_elements):
                # Create multiple PageElement with original locator and order
                # Optional parameters are passed only if they are defined in the PageElement constructor
                signature = inspect.signature(self.page_element_class.__init__)
                opt_names = ['parent', 'webview', 'webview_context_selection_callback', 'webview_csc_args']
                opt_params = {name: getattr(self, name) for name in opt_names if name in signature.parameters}
                if 'order' in signature.parameters:
                    opt_params['order'] = order
                page_element = self.page_element_class(self.locator[0], self.locator[1], **opt_params)
                page_element.reset_object(self.driver_wrapper)
                page_element._web_element = web_element
                self._page_elements.append(page_element)
        return self._page_elements

    def __len__(self):
        return len(self.page_elements)

    def __getitem__(self, i):
        return self.page_elements[i]

    def __iter__(self):
        return iter(self.page_elements)


class Buttons(PageElements):
    page_element_class = Button


class Checkboxes(PageElements):
    page_element_class = Checkbox


class InputRadios(PageElements):
    page_element_class = InputRadio


class InputTexts(PageElements):
    page_element_class = InputText


class Links(PageElements):
    page_element_class = Link


class Selects(PageElements):
    page_element_class = Select


class Texts(PageElements):
    page_element_class = Text


class Groups(PageElements):
    page_element_class = Group
