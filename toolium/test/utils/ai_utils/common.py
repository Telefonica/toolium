"""
Copyright 2026 Telefónica Innovación Digital, S.L.
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

import pytest

from toolium.driver_wrappers_pool import DriverWrappersPool


@pytest.fixture(scope='module', autouse=True)
def configure_default_openai_model():
    """
    Configure OpenAI model once for all tests in the module
    """
    config = DriverWrappersPool.get_default_wrapper().config
    try:
        config.add_section('AI')
    except Exception:
        pass
    config.set('AI', 'openai_model', 'gpt-4.1-mini')
