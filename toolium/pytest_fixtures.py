# -*- coding: utf-8 -*-
"""
Copyright 2017 Telefónica Investigación y Desarrollo, S.A.U.
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
import pytest
from toolium.driver_wrappers_pool import DriverWrappersPool


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)
    return


@pytest.fixture(scope='session', autouse=True)
def session_driver_fixture(request):
    yield None
    DriverWrappersPool.close_drivers(scope='session',
                                     test_name=request.node.name,
                                     test_passed=request.session.testsfailed == 0)


@pytest.fixture(scope='module', autouse=True)
def module_driver_fixture(request):
    previous_fails = request.session.testsfailed
    yield None
    DriverWrappersPool.close_drivers(scope='module',
                                     test_name=os.path.splitext(os.path.basename(request.node.name))[0],
                                     test_passed=request.session.testsfailed == previous_fails)


@pytest.fixture(scope='function', autouse=True)
def driver_wrapper(request):
    default_driver_wrapper = DriverWrappersPool.connect_default_driver_wrapper()
    yield default_driver_wrapper
    DriverWrappersPool.close_drivers(scope='function',
                                     test_name=request.node.name,
                                     test_passed=not request.node.rep_call.failed)
