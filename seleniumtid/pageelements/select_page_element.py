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
from selenium.webdriver.support.ui import Select as SeleniumSelect


class Select(PageElement):
    @property
    def option(self):
        return self.select_object.first_selected_option.text

    @option.setter
    def option(self, value):
        self.select_object.select_by_visible_text(value)

    @property
    def select_object(self):
        return SeleniumSelect(self.element())
