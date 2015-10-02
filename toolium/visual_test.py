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

import logging
import os
import shutil
import re

from toolium import toolium_driver

try:
    from needle.engines.perceptualdiff_engine import Engine as diff_Engine
    from needle.engines.pil_engine import Engine as pil_Engine
    from needle.driver import NeedleWebElement
    from types import MethodType
    from PIL import Image
except ImportError:
    pass


class VisualTest(object):
    template_name = 'VisualTestsTemplate.html'
    row_template_name = 'VisualTestsRowTemplate.html'
    report_name = 'VisualTests.html'

    def __init__(self):
        if not toolium_driver.config.getboolean_optional('VisualTests', 'enabled'):
            return

        self.logger = logging.getLogger(__name__)
        self.driver = toolium_driver.driver
        self.output_directory = toolium_driver.visual_output_directory
        self.baseline_directory = toolium_driver.visual_baseline_directory
        engine_type = toolium_driver.config.get_optional('VisualTests', 'engine', 'pil')
        self.engine = diff_Engine() if engine_type == 'perceptualdiff' else pil_Engine()
        self.capture = False
        self.save_baseline = toolium_driver.config.getboolean_optional('VisualTests', 'save')

        # Override get_screenshot method to solve a window size problem in iOS and allow to exclude an element
        NeedleWebElement.get_screenshot = MethodType(self._get_screenshot.__func__, None, NeedleWebElement)

        # Create folders
        if not os.path.exists(self.baseline_directory):
            os.makedirs(self.baseline_directory)
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)
        self._copy_template()

    def _get_screenshot(self, exclude_elements=[]):
        """Returns a screenshot of this element as a PIL image.

        :param exclude_elements: WebElement objects to be excluded
        :returns: Image object with the screenshot
        """
        d = self.get_dimensions()

        # Cast values to int in order for _ImageCrop not to break
        d['left'] = int(d['left'])
        d['top'] = int(d['top'])
        d['width'] = int(d['width'])
        d['height'] = int(d['height'])

        # Get screenshot
        img = self._parent.get_screenshot_as_image()

        # Resize image in iOS
        if toolium_driver.config.get('Browser', 'browser').split('-')[0] == 'iphone':
            window_size = toolium_driver.driver.get_window_size()
            size = (window_size['width'], window_size['height'])
            img = img.resize(size, Image.ANTIALIAS)

        # Exclude elements
        for element in exclude_elements:
            img = VisualTest.exclude_element_from_image(img, element)

        # Crop image
        img = img.crop((d['left'], d['top'], d['left'] + d['width'], d['top'] + d['height']))

        return img

    def _copy_template(self):
        """Copy html template to output directory"""
        orig_template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources', self.template_name)
        dst_template_path = os.path.join(self.output_directory, self.report_name)
        if not os.path.exists(dst_template_path):
            shutil.copyfile(orig_template_path, dst_template_path)

    def assertScreenshot(self, element_or_selector, filename, file_suffix=None, threshold=0, exclude_elements=[]):
        """Assert that a screenshot of an element is the same as a screenshot on disk, within a given threshold

        :param element_or_selector: either a CSS/XPATH selector as a string or a WebElement object.
                                    If None, a full screenshot is taken.
        :param filename: the filename for the screenshot, which will be appended with ``.png``
        :param file_suffix: a string to be appended to the output filename
        :param threshold: the threshold for triggering a test failure
        :param exclude_elements: list of CSS/XPATH selectors as a string or WebElement objects that must be excluded
                                 from the assertion.
        """
        if not toolium_driver.config.getboolean_optional('VisualTests', 'enabled'):
            return

        # Search elements
        element = self.get_element(element_or_selector)
        exclude_elements = [self.get_element(exclude_element) for exclude_element in exclude_elements]

        baseline_file = os.path.join(self.baseline_directory, '{}.png'.format(filename))
        filename_with_suffix = '{0}__{1}'.format(filename, file_suffix) if file_suffix else filename
        unique_name = '{0:0=2d}_{1}.png'.format(toolium_driver.visual_number, filename_with_suffix)
        output_file = os.path.join(self.output_directory, unique_name)
        report_name = '{} ({})'.format(file_suffix, filename)

        # Save the new screenshot
        if element:
            element.get_screenshot(exclude_elements).save(output_file)
        else:
            self.driver.save_screenshot(output_file)
            self.exclude_elements_from_image_file(output_file, exclude_elements)
        toolium_driver.visual_number += 1

        # Determine whether we should save the baseline image
        if self.save_baseline or not os.path.exists(baseline_file):
            # Copy screenshot to baseline
            shutil.copyfile(output_file, baseline_file)

            if toolium_driver.config.getboolean_optional('VisualTests', 'complete_report'):
                self._add_to_report('baseline', report_name, output_file, None, 'Added to baseline')

            self.logger.debug("Visual screenshot '{}' saved in visualtests/baseline folder".format(filename))
        else:
            # Compare the screenshots
            self._compare_files(report_name, output_file, baseline_file, threshold)

    def get_element(self, element_or_selector):
        """Search element by xpath or css

        :param element_or_selector: either a CSS/XPATH selector as a string or a WebElement object
        :returns: WebElement object
        """
        if element_or_selector is None:
            element = None
        elif isinstance(element_or_selector, NeedleWebElement):
            element = element_or_selector
        elif '//' in element_or_selector:
            element = self.driver.find_element_by_xpath(element_or_selector)
        elif element_or_selector.startswith('.'):
            element = self.driver.find_element_by_ios_uiautomation(element_or_selector)
        else:
            element = self.driver.find_element_by_css_selector(element_or_selector)
        return element

    def _compare_files(self, report_name, image_file, baseline_file, threshold):
        """Compare two image files and add result to the html report

        :param report_name: name to show in html report
        :param image_file: image file path
        :param baseline_file: baseline image file path
        :param threshold: percentage threshold
        :returns: error message
        """
        try:
            self.engine.assertSameFiles(image_file, baseline_file, threshold)
            if toolium_driver.config.getboolean_optional('VisualTests', 'complete_report'):
                self._add_to_report('equal', report_name, image_file, baseline_file)
            return None
        except AssertionError as exc:
            self._add_to_report('diff', report_name, image_file, baseline_file, exc.message)
            if toolium_driver.config.getboolean_optional('VisualTests', 'fail'):
                raise exc
            else:
                self.logger.warn('Visual error: {}'.format(exc.message))
                return exc.message

    @staticmethod
    def exclude_elements_from_image_file(image_file, elements):
        """Modify image file hiding elements with a black rectangle

        :param image_file: image file path
        :param elements: WebElement objects to be excluded
        """
        if len(elements) == 0:
            return

        img = Image.open(image_file)
        for element in elements:
            img = VisualTest.exclude_element_from_image(img, element)
        img.save(image_file, "PNG")

    @staticmethod
    def exclude_element_from_image(img, element):
        """Modify image object hiding an element with a black rectangle

        :param img: image object
        :param element: WebElement object to be excluded
        """
        if element is None:
            return img

        img = img.convert("RGBA")
        pixdata = img.load()
        d = element.get_dimensions()

        for y in xrange(d['top'], d['top'] + d['height']):
            for x in xrange(d['left'], d['left'] + d['width']):
                try:
                    pixdata[x, y] = (0, 0, 0, 255)
                except IndexError:
                    pass

        return img

    def _add_to_report(self, result, report_name, image_file, baseline_file, message=None):
        """Add the result of a visual test to the html report

        :param result: comparation result (equal, diff, baseline)
        :param report_name: name to show in html report
        :param image_file: image file path
        :param baseline_file: baseline image file path
        :param message: error message
        """
        row = self._get_html_row(result, report_name, image_file, baseline_file, message)
        with open(os.path.join(self.output_directory, self.report_name), "r+") as f:
            report = f.read()
            index = report.find('</tbody>')
            report = report[:index] + row + report[index:]
            f.seek(0)
            f.write(report)

    def _get_html_row(self, result, report_name, image_file, baseline_file, message=None):
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
