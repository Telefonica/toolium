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

from setuptools import setup

__VERSION__ = file('VERSION').read().strip()


def read_file(filepath):
    with open(filepath) as f:
        return f.read().splitlines()


def get_long_description():
    """Get README content and update rst urls

    :returns: long description
    """
    docs_url = 'http://toolium.readthedocs.org/en/latest'
    readme = read_file('README.rst')
    description = []
    for line in readme:
        desc_line = line.replace('/docs/browser_configuration.rst', docs_url + '/browser_configuration.html')
        desc_line = desc_line.replace('/CHANGELOG.rst', docs_url + '/changelog.html')
        description.append(desc_line)
    return description


setup(
    name='toolium',
    version=__VERSION__,
    packages=['toolium', 'toolium.pageobjects', 'toolium.pageelements', 'toolium.lettuce'],
    package_data={'': ['resources/VisualTestsTemplate.html']},
    install_requires=read_file('requirements.txt'),
    tests_require=read_file('requirements_dev.txt'),
    test_suite='toolium.test',
    author='Rubén González Alonso, Telefónica I+D',
    author_email='ruben.gonzalezalonso@telefonica.com',
    url='https://github.com/telefonica/toolium',
    description='Wrapper tool of Selenium and Appium libraries to test web and mobile applications in a single project',
    long_description=get_long_description(),
    keywords=['selenium', 'appium', 'webdriver', 'web automation', 'mobile automation', 'page object',
              'visual testing'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
    ],
    license='Apache 2.0',
)
