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

from toolium.pageelements.button_page_element import Button


class Checkbox(Button):
    @property
    def text(self):
        """Get the element text value

        :returns: element text value
        """
        return self.web_element.get_attribute("value")

    def is_selected(self):
        """Returns whether the element is selected

        :returns: true whether the element is selected
        """
        return self.web_element.is_selected()

    def check(self):
        """Select the checkbox

        :returns: page element instance
        """
        if not self.is_selected():
            self.web_element.click()
        return self

    def uncheck(self):
        """Uncheck the checkbox

        :returns: page element instance
        """
        if self.is_selected():
            self.web_element.click()
        return self
