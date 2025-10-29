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

import pytest

from toolium.utils.ai_utils.accuracy import get_accuracy_and_retries_from_tags


accuracy_tags_examples = (
    (['accuracy'], {'accuracy': 0.9, 'retries': 10}),
    (['accuracy_85'], {'accuracy': 0.85, 'retries': 10}),
    (['accuracy_percent_80'], {'accuracy': 0.8, 'retries': 10}),
    (['accuracy_75_5'], {'accuracy': 0.75, 'retries': 5}),
    (['accuracy_percent_70_retries_3'], {'accuracy': 0.7, 'retries': 3}),
    (['other_tag', 'accuracy_95_15'], {'accuracy': 0.95, 'retries': 15}),
    (['no_accuracy_tag'], None),
    (['accuracy_85', 'accuracy_95_15'], {'accuracy': 0.85, 'retries': 10}),
    ([], None),
)


@pytest.mark.parametrize('tags, expected_accuracy_data', accuracy_tags_examples)
def test_get_accuracy_and_retries_from_tags(tags, expected_accuracy_data):
    accuracy_data = get_accuracy_and_retries_from_tags(tags)
    assert accuracy_data == expected_accuracy_data
