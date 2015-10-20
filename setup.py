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
with open('requirements.txt') as f:
    required = f.read().splitlines()

readme = []
with open('README.md', 'r') as fh:
    readme = fh.readlines()

setup(
    name='toolium',
    version=__VERSION__,
    packages=['toolium', 'toolium.pageobjects', 'toolium.pageelements', 'toolium.lettuce'],
    package_data={'': ['resources/VisualTestsTemplate.html']},
    install_requires=required,
    author='Rubén González Alonso, Telefónica I+D',
    author_email='ruben.gonzalezalonso@telefonica.com',
    url='https://github.com/telefonica/toolium',
    description='Wrapper tool for Selenium and Appium libraries',
    long_description='\n'.join(readme),
    keywords=['selenium', 'appium', 'webdriver', 'web automation', 'mobile automation'],
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
