# -*- coding: utf-8 -*-

u"""
(c) Copyright 2015 Telefónica, I+D. Printed in Spain (Europe). All Rights
Reserved.

The copyright to the software program(s) is property of Telefónica I+D.
The program(s) may be used and or copied only with the express written
consent of Telefónica I+D or in accordance with the terms and conditions
stipulated in the agreement/contract under which the program(s) have
been supplied.
"""

import unittest
import os

from seleniumtid.visual_test import VisualTest


class VisualTests(unittest.TestCase):
    def test_get_row(self):
        row = VisualTest().get_html_row('test1', 'C:\\output\\file1.png', 'C:\\baseline\\file1.png')
        print row

    def test_add_to_report(self):
        visual = VisualTest()
        visual.output_directory = 'dist'
        visual.report_name = 'VisualTest.html'
        if not os.path.exists(visual.output_directory):
            os.makedirs(visual.output_directory)
        visual.copy_template()
        visual.add_to_report('test1', 'C:\\output\\file1.png', 'C:\\baseline\\file1.png')
        visual.add_to_report('test2', 'C:\\output\\file2.png', 'C:\\baseline\\file2.png')
