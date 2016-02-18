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

import os
import shutil
import unittest

# Python 2 and 3 compatibility
from six import assertRegex

from PIL import Image
from needle.engines.perceptualdiff_engine import Engine as PerceptualEngine

from nose.tools import assert_is_none, assert_equal, assert_in, assert_is_instance, assert_raises

# from needle.engines.imagemagick_engine import Engine as MagickEngine
from needle.engines.pil_engine import Engine as PilEngine
import mock
from toolium.visual_test import VisualTest
from toolium.config_files import ConfigFiles
from toolium.driver_wrapper import DriverWrappersPool
from toolium.driver_wrapper import DriverWrapper


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

        # Reset wrappers pool values
        DriverWrappersPool._empty_pool()
        DriverWrapper.config_properties_filenames = None

        # Create a new wrapper
        self.driver_wrapper = DriverWrappersPool.get_default_wrapper()
        self.driver_wrapper.driver = mock.MagicMock()

        # Configure properties
        config_files = ConfigFiles()
        config_files.set_config_directory(os.path.join(self.root_path, 'conf'))
        config_files.set_config_properties_filenames('properties.cfg')
        config_files.set_output_directory(os.path.join(self.root_path, 'output'))
        self.driver_wrapper.configure(tc_config_files=config_files)
        self.driver_wrapper.config.set('VisualTests', 'enabled', 'true')

        # Create a new VisualTest instance
        self.visual = VisualTest(self.driver_wrapper)

    @classmethod
    def tearDownClass(cls):
        # Remove visual path
        visual_path = os.path.join(cls.root_path, 'output', 'visualtests')
        if os.path.exists(visual_path):
            shutil.rmtree(visual_path)

        # Reset wrappers pool values
        DriverWrappersPool._empty_pool()
        DriverWrapper.config_properties_filenames = None

    def test_no_enabled(self):
        # Update conf and create a new VisualTest instance
        self.driver_wrapper.config.set('VisualTests', 'enabled', 'false')
        self.visual = VisualTest(self.driver_wrapper)

        self.visual.assert_screenshot(None, filename='screenshot_full', file_suffix='screenshot_suffix')
        self.driver_wrapper.driver.save_screenshot.assert_not_called()

    def test_engine_pil(self):
        assert_is_instance(self.visual.engine, PilEngine)

    def test_engine_perceptual(self):
        # Update conf and create a new VisualTest instance
        self.driver_wrapper.config.set('VisualTests', 'engine', 'perceptualdiff')
        self.visual = VisualTest(self.driver_wrapper)

        assert_is_instance(self.visual.engine, PerceptualEngine)

    # def test_engine_magick(self):
    #    self.driver_wrapper.config.set('VisualTests', 'engine', 'imagemagick')
    #    visual = VisualTest()
    #    assert_is_instance(visual.engine, MagickEngine)

    def test_engine_empty(self):
        # Update conf and create a new VisualTest instance
        self.driver_wrapper.config.set('VisualTests', 'engine', '')
        self.visual = VisualTest(self.driver_wrapper)

        assert_is_instance(self.visual.engine, PilEngine)

    def test_engine_unknown(self):
        # Update conf and create a new VisualTest instance
        self.driver_wrapper.config.set('VisualTests', 'engine', 'unknown')
        self.visual = VisualTest(self.driver_wrapper)

        assert_is_instance(self.visual.engine, PilEngine)

    def test_compare_files_equals(self):
        message = self.visual.compare_files(self._testMethodName, self.file_v1, self.file_v1, 0)
        assert_is_none(message)

    def test_compare_files_diff(self):
        message = self.visual.compare_files(self._testMethodName, self.file_v1, self.file_v2, 0)
        assert_in('by a distance of 522.65', message)

    def test_compare_files_diff_fail(self):
        # Update conf and create a new VisualTest instance
        self.driver_wrapper.config.set('VisualTests', 'fail', 'true')
        self.visual = VisualTest(self.driver_wrapper)

        with assert_raises(AssertionError):
            self.visual.compare_files(self._testMethodName, self.file_v1, self.file_v2, 0)

    def test_compare_files_size(self):
        message = self.visual.compare_files(self._testMethodName, self.file_v1, self.file_small, 0)
        # PIL returns an empty error
        assert_equal('', message)

    def test_compare_files_size_fail(self):
        # Update conf and create a new VisualTest instance
        self.driver_wrapper.config.set('VisualTests', 'fail', 'true')
        self.visual = VisualTest(self.driver_wrapper)

        with assert_raises(AssertionError):
            self.visual.compare_files(self._testMethodName, self.file_v1, self.file_small, 0)

    def test_get_html_row(self):
        expected_row = '<tr class=diff><td>test_get_html_row</td><td><img style="width: 100%" onclick="window.open\(this.src\)" src="file://.*register_v2.png"/></td></td><td><img style="width: 100%" onclick="window.open\(this.src\)" src="file://.*register.png"/></td></td><td></td></tr>'
        row = self.visual._get_html_row('diff', self._testMethodName, self.file_v1, self.file_v2)
        assertRegex(self, row, expected_row)

    def assert_image(self, img, img_name, expected_image_filename):
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
        PilEngine().assertSameFiles(result_file, expected_image, 0.1)

    def test_crop_element(self):
        # Create element mock
        web_element = get_mock_element(x=250, y=40, height=40, width=300)

        # Resize image
        img = Image.open(self.file_v1)
        img = self.visual.crop_element(img, web_element)

        # Assert output image
        self.assert_image(img, self._testMethodName, 'register_cropped_element')

    def test_mobile_resize(self):
        # Update conf and create a new VisualTest instance
        self.driver_wrapper.driver.get_window_size.return_value = {'width': 375, 'height': 667}
        self.driver_wrapper.config.set('Browser', 'browser', 'ios')
        self.visual = VisualTest(self.driver_wrapper)

        # Resize image
        img = Image.open(self.file_ios)
        img = self.visual.mobile_resize(img)

        # Assert output image
        self.assert_image(img, self._testMethodName, 'ios_resized')

    def test_mobile_no_resize(self):
        # Update conf and create a new VisualTest instance
        self.driver_wrapper.driver.get_window_size.return_value = {'width': 750, 'height': 1334}
        self.driver_wrapper.config.set('Browser', 'browser', 'ios')
        self.visual = VisualTest(self.driver_wrapper)

        # Resize image
        orig_img = Image.open(self.file_ios)
        img = self.visual.mobile_resize(orig_img)

        # Assert that image object has not been modified
        assert_equal(orig_img, img)

    def test_exclude_elements(self):
        # Create elements mock
        web_elements = [get_mock_element(x=250, y=40, height=40, width=300),
                        get_mock_element(x=250, y=90, height=20, width=100)]
        img = Image.open(self.file_v1)

        # Exclude elements
        img = self.visual.exclude_elements(img, web_elements)

        # Assert output image
        self.assert_image(img, self._testMethodName, 'register_exclude')

    def test_exclude_element_outofimage(self):
        # Create elements mock
        web_elements = [get_mock_element(x=250, y=40, height=40, width=1500)]
        img = Image.open(self.file_v1)

        # Exclude elements
        img = self.visual.exclude_elements(img, web_elements)

        # Assert output image
        self.assert_image(img, self._testMethodName, 'register_exclude_outofimage')

    def test_exclude_no_elements(self):
        # Exclude no elements
        img = Image.open(self.file_v1)
        img = self.visual.exclude_elements(img, [])

        # Assert output image
        self.assert_image(img, self._testMethodName, 'register')

    def test_assert_screenshot_full_and_save_baseline(self):
        # Configure driver mock
        def copy_file_side_effect(output_file):
            shutil.copyfile(self.file_v1, output_file)

        self.driver_wrapper.driver.save_screenshot.side_effect = copy_file_side_effect

        # Assert screenshot
        self.visual.assert_screenshot(None, filename='screenshot_full', file_suffix='screenshot_suffix')
        output_file = os.path.join(self.visual.output_directory, '01_screenshot_full__screenshot_suffix.png')
        self.driver_wrapper.driver.save_screenshot.assert_called_with(output_file)

        # Output image and new baseline image must be equals
        baseline_file = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'firefox',
                                     'screenshot_full.png')
        PilEngine().assertSameFiles(output_file, baseline_file, 0.1)

    def test_assert_screenshot_element_and_save_baseline(self):
        # Create element mock
        web_element = get_mock_element(x=250, y=40, height=40, width=300)

        # Configure driver mock
        with open(self.file_v1, "rb") as f:
            image_data = f.read()
        self.driver_wrapper.driver.get_screenshot_as_png.return_value = image_data

        # Assert screenshot
        self.visual.assert_screenshot(web_element, filename='screenshot_elem', file_suffix='screenshot_suffix')
        self.driver_wrapper.driver.get_screenshot_as_png.assert_called_with()

        # Check cropped image
        expected_image = os.path.join(self.root_path, 'resources', 'register_cropped_element.png')
        output_file = os.path.join(self.visual.output_directory, '01_screenshot_elem__screenshot_suffix.png')
        PilEngine().assertSameFiles(output_file, expected_image, 0.1)

        # Output image and new baseline image must be equals
        baseline_file = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'firefox',
                                     'screenshot_elem.png')
        PilEngine().assertSameFiles(output_file, baseline_file, 0.1)

    def test_assert_screenshot_full_and_compare(self):
        # Configure driver mock
        def copy_file_side_effect(output_file):
            shutil.copyfile(self.file_v1, output_file)

        self.driver_wrapper.driver.save_screenshot.side_effect = copy_file_side_effect

        # Add baseline image
        baseline_file = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'firefox',
                                     'screenshot_full.png')
        shutil.copyfile(self.file_v1, baseline_file)

        # Assert screenshot
        self.visual.assert_screenshot(None, filename='screenshot_full', file_suffix='screenshot_suffix')
        output_file = os.path.join(self.visual.output_directory, '01_screenshot_full__screenshot_suffix.png')
        self.driver_wrapper.driver.save_screenshot.assert_called_with(output_file)

    def test_assert_screenshot_element_and_compare(self):
        # Add baseline image
        expected_image = os.path.join(self.root_path, 'resources', 'register_cropped_element.png')
        baseline_file = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'firefox',
                                     'screenshot_elem.png')
        shutil.copyfile(expected_image, baseline_file)

        # Create element mock
        web_element = get_mock_element(x=250, y=40, height=40, width=300)

        # Configure driver mock
        with open(self.file_v1, "rb") as f:
            image_data = f.read()
        self.driver_wrapper.driver.get_screenshot_as_png.return_value = image_data

        # Assert screenshot
        self.visual.assert_screenshot(web_element, filename='screenshot_elem', file_suffix='screenshot_suffix')
        self.driver_wrapper.driver.get_screenshot_as_png.assert_called_with()

    def test_assert_screenshot_mobile_resize_and_exclude(self):
        # Create elements mock
        exclude_elements = [get_mock_element(x=0, y=0, height=24, width=375)]

        # Configure driver mock
        with open(self.file_ios, "rb") as f:
            image_data = f.read()
        self.driver_wrapper.driver.get_screenshot_as_png.return_value = image_data
        self.driver_wrapper.driver.get_window_size.return_value = {'width': 375, 'height': 667}

        # Update conf and create a new VisualTest instance
        self.driver_wrapper.config.set('Browser', 'browser', 'ios')
        self.visual = VisualTest(self.driver_wrapper)

        # Assert screenshot
        self.visual.assert_screenshot(None, filename='screenshot_ios', file_suffix='screenshot_suffix',
                                      exclude_elements=exclude_elements)
        self.driver_wrapper.driver.get_screenshot_as_png.assert_called_with()

        # Check cropped image
        expected_image = os.path.join(self.root_path, 'resources', 'ios_excluded.png')
        output_file = os.path.join(self.visual.output_directory, '01_screenshot_ios__screenshot_suffix.png')
        PilEngine().assertSameFiles(output_file, expected_image, 0.1)

        # Output image and new baseline image must be equals
        baseline_file = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'firefox',
                                     'screenshot_ios.png')
        PilEngine().assertSameFiles(output_file, baseline_file, 0.1)

    def test_assert_screenshot_mobile_web_resize_and_exclude(self):
        # Create elements mock
        form_element = get_mock_element(x=0, y=0, height=559, width=375)
        exclude_elements = [get_mock_element(x=15, y=296.515625, height=32, width=345)]

        # Configure driver mock
        file_ios_web = os.path.join(self.root_path, 'resources', 'ios_web.png')
        with open(file_ios_web, "rb") as f:
            image_data = f.read()
        self.driver_wrapper.driver.get_screenshot_as_png.return_value = image_data
        self.driver_wrapper.driver.get_window_size.return_value = {'width': 375, 'height': 667}

        # Update conf and create a new VisualTest instance
        self.driver_wrapper.config.set('Browser', 'browser', 'ios')
        self.driver_wrapper.config.set('AppiumCapabilities', 'browserName', 'safari')
        self.visual = VisualTest(self.driver_wrapper)

        # Assert screenshot
        self.visual.assert_screenshot(form_element, filename='screenshot_ios_web', file_suffix='screenshot_suffix',
                                      exclude_elements=exclude_elements)
        self.driver_wrapper.driver.get_screenshot_as_png.assert_called_with()

        # Check cropped image
        expected_image = os.path.join(self.root_path, 'resources', 'ios_web_exclude.png')
        output_file = os.path.join(self.visual.output_directory, '01_screenshot_ios_web__screenshot_suffix.png')
        PilEngine().assertSameFiles(output_file, expected_image, 0.1)

        # Output image and new baseline image must be equals
        baseline_file = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'firefox',
                                     'screenshot_ios_web.png')
        PilEngine().assertSameFiles(output_file, baseline_file, 0.1)


@mock.patch('selenium.webdriver.remote.webelement.WebElement', spec=True)
def get_mock_element(WebElement, x, y, height, width):
    web_element = WebElement.return_value
    web_element.location = {'x': x, 'y': y}
    web_element.size = {'height': height, 'width': width}
    return web_element
