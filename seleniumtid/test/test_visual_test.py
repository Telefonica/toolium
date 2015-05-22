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
        # Configure visual path
        cls.root_path = os.path.dirname(os.path.realpath(__file__))
        cls.visual_path = os.path.join(cls.root_path, 'dist', 'visualtests')
        if os.path.exists(cls.visual_path):
            shutil.rmtree(cls.visual_path)

        # Configure common properties
        os.environ["Files_properties"] = os.path.join(cls.root_path, 'conf', 'properties.cfg')
        os.environ["VisualTests_enabled"] = 'true'
        os.environ["VisualTests_fail"] = 'false'
        os.environ["VisualTests_engine"] = 'pil'

        # Create html report in dist/visualtests
        selenium_driver.output_directory = os.path.join(cls.root_path, 'dist', 'visualtests')

        # Get file paths
        cls.file_v1 = os.path.join(cls.root_path, 'resources', 'register_v1.png')
        cls.file_v2 = os.path.join(cls.root_path, 'resources', 'register_v2.png')
        cls.file_v1_small = os.path.join(cls.root_path, 'resources', 'register_v1_small.png')

    def setUp(self):
        # Configure properties
        selenium_driver.configure()

    def tearDown(self):
        # Remove previous conf properties
        selenium_driver.conf_properties_files = None

    @classmethod
    def tearDownClass(cls):
        # Remove environment properties
        try:
            del os.environ["Files_properties"]
            del os.environ["VisualTests_enabled"]
            del os.environ["VisualTests_fail"]
            del os.environ["VisualTests_engine"]
        except KeyError:
            pass

    def test_compare_files_equals(self):
        message = VisualTest()._compare_files(self._testMethodName, self.file_v1, self.file_v1, 0)
        self.assertIsNone(message)

    def test_compare_files_diff(self):
        message = VisualTest()._compare_files(self._testMethodName, self.file_v1, self.file_v2, 0)
        self.assertIn('by a distance of 522.65', message)

    def test_compare_files_diff_fail(self):
        selenium_driver.config.set('VisualTests', 'fail', 'true')

        with self.assertRaises(AssertionError):
            VisualTest()._compare_files(self._testMethodName, self.file_v1, self.file_v2, 0)

    def test_compare_files_size(self):
        message = VisualTest()._compare_files(self._testMethodName, self.file_v1, self.file_v1_small, 0)
        # PIL returns an empty error
        self.assertEquals('', message)

    def test_compare_files_size_fail(self):
        selenium_driver.config.set('VisualTests', 'fail', 'true')

        with self.assertRaises(AssertionError):
            VisualTest()._compare_files(self._testMethodName, self.file_v1, self.file_v1_small, 0)

    def test_compare_files_perceptualdiff_equals(self):
        selenium_driver.config.set('VisualTests', 'engine', 'perceptualdiff')

        message = VisualTest()._compare_files(self._testMethodName, self.file_v1, self.file_v1, 0)
        self.assertIsNone(message)

    def test_compare_files_perceptualdiff_diff(self):
        selenium_driver.config.set('VisualTests', 'engine', 'perceptualdiff')
        visual = VisualTest()

        # Copy image file
        image_file = os.path.join(visual.output_directory, self._testMethodName + '.png')
        shutil.copyfile(self.file_v1, image_file)

        message = visual._compare_files(self._testMethodName, image_file, self.file_v2, 0)
        self.assertIn('3114 pixels are different', message)

    def test_compare_files_perceptualdiff_diff_fail(self):
        selenium_driver.config.set('VisualTests', 'engine', 'perceptualdiff')
        selenium_driver.config.set('VisualTests', 'fail', 'true')
        visual = VisualTest()

        # Copy image file
        image_file = os.path.join(visual.output_directory, self._testMethodName + '.png')
        shutil.copyfile(self.file_v1, image_file)

        with self.assertRaises(AssertionError):
            visual._compare_files(self._testMethodName, image_file, self.file_v2, 0)

    def test_compare_files_perceptualdiff_size(self):
        selenium_driver.config.set('VisualTests', 'engine', 'perceptualdiff')

        message = VisualTest()._compare_files(self._testMethodName, self.file_v1, self.file_v1_small, 0)
        self.assertIn('Image dimensions do not match', message)

    def test_compare_files_perceptualdiff_size_fail(self):
        selenium_driver.config.set('VisualTests', 'engine', 'perceptualdiff')
        selenium_driver.config.set('VisualTests', 'fail', 'true')

        with self.assertRaises(AssertionError):
            VisualTest()._compare_files(self._testMethodName, self.file_v1, self.file_v1_small, 0)

    def test_get_html_row(self):
        row = VisualTest()._get_html_row('diff', self._testMethodName, self.file_v1, self.file_v2)
        print row

    def test_add_to_report(self):
        visual = VisualTest()
        visual._add_to_report('diff', self._testMethodName, self.file_v1, self.file_v2, 'diff')
        visual._add_to_report('equal', self._testMethodName, self.file_v1, self.file_v1)
        visual._add_to_report('baseline', self._testMethodName, self.file_v1, None, 'Added to baseline')

    def test_exclude_element_from_image_file(self):
        selenium_driver.config.set('VisualTests', 'engine', 'perceptualdiff')
        visual = VisualTest()

        # Copy image file
        image_file = os.path.join(visual.output_directory, self._testMethodName + '.png')
        shutil.copyfile(self.file_v1, image_file)

        class FakeElement():
            def get_dimensions(self):
                return {'left': 250, 'top': 40, 'width': 300, 'height': 40}
        elements = [FakeElement()]

        visual.exclude_elements_from_image_file(image_file, elements)

        # Compare only to add image to visual report
        message = visual._compare_files(self._testMethodName, image_file, image_file, 0)
        self.assertIsNone(message)

    def test_exclude_element_from_image_file_outofimage(self):
        visual = VisualTest()

        # Copy image file
        image_file = os.path.join(visual.output_directory, self._testMethodName + '.png')
        shutil.copyfile(self.file_v1, image_file)

        class FakeElement():
            def get_dimensions(self):
                return {'left': 250, 'top': 40, 'width': 1500, 'height': 500}
        elements = [FakeElement()]

        visual.exclude_elements_from_image_file(image_file, elements)

        # Compare only to add image to visual report
        message = visual._compare_files(self._testMethodName, image_file, image_file, 0)
        self.assertIsNone(message)
