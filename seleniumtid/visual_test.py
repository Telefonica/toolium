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

import logging
import os
import shutil
import re

from seleniumtid import selenium_driver
from selenium.webdriver.remote.webdriver import WebDriver

try:
    from needle.engines.perceptualdiff_engine import Engine as diff_Engine
    from needle.engines.pil_engine import Engine as pil_Engine
    from needle.driver import NeedleWebElement
except ImportError:
    pass


class VisualTest(object):
    template_name = 'VisualTestsTemplate.html'
    row_template_name = 'VisualTestsRowTemplate.html'
    css_name = 'bootstrap.min.css'
    report_name = 'VisualTests.html'

    def __init__(self):
        if not selenium_driver.config.getboolean_optional('Server', 'visualtests_enabled'):
            return

        self.logger = logging.getLogger(__name__)
        self.driver = selenium_driver.driver
        self.output_directory = selenium_driver.output_directory
        self.baseline_directory = selenium_driver.baseline_directory
        engine_type = selenium_driver.config.get_optional('Server', 'visualtests_engine', 'pil')
        self.engine = diff_Engine() if engine_type == 'perceptualdiff' else pil_Engine()
        self.capture = False
        self.save_baseline = selenium_driver.config.getboolean_optional('Server', 'visualtests_save')

        # Create folders
        if not os.path.exists(self.baseline_directory):
            os.makedirs(self.baseline_directory)
        if not self.save_baseline:
            if not os.path.exists(self.output_directory):
                os.makedirs(self.output_directory)
            self._copy_template()

    def _copy_template(self):
        """Copy html template and css file to output directory"""
        orig_template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources', self.template_name)
        dst_template_path = os.path.join(self.output_directory, self.report_name)
        if not os.path.exists(dst_template_path):
            shutil.copyfile(orig_template_path, dst_template_path)
        orig_css_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources', self.css_name)
        dst_css_path = os.path.join(self.output_directory, self.css_name)
        if not os.path.exists(dst_css_path):
            shutil.copyfile(orig_css_path, dst_css_path)

    def assertScreenshot(self, element_or_selector, filename, file_suffix, threshold=0):
        """Assert that a screenshot of an element is the same as a screenshot on disk, within a given threshold

        :param element_or_selector: either a CSS selector as a string or a WebElement object that represents the
                    element to capture. If None, a full screenshot is taken.
        :param filename: the filename for the screenshot, which will be appended with ``.png``
        :param file_suffix: a string to be appended to the output filename
        :param threshold: the threshold for triggering a test failure
        """
        if not selenium_driver.config.getboolean_optional('Server', 'visualtests_enabled'):
            return

        # Search element
        if element_or_selector is None:
            element = None
        elif isinstance(element_or_selector, NeedleWebElement):
            element = element_or_selector
        elif '//' in element_or_selector:
            element = self.driver.find_element_by_xpath(element_or_selector)
        else:
            element = self.driver.find_element_by_css_selector(element_or_selector)

        baseline_file = os.path.join(self.baseline_directory, '{}.png'.format(filename))
        unique_name = '{0:0=2d}_{1}__{2}.png'.format(selenium_driver.visual_number, filename, file_suffix)
        output_file = os.path.join(self.output_directory, unique_name)

        # Determine whether we should save the baseline image
        if self.save_baseline or not os.path.exists(baseline_file):
            # Save the baseline screenshot and bail out
            if element:
                element.get_screenshot().save(baseline_file)
            else:
                self.driver.save_screenshot(baseline_file)
            self.logger.debug("Visual screenshot '{}' saved in visualtests/baseline folder".format(filename))
        else:
            # Save the new screenshot
            if element:
                element.get_screenshot().save(output_file)
            else:
                self.driver.save_screenshot(output_file)
            selenium_driver.visual_number += 1
            # Compare the screenshots
            self._compare_files(file_suffix, output_file, baseline_file, threshold)

    def _compare_files(self, test_name, image_file, baseline_file, threshold):
        """Compare two image files and add result to the html report

        :param test_name: test name
        :param image_file: image file path
        :param baseline_file: baseline image file path
        :param threshold:
        :returns: error message
        """
        try:
            self.engine.assertSameFiles(image_file, baseline_file, threshold)
            return None
        except AssertionError as exc:
            self._add_to_report(test_name, image_file, baseline_file, exc.message)
            if selenium_driver.config.getboolean_optional('Server', 'visualtests_fail'):
                raise exc
            else:
                self.logger.warn('Visual error: {}'.format(exc.message))
                return exc.message

    def _add_to_report(self, test_name, image_file, baseline_file, message=''):
        """Add the result of a visual test to the html report

        :param test_name: test name
        :param image_file: image file path
        :param baseline_file: baseline image file path
        :param message: error message
        """
        row = self._get_html_row(test_name, image_file, baseline_file, message)
        with open(os.path.join(self.output_directory, self.report_name), "r+") as f:
            report = f.read()
            index = report.find('</tbody>')
            report = report[:index] + row + report[index:]
            f.seek(0)
            f.write(report)

    def _get_html_row(self, test_name, image_file, baseline_file, message=''):
        """Create the html row with the result of a visual test

        :param test_name: test name
        :param image_file: image file path
        :param baseline_file: baseline image file path
        :param message: error message
        :returns: str with the html row
        """
        img = '<img style="width: 100%" onclick="window.open(this.src)" src="file://{}"/></td>'
        row = '<tr>'
        row += '<td>' + test_name + '</td>'
        row += '<td>' + img.format(baseline_file) + '</td>'
        row += '<td>' + img.format(image_file) + '</td>'
        diff_file = image_file.replace('.png', '.diff.png')
        diff_row = ''
        if os.path.exists(diff_file):
            diff_row = img.format(diff_file)
        elif 'Image dimensions do not match' in message or message == '':
            diff_row = 'Image dimensions do not match'
        elif 'by a distance of' in message:
            m = re.search('\(by a distance of (.*)\)', message)
            diff_row = 'Distance of ' + m.group(1)
        else:
            diff_row = message
        row += '<td>' + diff_row + '</td>'
        row += '</tr>'
        return row
