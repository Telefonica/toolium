# -*- coding: utf-8 -*-
"""
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

import logging

from toolium.driver_wrapper import DriverWrappersPool
from toolium.pageelements.page_element import PageElement
from toolium.pageobjects.page_object import PageObject


class Group(PageObject, PageElement):
    def __init__(self, by, value, parent=None, driver_wrapper=None, order=None, wait=False, webview=False,
                 webview_context_selection_callback=None, webview_csc_args=None):
        """Initialize the Group object with the given locator components.

        If parent is not None, find_elements will be performed over it, instead of
        using the driver's method, so it can find nested elements.

        :param by: locator type
        :param value: locator value
        :param parent: parent element (WebElement, PageElement or locator tuple)
        :param driver_wrapper: driver wrapper instance
        :param order: index value if the locator returns more than one element
        :param wait: True if the page element must be loaded in wait_until_loaded method of the container page object
        :param shadowroot: CSS SELECTOR of JS element where shadowroot tag appears
        :param webview: True if the element is in a mobile webiew
        :param webview_context_selection_callback: method provided to select the desired webview context if
        automatic_context_selection is enabled. Must return a tuple (context, window_handle) for android, and a context
        for ios
        :param webview_csc_args: arguments list for webview_context_selection_callback
        """
        self.logger = logging.getLogger(__name__)  #: logger instance
        self.locator = (by, value)  #: tuple with locator type and locator value
        self.parent = parent  #: element from which to find actual elements
        self.order = order  #: index value if the locator returns more than one element
        self.wait = wait  #: True if it must be loaded in wait_until_loaded method of the container page object
        self.webview = webview  #: True if element is in a mobile webview
        self.webview_context_selection_callback = webview_context_selection_callback  #: callback for selection of the
        # webview context with automatic_context_selection
        self.webview_csc_args = webview_csc_args  #: arguments list for the context selection callback method
        self.shadowroot = None  #: Not implemented for Group yet
        self.driver_wrapper = driver_wrapper if driver_wrapper else \
            DriverWrappersPool.get_default_wrapper()  #: driver wrapper instance
        self.init_page_elements()
        self.reset_object(self.driver_wrapper)

    def reset_object(self, driver_wrapper=None):
        """Reset each page element object

        :param driver_wrapper: driver wrapper instance
        """
        from toolium.pageelements.page_elements import PageElements
        if driver_wrapper:
            self.driver_wrapper = driver_wrapper
        self._web_element = None
        for element in self._get_page_elements():
            element.reset_object(driver_wrapper)
            if isinstance(element, (PageElement, PageElements)) and element.parent is None:
                # If element is not a page object and it has not a custom parent, update element parent
                element.parent = self
