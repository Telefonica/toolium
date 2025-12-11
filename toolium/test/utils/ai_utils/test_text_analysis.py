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
from toolium.utils.ai_utils.text_analysis import (get_text_criteria_analysis_openai,
                                                  get_text_criteria_analysis_sentence_transformers)


def configure_default_openai_model():
    """
    Configure OpenAI model used in unit tests
    """
    config = DriverWrappersPool.get_default_wrapper().config
    try:
        config.add_section('AI')
    except Exception:
        pass
    config.set('AI', 'openai_model', 'gpt-4o-mini')


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
    similarity = json.loads(get_text_criteria_analysis_openai(input_text, features_list, azure=True))
    assert expected_low <= similarity['overall_match'] <= expected_high,\
        f"Overall match {similarity['overall_match']} not in range"


extra_task = """
    Additional task:

    Extract all verbs from the input text and add them to the JSON under data.verbs.
    
    Rules:
    - Use the same language as the input text.
    - Return verbs in their base/infinitive form when possible.
    - Do not repeat verbs (no duplicates).
    - Preserve the order in which they first appear in the text.
    - Verbs should be in this base/infinitive form.
    
    The data field must include:
    "data": {
      "verbs": [ "<verb1>", "<verb2>", ... ]
    }
    If no verbs are found, set "verbs" to an empty array: "verbs": [].
"""

get_extra_examples = (
    ('How are you today?', ["is a greeting phrase", "is a question"], ['be']),
    ('I wrote a letter', ["is an affirmation", "talks about the weather"], ['write']),
    ('I have to go', ["expresses a positive sentiment"], ['have', 'go']),
    ('I went to Madrid', ["is an affirmation", "talks about the weather"], ['go']),
    ('Oops I did it again', ["is a greeting phrase", "is a question"], ['do'])
)

@pytest.mark.skipif(os.getenv("AZURE_OPENAI_API_KEY") is None,
                    reason="AZURE_OPENAI_API_KEY environment variable not set")
@pytest.mark.parametrize('input_text, features_list, verb_list', get_extra_examples)
def test_get_text_analysis_extra_features(input_text, features_list, verb_list):
    similarity = json.loads(get_text_criteria_analysis_openai(input_text, features_list,
                                                              azure=True, extra_tasks=extra_task))
    assert similarity['data']['verbs'] == verb_list


examples_sentence_transformers = (
    ('How are you today?', ["hello!", "What's up"], 0.4, 1),
    ('Today is not sunny', ["it's raining"], 0.4, 1),
    ('I love programming', ["I like code", "I love to cook"], 0.4, 1),
    ('How are you today?', ["it's raining", "this text is an affirmation"], 0.0, 0.3),
    ('Today is sunny', ["I like code", "I love to cook"], 0.0, 0.3),
    ('I love programming', ["hello!", "What's up"], 0.0, 0.3),
)


# @pytest.mark.skip(reason='Sentence Transformers model is not available in the CI environment')
@pytest.mark.parametrize('input_text, features_list, expected_low, expected_high', examples_sentence_transformers)
def test_get_text_analysis_sentence_transformers(input_text, features_list, expected_low, expected_high):
    similarity = get_text_criteria_analysis_sentence_transformers(input_text, features_list)
    assert expected_low <= similarity['overall_match'] <= expected_high
