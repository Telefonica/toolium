# -*- coding: utf-8 -*-

u"""
(c) Copyright 2014 Telefónica, I+D. Printed in Spain (Europe). All Rights
Reserved.

The copyright to the software program(s) is property of Telefónica I+D.
The program(s) may be used and or copied only with the express written
consent of Telefónica I+D or in accordance with the terms and conditions
stipulated in the agreement/contract under which the program(s) have
been supplied.
"""

from toolium.pageelements.page_element import PageElement
from toolium import selenium_driver


class InputText(PageElement):
    @property
    def text(self):
        return self.element().get_attribute("value")

    @text.setter
    def text(self, value):
        if selenium_driver.is_ios_test() and not selenium_driver.is_web_test():
            self.element().set_value(value)
        else:
            self.element().send_keys(value)
