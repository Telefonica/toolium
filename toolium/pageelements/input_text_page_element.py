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

from toolium.pageelements.page_element import PageElement


class InputText(PageElement):
    @property
    def text(self):
        """Get the element text value

        :returns: element text value
        """
        return self.web_element.get_attribute("value")

    @text.setter
    def text(self, value):
        """Set value on the element

        :param value: value to be set
        """
        if self.driver_wrapper.is_ios_test() and not self.driver_wrapper.is_web_test():
            self.web_element.set_value(value)
        elif self.shadowroot:
            self.driver.execute_script('return document.querySelector("%s")'
                                       '.shadowRoot.querySelector("%s")'
                                       '.value = "%s"' % (self.shadowroot, self.locator[1], value))
        else:
            self.web_element.send_keys(value)

    def clear(self):
        """Clear the element value

        :returns: page element instance
        """
        self.web_element.clear()
        return self
