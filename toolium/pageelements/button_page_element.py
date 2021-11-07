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

from selenium.common.exceptions import StaleElementReferenceException
from toolium.pageelements.page_element import PageElement


class Button(PageElement):
    @property
    def text(self):
        """Get the element text value

        :returns: element text value
        """
        try:
            return self.web_element.text
        except StaleElementReferenceException:
            # Retry if element has changed
            return self.web_element.text

    def click(self):
        """Click the element

        :returns: page element instance
        """
        try:
            self.wait_until_clickable().web_element.click()
        except StaleElementReferenceException:
            # Retry if element has changed
            self.web_element.click()
        return self
