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

import logging

from toolium.driver_wrapper import DriverWrappersPool
from toolium.pageobjects.common_object import CommonObject


class PageObject(CommonObject):
    """Class to represent a web page or a mobile application screen

    :type app_strings: str
    :type logger: logging.Logger
    """

    def __init__(self, driver_wrapper=None):
        """Initialize page object properties and update their page elements

        :param driver_wrapper: driver wrapper instance
        """
        self.logger = logging.getLogger(__name__)  #: logger instance
        self.driver_wrapper = driver_wrapper if driver_wrapper else DriverWrappersPool.get_default_wrapper()  #: driver wrapper instance
        self.app_strings = None  #:mobile application strings
        self.init_page_elements()
        self._update_page_elements()

    def reset_object(self):
        """Reset web element object in all page elements"""
        self.app_strings = self.driver_wrapper.app_strings
        for element in self._get_page_elements():
            element.reset_object()

    def init_page_elements(self):
        """Method to initialize page elements

        This method can be overridden to define page elements and will be called in page object __init__
        """
        pass

    def _get_page_elements(self):
        """Return page elements and page objects of this page object

        :returns: list of page elements and page objects
        """
        from toolium.pageelements.page_element import PageElement
        from toolium.pageelements.page_elements import PageElements
        page_elements = []
        for attribute, value in list(self.__dict__.items()) + list(self.__class__.__dict__.items()):
            if attribute != 'parent' and (isinstance(value, PageElement) or isinstance(value, PageElements)
                                          or isinstance(value, PageObject)):
                page_elements.append(value)
        return page_elements

    def _update_page_elements(self, parent=None):
        """Copy driver and utils instances to all page elements of this page object

        :param parent: parent element (WebElement, PageElement or locator tuple)
        """
        for element in self._get_page_elements():
            element.set_driver_wrapper(self.driver_wrapper)
            if parent and not isinstance(element, PageObject) and not element.parent:
                # If this instance is a group and element is not a page object, update element parent
                element.parent = parent
            if isinstance(element, PageObject):
                # If element is a page object, update also its page elements
                element._update_page_elements(parent)
