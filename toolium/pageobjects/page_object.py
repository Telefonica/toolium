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

from toolium.driver_wrapper import DriverWrappersPool
from toolium.pageobjects.common_object import CommonObject


class PageObject(CommonObject):
    """Class to represent a web page or a mobile application screen

    :type app_strings: str
    """

    def __init__(self, driver_wrapper=None, wait=False):
        """Initialize page object properties and update their page elements

        :param driver_wrapper: driver wrapper instance
        :param wait: True if the page object must be loaded in wait_until_loaded method of the container page object
        """
        super(PageObject, self).__init__()
        self.wait = wait  #: True if it must be loaded in wait_until_loaded method of the container page object
        self.driver_wrapper = driver_wrapper if driver_wrapper else \
            DriverWrappersPool.get_default_wrapper()  #: driver wrapper instance
        self.init_page_elements()
        self.reset_object(self.driver_wrapper)

    def reset_object(self, driver_wrapper=None):
        """Reset each page element object

        :param driver_wrapper: driver wrapper instance
        """
        if driver_wrapper:
            self.driver_wrapper = driver_wrapper
        self.app_strings = self.driver_wrapper.app_strings  #: mobile application strings
        for element in self._get_page_elements():
            element.reset_object(driver_wrapper)

    def init_page_elements(self):
        """Method to initialize page elements

        This method can be overridden to define page elements and will be called in page object __init__
        """
        pass

    def _get_page_elements(self):
        """Return page elements and page objects of this page object

        :returns: list of page elements and page objects
        """
        page_elements = []
        for attribute, value in list(self.__dict__.items()) + list(self.__class__.__dict__.items()):
            if attribute != 'parent' and isinstance(value, CommonObject):
                page_elements.append(value)
        return page_elements

    def wait_until_loaded(self, timeout=None):
        """Wait until page object is loaded
        Search all page elements configured with wait=True

        :param timeout: max time to wait
        :returns: this page object instance
        """
        for element in self._get_page_elements():
            if hasattr(element, 'wait') and element.wait:
                from toolium.pageelements.page_element import PageElement
                if isinstance(element, PageElement):
                    # Pageelement and Group
                    element.wait_until_visible(timeout)
                if isinstance(element, PageObject):
                    # PageObject and Group
                    element.wait_until_loaded(timeout)
        return self
