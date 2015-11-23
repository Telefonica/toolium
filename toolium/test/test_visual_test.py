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
from needle.engines.perceptualdiff_engine import Engine as PerceptualEngine


# from needle.engines.imagemagick_engine import Engine as MagickEngine
from needle.engines.pil_engine import Engine as PilEngine
from selenium.webdriver.remote.webelement import WebElement
import mock

from selenium.webdriver.common.by import By

from toolium.visual_test import VisualTest
from toolium import toolium_driver


class VisualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Get file paths
        cls.root_path = os.path.dirname(os.path.realpath(__file__))
        cls.file_v1 = os.path.join(cls.root_path, 'resources', 'register.png')
        cls.file_v2 = os.path.join(cls.root_path, 'resources', 'register_v2.png')
        cls.file_small = os.path.join(cls.root_path, 'resources', 'register_small.png')
        cls.file_ios = os.path.join(cls.root_path, 'resources', 'ios.png')

    def setUp(self):
        # Remove previous visual path
        visual_path = os.path.join(self.root_path, 'output', 'visualtests')
        if os.path.exists(visual_path):
            shutil.rmtree(visual_path)

        # Remove previous driver instance and conf properties
        toolium_driver._instance = None
        toolium_driver.config_properties_filenames = None

        # Configure properties
        toolium_driver.configure(tc_config_directory=os.path.join(self.root_path, 'conf'),
                                 tc_config_prop_filenames='properties.cfg',
                                 tc_output_directory=os.path.join(self.root_path, 'output'))
        toolium_driver.config.set('VisualTests', 'enabled', 'true')

        # Create a new VisualTest instance
        self.visual = VisualTest()
        toolium_driver.visual_number = 1

    @classmethod
    def tearDownClass(cls):
        # Remove visual path
        visual_path = os.path.join(cls.root_path, 'output', 'visualtests')
        if os.path.exists(visual_path):
            shutil.rmtree(visual_path)

        # Remove driver instance and conf properties
        toolium_driver._instance = None
        toolium_driver.config_properties_filenames = None

    @mock.patch('toolium.toolium_driver.driver')
    def test_no_enabled(self, driver):
        toolium_driver.config.set('VisualTests', 'enabled', 'false')
        VisualTest().assertScreenshot(None, filename='screenshot_full', file_suffix='screenshot_suffix')
        driver.save_screenshot.assert_not_called()

    def test_engine_pil(self):
        visual = VisualTest()
        self.assertIsInstance(visual.engine, PilEngine)

    def test_engine_perceptual(self):
        toolium_driver.config.set('VisualTests', 'engine', 'perceptualdiff')
        visual = VisualTest()
        self.assertIsInstance(visual.engine, PerceptualEngine)

    # def test_engine_magick(self):
    #    toolium_driver.config.set('VisualTests', 'engine', 'imagemagick')
    #    visual = VisualTest()
    #    self.assertIsInstance(visual.engine, MagickEngine)

    def test_engine_empty(self):
        toolium_driver.config.set('VisualTests', 'engine', '')
        visual = VisualTest()
        self.assertIsInstance(visual.engine, PilEngine)

    def test_engine_unknown(self):
        toolium_driver.config.set('VisualTests', 'engine', 'unknown')
        visual = VisualTest()
        self.assertIsInstance(visual.engine, PilEngine)

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
            # Python 3
            assertRegex = self.assertRegex
        except AttributeError:
            # Python 2.7
            assertRegex = self.assertRegexpMatches
        assertRegex(row, expected_row)

    def assertImage(self, img, img_name, expected_image_filename):
        """Save img in an image file and compare with the expected image

        :param img: image object
        :param img_name: temporary filename
        :param expected_image_filename: filename of the expected image
        """
        # Save result image in output folder
        result_file = os.path.join(self.visual.output_directory, img_name + '.png')
        img.save(result_file)

        # Output image and expected image must be equals
        expected_image = os.path.join(self.root_path, 'resources', expected_image_filename + '.png')
        PilEngine().assertSameFiles(result_file, expected_image, 0)

    def test_crop_element(self):
        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        # Resize image
        img = Image.open(self.file_v1)
        img = self.visual.crop_element(img, element)

        # Assert output image
        self.assertImage(img, self._testMethodName, 'register_cropped_element')

    @mock.patch('toolium.toolium_driver.driver')
    def test_mobile_resize(self, driver):
        # Configure driver mock
        driver.get_window_size.return_value = {'width': 375, 'height': 667}
        toolium_driver.config.set('Browser', 'browser', 'iphone')

        # Resize image
        img = Image.open(self.file_ios)
        img = self.visual.mobile_resize(img)

        # Assert output image
        self.assertImage(img, self._testMethodName, 'ios_resized')

    @mock.patch('toolium.toolium_driver.driver')
    def test_mobile_no_resize(self, driver):
        # Configure driver mock
        driver.get_window_size.return_value = {'width': 750, 'height': 1334}
        toolium_driver.config.set('Browser', 'browser', 'iphone')

        # Resize image
        orig_img = Image.open(self.file_ios)
        img = self.visual.mobile_resize(orig_img)

        # Assert that image object has not been modified
        self.assertEqual(orig_img, img)

    def test_exclude_elements(self):
        # Create elements mock
        elements = [get_mock_element(x=250, y=40, height=40, width=300),
                    get_mock_element(x=250, y=90, height=20, width=100)]
        img = Image.open(self.file_v1)

        # Exclude elements
        img = self.visual.exclude_elements(img, elements)

        # Assert output image
        self.assertImage(img, self._testMethodName, 'register_exclude')

    def test_exclude_element_outofimage(self):
        # Create elements mock
        elements = [get_mock_element(x=250, y=40, height=40, width=1500)]
        img = Image.open(self.file_v1)

        # Exclude elements
        img = self.visual.exclude_elements(img, elements)

        # Assert output image
        self.assertImage(img, self._testMethodName, 'register_exclude_outofimage')

    def test_exclude_no_elements(self):
        # Exclude no elements
        img = Image.open(self.file_v1)
        img = self.visual.exclude_elements(img, [])

        # Assert output image
        self.assertImage(img, self._testMethodName, 'register')

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

    @mock.patch('toolium.toolium_driver.driver')
    def test_get_element_locator(self, driver):
        # Configure driver mock
        driver.find_element.return_value = 'mock_element'
        element_locator = (By.ID, 'element_id')

        # Get element and assert response
        element = self.visual.get_element(element_locator)
        self.assertEqual('mock_element', element)
        driver.find_element.assert_called_with(*element_locator)

    @mock.patch('toolium.toolium_driver.driver')
    def test_assert_screenshot_full_and_save_baseline(self, driver):
        # Configure driver mock
        def copy_file_side_effect(output_file):
            shutil.copyfile(self.file_v1, output_file)

        driver.save_screenshot.side_effect = copy_file_side_effect

        # Assert screenshot
        self.visual.assertScreenshot(None, filename='screenshot_full', file_suffix='screenshot_suffix')
        output_file = os.path.join(self.visual.output_directory, '01_screenshot_full__screenshot_suffix.png')
        driver.save_screenshot.assert_called_with(output_file)

        # Output image and new baseline image must be equals
        baseline_file = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'firefox',
                                     'screenshot_full.png')
        PilEngine().assertSameFiles(output_file, baseline_file, 0)

    @mock.patch('toolium.toolium_driver.driver')
    def test_assert_screenshot_element_and_save_baseline(self, driver):
        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        # Configure driver mock
        with open(self.file_v1, "rb") as f:
            image_data = f.read()
        driver.get_screenshot_as_png.return_value = image_data

        # Assert screenshot
        self.visual.assertScreenshot(element, filename='screenshot_elem', file_suffix='screenshot_suffix')
        driver.get_screenshot_as_png.assert_called_with()

        # Check cropped image
        expected_image = os.path.join(self.root_path, 'resources', 'register_cropped_element.png')
        output_file = os.path.join(self.visual.output_directory, '01_screenshot_elem__screenshot_suffix.png')
        PilEngine().assertSameFiles(output_file, expected_image, 0)

        # Output image and new baseline image must be equals
        baseline_file = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'firefox',
                                     'screenshot_elem.png')
        PilEngine().assertSameFiles(output_file, baseline_file, 0)

    @mock.patch('toolium.toolium_driver.driver')
    def test_assert_screenshot_full_and_compare(self, driver):
        # Configure driver mock
        def copy_file_side_effect(output_file):
            shutil.copyfile(self.file_v1, output_file)

        driver.save_screenshot.side_effect = copy_file_side_effect

        # Add baseline image
        baseline_file = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'firefox',
                                     'screenshot_full.png')
        shutil.copyfile(self.file_v1, baseline_file)

        # Assert screenshot
        self.visual.assertScreenshot(None, filename='screenshot_full', file_suffix='screenshot_suffix')
        output_file = os.path.join(self.visual.output_directory, '01_screenshot_full__screenshot_suffix.png')
        driver.save_screenshot.assert_called_with(output_file)

    @mock.patch('toolium.toolium_driver.driver')
    def test_assert_screenshot_element_and_compare(self, driver):
        # Add baseline image
        expected_image = os.path.join(self.root_path, 'resources', 'register_cropped_element.png')
        baseline_file = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'firefox',
                                     'screenshot_elem.png')
        shutil.copyfile(expected_image, baseline_file)

        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        # Configure driver mock
        with open(self.file_v1, "rb") as f:
            image_data = f.read()
        driver.get_screenshot_as_png.return_value = image_data

        # Assert screenshot
        self.visual.assertScreenshot(element, filename='screenshot_elem', file_suffix='screenshot_suffix')
        driver.get_screenshot_as_png.assert_called_with()

    @mock.patch('toolium.toolium_driver.driver')
    def test_assert_screenshot_mobile_resize_and_exclude(self, driver):
        # Create elements mock
        elements = [get_mock_element(x=0, y=0, height=24, width=375)]

        # Configure driver mock
        with open(self.file_ios, "rb") as f:
            image_data = f.read()
        driver.get_screenshot_as_png.return_value = image_data
        driver.get_window_size.return_value = {'width': 375, 'height': 667}
        toolium_driver.config.set('Browser', 'browser', 'iphone')

        # Assert screenshot
        self.visual.assertScreenshot(None, filename='screenshot_ios', file_suffix='screenshot_suffix',
                                     exclude_elements=elements)
        driver.get_screenshot_as_png.assert_called_with()

        # Check cropped image
        expected_image = os.path.join(self.root_path, 'resources', 'ios_excluded.png')
        output_file = os.path.join(self.visual.output_directory, '01_screenshot_ios__screenshot_suffix.png')
        PilEngine().assertSameFiles(output_file, expected_image, 0)

        # Output image and new baseline image must be equals
        baseline_file = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'firefox',
                                     'screenshot_ios.png')
        PilEngine().assertSameFiles(output_file, baseline_file, 0)

    @mock.patch('toolium.toolium_driver.driver')
    def test_assert_screenshot_mobile_web_resize_and_exclude(self, driver):
        # Create elements mock
        form_element = get_mock_element(x=0, y=0, height=559, width=375)
        exclude_elements = [get_mock_element(x=15, y=296.515625, height=32, width=345)]

        # Configure driver mock
        file_ios_web = os.path.join(self.root_path, 'resources', 'ios_web.png')
        with open(file_ios_web, "rb") as f:
            image_data = f.read()
        driver.get_screenshot_as_png.return_value = image_data
        driver.get_window_size.return_value = {'width': 375, 'height': 667}
        toolium_driver.config.set('Browser', 'browser', 'iphone')
        toolium_driver.config.set('AppiumCapabilities', 'browserName', 'safari')

        # Assert screenshot
        self.visual.assertScreenshot(form_element, filename='screenshot_ios_web', file_suffix='screenshot_suffix',
                                     exclude_elements=exclude_elements)
        driver.get_screenshot_as_png.assert_called_with()

        # Check cropped image
        expected_image = os.path.join(self.root_path, 'resources', 'ios_web_exclude.png')
        output_file = os.path.join(self.visual.output_directory, '01_screenshot_ios_web__screenshot_suffix.png')
        PilEngine().assertSameFiles(output_file, expected_image, 0)

        # Output image and new baseline image must be equals
        baseline_file = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'firefox',
                                     'screenshot_ios_web.png')
        PilEngine().assertSameFiles(output_file, baseline_file, 0)


@mock.patch('selenium.webdriver.remote.webelement.WebElement', spec=True)
def get_mock_element(WebElement, x, y, height, width):
    element = WebElement.return_value
    element.location = {'x': x, 'y': y}
    element.size = {'height': height, 'width': width}
    return element
