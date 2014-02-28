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


class PageElement(object):
    locator = (None, None)

    def __get__(self, obj, cls=None):
        pass

    def __set__(self, obj, val):
        pass

    def __delete__(self, obj):
        pass
