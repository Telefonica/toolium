# -*- coding: utf-8 -*-
"""
Copyright 2025 Telefónica Innovación Digital, S.L.
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
import json
import pytest

from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.utils.ai_utils.text_analysis import get_text_criteria_analysis


def configure_default_openai_model():
    """
    Configure OpenAI model used in unit tests
    """
    config = DriverWrappersPool.get_default_wrapper().config
    try:
        config.add_section('AI')
    except Exception:
        pass
    config.set('AI', 'openai_model', 'gpt-4.1-mini')


get_analysis_examples = (
    ('How are you today?', ["is a greeting phrase", "is a question"], 0.7, 1),
    ('Today is sunny', ["is an affirmation", "talks about the weather"], 0.7, 1),
    ('I love programming', ["expresses a positive sentiment"], 0.7, 1),
    ('How are you today?', ["is an affirmation", "talks about the weather"], 0.0, 0.2),
    ('Today is sunny', ["is a greeting phrase", "is a question"], 0.0, 0.2),
    ('I love programming', ["is a greeting phrase", "is a question"], 0.0, 0.2),
)


@pytest.mark.skipif(os.getenv("AZURE_OPENAI_API_KEY") is None,
                    reason="AZURE_OPENAI_API_KEY environment variable not set")
@pytest.mark.parametrize('input_text, features_list, expected_low, expected_high', get_analysis_examples)
def test_get_text_analysis(input_text, features_list, expected_low, expected_high):
    similarity = json.loads(get_text_criteria_analysis(input_text, features_list, azure=True))
    assert expected_low <= similarity['overall_match'] <= expected_high
