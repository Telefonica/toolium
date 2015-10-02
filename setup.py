# -*- coding: utf-8 -*-
'''
(c) Copyright 2014 Telefonica, I+D. Printed in Spain (Europe). All Rights
Reserved.

The copyright to the software program(s) is property of Telefonica I+D.
The program(s) may be used and or copied only with the express written
consent of Telefonica I+D or in accordance with the terms and conditions
stipulated in the agreement/contract under which the program(s) have
been supplied.
'''
from setuptools import setup

__VERSION__ = file('VERSION').read().strip()
with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='toolium',
    version=__VERSION__,
    packages=['toolium', 'toolium.pageobjects', 'toolium.pageelements', 'toolium.lettuce'],
    package_data={'': ['resources/VisualTestsTemplate.html']},
    url='',
    license='',
    author='Telefonica I+D',
    author_email='ruben.gonzalezalonso@telefonica.com',
    description='Toolium library for Python',
    install_requires=required
)
