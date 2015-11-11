# -*- coding: utf-8 -*-
u"""
Copyright 2015 Telefónica Investigación y Desarrollo, S.A.U.
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

import unittest
import os
import shutil

from PIL import Image
from needle.engines.pil_engine import Engine
from selenium.webdriver.remote.webelement import WebElement
import mock

from selenium.webdriver.common.by import By

from toolium.visual_test import VisualTest
from toolium import toolium_driver


class VisualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure common visual properties
        os.environ["VisualTests_enabled"] = 'true'
        os.environ["VisualTests_fail"] = 'false'
        os.environ["VisualTests_engine"] = 'pil'

        # Get file paths
        cls.root_path = os.path.dirname(os.path.realpath(__file__))
        cls.file_v1 = os.path.join(cls.root_path, 'resources', 'register.png')
        cls.file_v2 = os.path.join(cls.root_path, 'resources', 'register_v2.png')
        cls.file_small = os.path.join(cls.root_path, 'resources', 'register_small.png')

    def setUp(self):
        # Remove previous visual path
        visual_path = os.path.join(self.root_path, 'output', 'visualtests')
        if os.path.exists(visual_path):
            shutil.rmtree(visual_path)

        # Remove previous conf properties
        toolium_driver.config_properties_filenames = None

        # Configure properties
        toolium_driver.configure(tc_config_directory=os.path.join(self.root_path, 'conf'),
                                 tc_config_prop_filenames='properties.cfg',
                                 tc_output_directory=os.path.join(self.root_path, 'output'))

        # Create a new VisualTest instance
        self.visual = VisualTest()
        toolium_driver.visual_number = 1

    @classmethod
    def tearDownClass(cls):
        # Remove environment properties
        try:
            del os.environ["VisualTests_enabled"]
            del os.environ["VisualTests_fail"]
            del os.environ["VisualTests_engine"]
        except KeyError:
            pass

        # Remove visual path
        visual_path = os.path.join(cls.root_path, 'output', 'visualtests')
        if os.path.exists(visual_path):
            shutil.rmtree(visual_path)

        # Remove conf properties
        toolium_driver.config_properties_filenames = None

    def test_compare_files_equals(self):
        message = self.visual.compare_files(self._testMethodName, self.file_v1, self.file_v1, 0)
        self.assertIsNone(message)

    def test_compare_files_diff(self):
        message = self.visual.compare_files(self._testMethodName, self.file_v1, self.file_v2, 0)
        self.assertIn('by a distance of 522.65', message)

    def test_compare_files_diff_fail(self):
        toolium_driver.config.set('VisualTests', 'fail', 'true')

        with self.assertRaises(AssertionError):
            self.visual.compare_files(self._testMethodName, self.file_v1, self.file_v2, 0)

    def test_compare_files_size(self):
        message = self.visual.compare_files(self._testMethodName, self.file_v1, self.file_small, 0)
        # PIL returns an empty error
        self.assertEqual('', message)

    def test_compare_files_size_fail(self):
        toolium_driver.config.set('VisualTests', 'fail', 'true')

        with self.assertRaises(AssertionError):
            self.visual.compare_files(self._testMethodName, self.file_v1, self.file_small, 0)

    def test_get_html_row(self):
        expected_row = '<tr class=diff><td>test_get_html_row</td><td><img style="width: 100%" onclick="window.open\(this.src\)" src="file://.*register_v2.png"/></td></td><td><img style="width: 100%" onclick="window.open\(this.src\)" src="file://.*register.png"/></td></td><td></td></tr>'
        row = self.visual._get_html_row('diff', self._testMethodName, self.file_v1, self.file_v2)
        try:
            assertRegex = self.assertRegex
        except AttributeError:
            assertRegex = self.assertRegexpMatches
        assertRegex(row, expected_row)

    def test_exclude_elements(self):
        # Exclude element
        elements = [get_mock_element(x=250, y=40, height=40, width=300),
                    get_mock_element(x=250, y=90, height=20, width=100)]
        img = Image.open(self.file_v1)
        img = self.visual.exclude_elements(img, elements)

        # Save result image in output folder
        file_excluded = os.path.join(self.visual.output_directory, self._testMethodName + '.png')
        img.save(file_excluded)

        # Output image and expected image must be equals
        expected_image = os.path.join(self.root_path, 'resources', 'register_exclude.png')
        Engine().assertSameFiles(file_excluded, expected_image, 0)

    def test_exclude_element_outofimage(self):
        # Exclude element
        elements = [get_mock_element(x=250, y=40, height=40, width=1500)]
        img = Image.open(self.file_v1)
        img = self.visual.exclude_elements(img, elements)

        # Save result image in output folder
        file_excluded = os.path.join(self.visual.output_directory, self._testMethodName + '.png')
        img.save(file_excluded)

        # Output image and expected image must be equals
        expected_image = os.path.join(self.root_path, 'resources', 'register_exclude_outofimage.png')
        Engine().assertSameFiles(file_excluded, expected_image, 0)

    def test_exclude_no_elements(self):
        # Exclude element
        img = Image.open(self.file_v1)
        img = self.visual.exclude_elements(img, [])

        # Save result image in output folder
        file_excluded = os.path.join(self.visual.output_directory, self._testMethodName + '.png')
        img.save(file_excluded)

        # Output image and initial image must be equals
        Engine().assertSameFiles(file_excluded, self.file_v1, 0)

    def test_get_element_none(self):
        element = self.visual.get_element(None)
        self.assertIsNone(element)

    def test_get_element_webelement(self):
        web_element = WebElement(None, 1)
        element = self.visual.get_element(web_element)
        self.assertEqual(web_element, element)

    def test_get_element_pageelement(self):
        page_element = mock.MagicMock()
        page_element.element.return_value = 'mock_element'

        element = self.visual.get_element(page_element)
        self.assertEqual('mock_element', element)
        page_element.element.assert_called_with()

    def test_get_element_locator(self):
        toolium_driver.driver = mock.MagicMock()
        toolium_driver.driver.find_element.return_value = 'mock_element'
        element_locator = (By.ID, 'element_id')

        element = self.visual.get_element(element_locator)
        self.assertEqual('mock_element', element)
        toolium_driver.driver.find_element.assert_called_with(*element_locator)

    def test_assert_screenshot_full_and_save_baseline(self):
        # Create driver mock
        def copy_file_side_effect(output_file):
            shutil.copyfile(self.file_v1, output_file)

        toolium_driver.driver = mock.MagicMock()
        toolium_driver.driver.save_screenshot.side_effect = copy_file_side_effect

        self.visual.assertScreenshot(None, filename='screenshot_full', file_suffix='screenshot_suffix')
        output_file = os.path.join(self.visual.output_directory, '01_screenshot_full__screenshot_suffix.png')
        toolium_driver.driver.save_screenshot.assert_called_with(output_file)

        # Output image and new baseline image must be equals
        baseline_file = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'firefox-base',
                                     'screenshot_full.png')
        Engine().assertSameFiles(output_file, baseline_file, 0)

    def test_assert_screenshot_element_and_save_baseline(self):
        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        # Create driver mock
        toolium_driver.driver = mock.MagicMock()
        with open(self.file_v1, "rb") as f:
            image_data = f.read()
        toolium_driver.driver.get_screenshot_as_png.return_value = image_data

        self.visual.assertScreenshot(element, filename='screenshot_elem', file_suffix='screenshot_suffix')
        toolium_driver.driver.get_screenshot_as_png.assert_called_with()

        # Check cropped image
        expected_image = os.path.join(self.root_path, 'resources', 'register_cropped_element.png')
        output_file = os.path.join(self.visual.output_directory, '01_screenshot_elem__screenshot_suffix.png')
        Engine().assertSameFiles(output_file, expected_image, 0)

        # Output image and new baseline image must be equals
        baseline_file = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'firefox-base',
                                     'screenshot_elem.png')
        Engine().assertSameFiles(output_file, baseline_file, 0)

    def test_assert_screenshot_full_and_compare(self):
        # Create driver mock
        def copy_file_side_effect(output_file):
            shutil.copyfile(self.file_v1, output_file)

        toolium_driver.driver = mock.MagicMock()
        toolium_driver.driver.save_screenshot.side_effect = copy_file_side_effect

        # Add baseline image
        baseline_file = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'firefox-base',
                                     'screenshot_full.png')
        shutil.copyfile(self.file_v1, baseline_file)

        self.visual.assertScreenshot(None, filename='screenshot_full', file_suffix='screenshot_suffix')
        output_file = os.path.join(self.visual.output_directory, '01_screenshot_full__screenshot_suffix.png')
        toolium_driver.driver.save_screenshot.assert_called_with(output_file)

    def test_assert_screenshot_element_and_compare(self):
        # Add baseline image
        expected_image = os.path.join(self.root_path, 'resources', 'register_cropped_element.png')
        baseline_file = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'firefox-base',
                                     'screenshot_elem.png')
        shutil.copyfile(expected_image, baseline_file)

        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        # Create driver mock
        toolium_driver.driver = mock.MagicMock()
        with open(self.file_v1, "rb") as f:
            image_data = f.read()
        toolium_driver.driver.get_screenshot_as_png.return_value = image_data

        self.visual.assertScreenshot(element, filename='screenshot_elem', file_suffix='screenshot_suffix')
        toolium_driver.driver.get_screenshot_as_png.assert_called_with()


@mock.patch('selenium.webdriver.remote.webelement.WebElement', spec=True)
def get_mock_element(WebElement, x, y, height, width):
    element = WebElement.return_value
    element.location = {'x': x, 'y': y}
    element.size = {'height': height, 'width': width}
    return element
