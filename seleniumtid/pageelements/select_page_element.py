# -*- coding: utf-8 -*-
'''
(c) Copyright 2014 Telefonica, I+D. Printed in Spain (Europe). All Rights
Reserved.

The copyright to the software program(s) is property of Telefonica I+D.
The program(s) may be used and or copied only with the express written
consent of Telefonica I+D or in accordance with the terms and conditions
stipulated in the agreement/contract under which the program(s) have
been supplied.
'''
from seleniumtid.pageelements.page_element import PageElement
from selenium.webdriver.support.ui import Select


class SelectPageElement(PageElement):
    @property
    def option(self):
        return Select(self.element()).first_selected_option.text

    @option.setter
    def option(self, value):
        Select(self.element()).select_by_visible_text(value)
