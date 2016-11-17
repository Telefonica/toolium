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


class ConfigFiles():
    def __init__(self):
        self.config_directory = None
        self.output_directory = None
        self.visual_baseline_directory = None
        self.config_properties_filenames = None
        self.config_log_filename = None
        self.output_log_filename = None

    def set_config_directory(self, config_directory):
        """Set directory where configuration files are saved

        :param config_directory: configuration directory path
        """
        self.config_directory = config_directory

    def set_output_directory(self, output_directory):
        """Set output directory where log file and screenshots will be saved

        :param output_directory: output directory path
        """
        self.output_directory = output_directory

    def set_visual_baseline_directory(self, visual_baseline_directory):
        """Set visual baseline directory where baseline images will be saved

        :param visual_baseline_directory: visual baseline directory path
        """
        self.visual_baseline_directory = visual_baseline_directory

    def set_config_properties_filenames(self, *filenames):
        """Set properties files used to configure test cases

        :param filenames: list of properties filenames
        """
        self.config_properties_filenames = ';'.join(filenames)

    def set_config_log_filename(self, filename):
        """Set logging configuration file

        :param filename: logging configuration filename
        """
        self.config_log_filename = filename

    def set_output_log_filename(self, filename):
        """Set logging output file

        :param filename: logging configuration filename
        """
        self.output_log_filename = filename
