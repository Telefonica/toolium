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

from seleniumtid.pageelements.page_element import PageElement


class InputText(PageElement):
    @property
    def text(self):
        return self.element().get_attribute("value")

    @text.setter
    def text(self, value):
        self.element().send_keys(value)
