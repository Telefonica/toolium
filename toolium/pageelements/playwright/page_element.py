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

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from toolium.pageelements import PageElement as BasePageElement


class PageElement(BasePageElement):
    @property
    async def web_element(self):
        """Find WebElement using element locator

        :returns: web element object
        :rtype: selenium.webdriver.remote.webelement.WebElement or appium.webdriver.webelement.WebElement
        """
        try:
            await self._find_web_element()
        except NoSuchElementException as exception:
            parent_msg = f" and parent locator {self.parent_locator_str()}" if self.parent else ''
            msg = "Page element of type '%s' with locator %s%s not found"
            self.logger.error(msg, type(self).__name__, self.locator, parent_msg)
            exception.msg += "\n  {}".format(msg % (type(self).__name__, self.locator, parent_msg))
            raise exception
        return self._web_element

    async def _find_web_element(self):
        """Find WebElement using element locator and save it in _web_element attribute"""
        if not self._web_element or not self.driver_wrapper.config.getboolean_optional('Driver', 'save_web_element'):
            # Element will be searched from parent element or from driver
            # TODO: search from parent element
            # base = self.utils.get_web_element(self.parent) if self.parent else self.driver
            self._web_element = self.driver.locator(self.playwright_locator)

    @property
    def playwright_locator(self):
        """Return playwright locator converted from toolium/selenium locator

        :returns: playwright locator
        """
        # TODO: Implement playwright locator conversion
        if self.locator[0] == By.ID:
            prefix = '#'
        elif self.locator[0] == By.XPATH:
            prefix = 'xpath='
        else:
            raise ValueError(f'Locator type not supported to be converted to playwright: {self.locator[0]}')
        playwright_locator = f'{prefix}{self.locator[1]}'
        return playwright_locator
