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
import shutil

import sys
from seleniumtid.visual_test import VisualTest
from seleniumtid import selenium_driver


class VisualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_path = os.path.dirname(os.path.realpath(__file__))
        cls.visual_path = os.path.join(cls.root_path, 'dist', 'visualtests')
        if os.path.exists(cls.visual_path):
            shutil.rmtree(cls.visual_path)

    def setUp(self):
        # Configure common properties
        os.environ["Files_properties"] = os.path.join(self.root_path, 'conf', 'properties.cfg')
        os.environ["Server_visualtests_enabled"] = 'true'
        os.environ["Server_visualtests_fail"] = 'false'
        os.environ["Server_visualtests_engine"] = 'pil'
        selenium_driver.configure()
        # Create html report in dist/visualtests
        selenium_driver.output_directory = os.path.join(self.root_path, 'dist', 'visualtests')

        # Get file paths
        self.file_v1 = os.path.join(self.root_path, 'resources', 'register_v1.png')
        self.file_v2 = os.path.join(self.root_path, 'resources', 'register_v2.png')
        self.file_v1_small = os.path.join(self.root_path, 'resources', 'register_v1_small.png')
        VisualTests.file_diff = os.path.join(self.root_path, 'resources', 'register_v1.diff.png')
        VisualTests.file_diff_backup = os.path.join(self.root_path, 'resources', 'register_v1_backup.diff.png')

        # Move previous diff file
        if os.path.exists(self.file_diff):
            if not os.path.exists(self.file_diff_backup):
                os.rename(self.file_diff, self.file_diff_backup)
            else:
                os.remove(self.file_diff)

    def tearDown(self):
        # Remove previous conf properties
        selenium_driver.conf_properties_files = None

    @classmethod
    def tearDownClass(cls):
        # Restore first diff file
        if os.path.exists(cls.file_diff_backup):
            os.rename(cls.file_diff_backup, cls.file_diff)

    def get_method_name(self):
        """Get caller method name

        :returns: caller method name
        """
        return sys._getframe(1).f_code.co_name

    def test_compare_files_equals(self):
        message = VisualTest()._compare_files(self.get_method_name(), self.file_v1, self.file_v1, 0)
        self.assertIsNone(message)

    def test_compare_files_diff(self):
        message = VisualTest()._compare_files(self.get_method_name(), self.file_v1, self.file_v2, 0)
        self.assertIn('by a distance of 522.65', message)

    def test_compare_files_diff_fail(self):
        selenium_driver.config.set('Server', 'visualtests_fail', 'true')

        with self.assertRaises(AssertionError):
            VisualTest()._compare_files(self.get_method_name(), self.file_v1, self.file_v2, 0)

    def test_compare_files_size(self):
        message = VisualTest()._compare_files(self.get_method_name(), self.file_v1, self.file_v1_small, 0)
        # PIL returns an empty error
        self.assertEquals('', message)

    def test_compare_files_size_fail(self):
        selenium_driver.config.set('Server', 'visualtests_fail', 'true')

        with self.assertRaises(AssertionError):
            VisualTest()._compare_files(self.get_method_name(), self.file_v1, self.file_v1_small, 0)

    def test_compare_files_perceptualdiff_equals(self):
        selenium_driver.config.set('Server', 'visualtests_engine', 'perceptualdiff')

        message = VisualTest()._compare_files(self.get_method_name(), self.file_v1, self.file_v1, 0)
        self.assertIsNone(message)

    def test_compare_files_perceptualdiff_diff(self):
        selenium_driver.config.set('Server', 'visualtests_engine', 'perceptualdiff')

        visual = VisualTest()
        message = visual._compare_files(self.get_method_name(), self.file_v1, self.file_v2, 0)
        self.assertIn('3114 pixels are different', message)

    def test_compare_files_perceptualdiff_diff_fail(self):
        selenium_driver.config.set('Server', 'visualtests_engine', 'perceptualdiff')
        selenium_driver.config.set('Server', 'visualtests_fail', 'true')

        with self.assertRaises(AssertionError):
            VisualTest()._compare_files(self.get_method_name(), self.file_v1, self.file_v2, 0)

    def test_compare_files_perceptualdiff_size(self):
        selenium_driver.config.set('Server', 'visualtests_engine', 'perceptualdiff')

        message = VisualTest()._compare_files(self.get_method_name(), self.file_v1, self.file_v1_small, 0)
        self.assertIn('Image dimensions do not match', message)

    def test_compare_files_perceptualdiff_size_fail(self):
        selenium_driver.config.set('Server', 'visualtests_engine', 'perceptualdiff')
        selenium_driver.config.set('Server', 'visualtests_fail', 'true')

        with self.assertRaises(AssertionError):
            VisualTest()._compare_files(self.get_method_name(), self.file_v1, self.file_v1_small, 0)

    def test_get_html_row(self):
        row = VisualTest()._get_html_row(self.get_method_name(), self.file_v1, self.file_v2)
        print row

    def test_add_to_report(self):
        visual = VisualTest()
        visual._add_to_report(self.get_method_name(), self.file_v1, self.file_v2, 'first')
        visual._add_to_report(self.get_method_name(), self.file_v1, self.file_v2, 'second')
