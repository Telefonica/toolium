# -*- coding: utf-8 -*-
"""
Copyright 2024 Telefónica Innovación Digital, S.L.
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

from toolium.pageelements.playwright.page_element import PageElement


class InputText(PageElement):
    # TODO: convert to async get_text
    @property
    def text(self):
        """Get the element text value

        :returns: element text value
        """
        if self.driver_wrapper.is_web_test() or self.webview:
            return self.web_element.get_attribute("value")
        elif self.driver_wrapper.is_ios_test():
            return self.web_element.get_attribute("label")
        elif self.driver_wrapper.is_android_test():
            return self.web_element.get_attribute("text")

    async def fill(self, value):
        """Set value on the element

        :param value: value to be set
        """
        await (await self.web_element).fill(value)

    # TODO: convert to async method
    def clear(self):
        """Clear the element value

        :returns: page element instance
        """
        self.web_element.clear()
        return self

    async def click(self):
        """Click the element

        :returns: page element instance
        """
        await (await self.web_element).click()
        return self

    # TODO: convert to async method
    def set_focus(self):
        """
        Set the focus over the element and click on the InputField

        :returns: page element instance
        """
        self.utils.focus_element(self.web_element, click=True)
        return self
