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

# Python 2.7
from __future__ import division

import logging
import os
import re
import shutil
from io import BytesIO

try:
    # Python 2.7
    xrange
except NameError:
    # Python 3
    xrange = range

from toolium.driver_wrappers_pool import DriverWrappersPool
import itertools
from needle.engines.perceptualdiff_engine import Engine as PerceptualEngine
# from needle.engines.imagemagick_engine import Engine as MagickEngine
from needle.engines.pil_engine import Engine as PilEngine
from PIL import Image


class VisualTest(object):
    template_name = 'VisualTestsTemplate.html'
    report_name = 'VisualTests.html'
    driver_wrapper = None

    def __init__(self, driver_wrapper=None):
        self.driver_wrapper = driver_wrapper if driver_wrapper else DriverWrappersPool.get_default_wrapper()
        if not self.driver_wrapper.config.getboolean_optional('VisualTests', 'enabled'):
            return

        self.utils = self.driver_wrapper.utils
        self.logger = logging.getLogger(__name__)
        self.output_directory = DriverWrappersPool.visual_output_directory
        self.baseline_directory = self.driver_wrapper.visual_baseline_directory
        engine_type = self.driver_wrapper.config.get_optional('VisualTests', 'engine', 'pil')
        if engine_type == 'perceptualdiff':
            self.engine = PerceptualEngine()
        # elif engine_type == 'imagemagick':
        #    self.engine = MagickEngine()
        elif engine_type == 'pil':
            self.engine = PilEngine()
        else:
            self.logger.warn(
                    "Engine '{}' not found, using pil instead. Review your properties.cfg file.".format(engine_type))
            self.engine = PilEngine()
        self.save_baseline = self.driver_wrapper.config.getboolean_optional('VisualTests', 'save')

        # Create folders
        if not os.path.exists(self.baseline_directory):
            os.makedirs(self.baseline_directory)
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)

        # Copy html template to output directory
        orig_template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources', self.template_name)
        dst_template_path = os.path.join(self.output_directory, self.report_name)
        if not os.path.exists(dst_template_path):
            shutil.copyfile(orig_template_path, dst_template_path)

    def assertScreenshot(self, element_or_locator, filename, file_suffix=None, threshold=0, exclude_elements=[]):
        """Assert that a screenshot of an element is the same as a screenshot on disk, within a given threshold

        :param element_or_locator: either a WebElement, a PageElement or an element locator as a tuple (locator_type,
                                   locator_value). If None, a full screenshot is taken.
        :param filename: the filename for the screenshot, which will be appended with ``.png``
        :param file_suffix: a string to be appended to the output filename
        :param threshold: the threshold for triggering a test failure
        :param exclude_elements: list of WebElements, a PageElement or element locators as a tuple (locator_type,
                                 locator_value) that must be excluded from the assertion.
        """
        if not self.driver_wrapper.config.getboolean_optional('VisualTests', 'enabled'):
            return

        # Search elements
        element = self.utils.get_element(element_or_locator)
        exclude_elements = [self.utils.get_element(exclude_element) for exclude_element in exclude_elements]

        baseline_file = os.path.join(self.baseline_directory, '{}.png'.format(filename))
        filename_with_suffix = '{0}__{1}'.format(filename, file_suffix) if file_suffix else filename
        unique_name = '{0:0=2d}_{1}.png'.format(DriverWrappersPool.visual_number, filename_with_suffix)
        output_file = os.path.join(self.output_directory, unique_name)
        report_name = '{}<br>({})'.format(file_suffix, filename)

        # Get screenshot and modify it
        if self.driver_wrapper.is_ios_test() or self.driver_wrapper.is_android_web_test() or (
                    exclude_elements and len(exclude_elements) > 0) or element:
            img = Image.open(BytesIO(self.driver_wrapper.driver.get_screenshot_as_png()))
            img = self.mobile_resize(img)
            img = self.exclude_elements(img, exclude_elements)
            img = self.crop_element(img, element)
            img.save(output_file)
        else:
            # Faster method if the screenshot must not be modified
            self.driver_wrapper.driver.save_screenshot(output_file)
        DriverWrappersPool.visual_number += 1

        # Determine whether we should save the baseline image
        if self.save_baseline or not os.path.exists(baseline_file):
            # Copy screenshot to baseline
            shutil.copyfile(output_file, baseline_file)

            if self.driver_wrapper.config.getboolean_optional('VisualTests', 'complete_report'):
                self._add_to_report('baseline', report_name, output_file, None, 'Added to baseline')

            self.logger.debug("Visual screenshot '{}' saved in visualtests/baseline folder".format(filename))
        else:
            # Compare the screenshots
            self.compare_files(report_name, output_file, baseline_file, threshold)

    def mobile_resize(self, img):
        """Resize image in iOS (native and web) and Android (web) to fit window size

        :param img: image object
        :returns: modified image object
        """
        if self.driver_wrapper.is_ios_test() or self.driver_wrapper.is_android_web_test():
            scale = img.size[0] / self.utils.get_window_size()['width']
            if scale != 1:
                new_image_size = (int(img.size[0] / scale), int(img.size[1] / scale))
                img = img.resize(new_image_size, Image.ANTIALIAS)
        return img

    def get_element_box(self, element):
        """Get element coordinates

        :param element: WebElement object
        :returns: tuple with element coordinates
        """
        offset = self.utils.get_safari_navigation_bar_height()
        return (int(element.location['x']), int(element.location['y'] + offset),
                int(element.location['x'] + element.size['width']),
                int(element.location['y'] + offset + element.size['height']))

    def crop_element(self, img, element):
        """Crop image to fit element

        :param img: image object
        :param element: WebElement object
        :returns: modified image object
        """
        if element:
            img = img.crop(self.get_element_box(element))
        return img

    def exclude_elements(self, img, elements):
        """Modify image hiding elements with a black rectangle

        :param img: image object
        :param elements: WebElement objects to be excluded
        """
        if elements and len(elements) > 0:
            img = img.convert("RGBA")
            pixel_data = img.load()

            for element in elements:
                element_box = self.get_element_box(element)
                for x, y in itertools.product(xrange(element_box[0], element_box[2]),
                                              xrange(element_box[1], element_box[3])):
                    try:
                        pixel_data[x, y] = (0, 0, 0, 255)
                    except IndexError:
                        pass

        return img

    def compare_files(self, report_name, image_file, baseline_file, threshold):
        """Compare two image files and add result to the html report

        :param report_name: name to show in html report
        :param image_file: image file path
        :param baseline_file: baseline image file path
        :param threshold: percentage threshold
        :returns: error message
        """
        try:
            self.engine.assertSameFiles(image_file, baseline_file, threshold)
            if self.driver_wrapper.config.getboolean_optional('VisualTests', 'complete_report'):
                self._add_to_report('equal', report_name, image_file, baseline_file)
            return None
        except AssertionError as exc:
            self._add_to_report('diff', report_name, image_file, baseline_file, str(exc))
            if self.driver_wrapper.config.getboolean_optional('VisualTests', 'fail'):
                raise exc
            else:
                self.logger.warn('Visual error: {}'.format(str(exc)))
                return str(exc)

    def _add_to_report(self, result, report_name, image_file, baseline_file, message=None):
        """Add the result of a visual test to the html report

        :param result: comparation result (equal, diff, baseline)
        :param report_name: name to show in html report
        :param image_file: image file path
        :param baseline_file: baseline image file path
        :param message: error message
        """
        row = VisualTest._get_html_row(result, report_name, image_file, baseline_file, message)
        with open(os.path.join(self.output_directory, self.report_name), "r+") as f:
            report = f.read()
            index = report.find('</tbody>')
            report = report[:index] + row + report[index:]
            f.seek(0)
            f.write(report)

    @staticmethod
    def _get_html_row(result, report_name, image_file, baseline_file, message=None):
        """Create the html row with the result of a visual test

        :param result: comparation result (equal, diff, baseline)
        :param report_name: name to show in html report
        :param image_file: image file path
        :param baseline_file: baseline image file path
        :param message: error message
        :returns: str with the html row
        """
        img = '<img style="width: 100%" onclick="window.open(this.src)" src="file://{}"/></td>'
        row = '<tr class=' + result + '>'
        row += '<td>' + report_name + '</td>'

        # baseline column
        baseline_col = img.format(baseline_file) if baseline_file is not None else ''
        row += '<td>' + baseline_col + '</td>'

        # image column
        image_col = img.format(image_file) if image_file is not None else ''
        row += '<td>' + image_col + '</td>'

        # diff column
        diff_file = image_file.replace('.png', '.diff.png')
        if os.path.exists(diff_file):
            diff_col = img.format(diff_file)
        elif message is None:
            diff_col = ''
        elif message == '' or 'Image dimensions do not match' in message:
            diff_col = 'Image dimensions do not match'
        elif 'by a distance of' in message:
            m = re.search('\(by a distance of (.*)\)', message)
            diff_col = 'Distance of ' + m.group(1)
        else:
            diff_col = message
        row += '<td>' + diff_col + '</td>'

        row += '</tr>'
        return row
