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

import os

import pytest

try:
    from pydantic import BaseModel, Field
except ImportError:
    BaseModel = None
    Field = None

from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.test.utils.ai_utils.common import (
    configure_default_openai_model,  # noqa: F401, fixture needed to set the OpenAI model for all tests in this module
)
from toolium.utils.ai_utils.evaluate_answer import assert_answer_evaluation, get_answer_evaluation_with_azure_openai

test_data_get = [
    (
        'Paris is both the capital and the most populous city in France.',
        'The capital and largest city of France is Paris.',
        'What is the capital of France and its largest city?',
    ),
    (
        'You can update your credentials by navigating to the Security tab within your Account Settings '
        'and click Change Password',
        'Go to Settings, click Security, and select Change Password.',
        'How do I reset my password?',
    ),
    (
        'Apples are healthy because they contain fiber which is good for your gut.',
        'Apples are high in fiber and Vitamin C, which support digestion and immune health.',
        'What are the health benefits of eating apples?',
    ),
    (
        'France won the World Cup in 2022 after a close final.',
        'Argentina won the 2022 FIFA World Cup.',
        'Who won the World Cup in 2022?',
    ),
]

data_assert = [
    (0.95),
    (0.7),
    (0.5),
    (0),
]

test_data_assert = [(*element, value) for element, value in zip(test_data_get, data_assert, strict=True)]


@pytest.mark.skipif(not os.getenv('AZURE_OPENAI_API_KEY'), reason='AZURE_OPENAI_API_KEY environment variable not set')
@pytest.mark.parametrize(
    ('llm_answer', 'reference_answer', 'question'),
    test_data_get,
)
def test_get_answer_evaluation_no_format_with_azure_openai(llm_answer, reference_answer, question):
    similarity, response = get_answer_evaluation_with_azure_openai(
        llm_answer=llm_answer, reference_answer=reference_answer, question=question
    )
    assert isinstance(similarity, float), 'Similarity should be a float'
    assert isinstance(response['explanation'], str), 'Explanation should be a string'
    assert response['explanation'], 'Explanation should not be empty'


@pytest.mark.skipif(not os.getenv('AZURE_OPENAI_API_KEY'), reason='AZURE_OPENAI_API_KEY environment variable not set')
@pytest.mark.skipif(BaseModel is None, reason='pydantic not installed, required for structured response format tests')
@pytest.mark.parametrize(
    ('llm_answer', 'reference_answer', 'question'),
    test_data_get,
)
def test_get_answer_evaluation_with_format_with_azure_openai(llm_answer, reference_answer, question):
    class SimilarityEvaluation(BaseModel):
        """Model for text similarity evaluation response"""

        similarity: float = Field(description='Similarity score between 0.0 and 1.0', ge=0.0, le=1.0)
        explanation: str = Field(description='Brief justification for the similarity score')

    similarity, response = get_answer_evaluation_with_azure_openai(
        llm_answer=llm_answer,
        reference_answer=reference_answer,
        question=question,
        response_format=SimilarityEvaluation,
    )
    assert isinstance(similarity, float), 'Similarity should be a float'
    assert isinstance(response.explanation, str), 'Explanation should be a string'
    assert response.explanation, 'Explanation should not be empty'


@pytest.mark.skipif(not os.getenv('AZURE_OPENAI_API_KEY'), reason='AZURE_OPENAI_API_KEY environment variable not set')
@pytest.mark.skipif(BaseModel is None, reason='pydantic not installed, required for structured response format tests')
@pytest.mark.parametrize(
    ('llm_answer', 'reference_answer', 'question'),
    test_data_get,
)
def test_get_answer_evaluation_with_complex_format_with_azure_openai(llm_answer, reference_answer, question):
    class AnswerEval(BaseModel):
        """LLM-as-a-judge evaluation of answer quality."""

        similarity: float = Field(description='Similarity score between 0.0 and 1.0', ge=0.0, le=1.0)
        explanation: str = Field(
            description='Concise feedback on the answer quality, comparing it to the reference answer and evaluating'
            ' based on the retrieved context'
        )
        accuracy: float = Field(
            description='How factually correct is the answer compared to the reference answer? 1 (wrong. any wrong '
            'answer must score 1) to 5 (ideal - perfectly accurate). An acceptable answer would score 3.'
        )
        completeness: float = Field(
            description='How complete is the answer in addressing all aspects of the question? 1 (very poor - missing '
            'key information) to 5 (ideal - all the information from the reference answer is provided completely).'
            'Only answer 5 if ALL information from the reference answer is included.'
        )
        relevance: float = Field(
            description='How relevant is the answer to the specific question asked? 1 (very poor - off-topic) to 5 '
            '(ideal - directly addresses question and gives no additional information). '
            'Only answer 5 if the answer is completely relevant to the question and gives no additional information.'
        )

    similarity, response = get_answer_evaluation_with_azure_openai(
        llm_answer=llm_answer,
        reference_answer=reference_answer,
        question=question,
        response_format=AnswerEval,
    )
    assert isinstance(similarity, float), 'Similarity should be a float'
    assert isinstance(response.explanation, str), 'Explanation should be a string'
    assert response.explanation, 'Explanation should not be empty'
    assert response.accuracy, 'Accuracy should be provided'
    assert response.completeness, 'Completeness should be provided'
    assert response.relevance, 'Relevance should be provided'


@pytest.mark.skipif(not os.getenv('AZURE_OPENAI_API_KEY'), reason='AZURE_OPENAI_API_KEY environment variable not set')
@pytest.mark.skipif(BaseModel is None, reason='pydantic not installed, required for structured response format tests')
@pytest.mark.parametrize(
    ('llm_answer', 'reference_answer', 'question'),
    test_data_get,
)
def test_get_answer_evaluation_ignored_format_with_azure_openai(llm_answer, reference_answer, question):
    class AnswerEval(BaseModel):
        """LLM-as-a-judge evaluation of answer quality."""

        explanation: str = Field(
            description='Concise feedback on the answer quality, comparing it to the reference answer and evaluating'
            ' based on the retrieved context'
        )
        accuracy: float = Field(
            description='How factually correct is the answer compared to the reference answer? 1 (wrong. any wrong '
            'answer must score 1) to 5 (ideal - perfectly accurate). An acceptable answer would score 3.'
        )
        completeness: float = Field(
            description='How complete is the answer in addressing all aspects of the question? 1 (very poor - missing '
            'key information) to 5 (ideal - all the information from the reference answer is provided completely).'
            'Only answer 5 if ALL information from the reference answer is included.'
        )
        relevance: float = Field(
            description='How relevant is the answer to the specific question asked? 1 (very poor - off-topic) to 5 '
            '(ideal - directly addresses question and gives no additional information). '
            'Only answer 5 if the answer is completely relevant to the question and gives no additional information.'
        )

    similarity, response = get_answer_evaluation_with_azure_openai(
        llm_answer=llm_answer,
        reference_answer=reference_answer,
        question=question,
        response_format=AnswerEval,
    )
    assert isinstance(similarity, float), 'Similarity should be a float'
    assert isinstance(response['explanation'], str), 'Explanation should be a string'
    assert response['explanation'], 'Explanation should not be empty'


@pytest.mark.skipif(not os.getenv('AZURE_OPENAI_API_KEY'), reason='AZURE_OPENAI_API_KEY environment variable not set')
@pytest.mark.parametrize(
    ('llm_answer', 'reference_answer', 'question', 'expected_low'),
    test_data_assert,
)
def test_assert_answer_with_azure_openai(llm_answer, reference_answer, question, expected_low):
    provider = 'azure'
    assert_answer_evaluation(
        llm_answer=llm_answer,
        reference_answers=reference_answer,
        question=question,
        threshold=expected_low,
        provider=provider,
    )


@pytest.mark.skipif(not os.getenv('AZURE_OPENAI_API_KEY'), reason='AZURE_OPENAI_API_KEY environment variable not set')
@pytest.mark.parametrize(
    ('llm_answer', 'reference_answer', 'question', 'expected_low'),
    test_data_assert,
)
def test_assert_answer_from_config(llm_answer, reference_answer, question, expected_low):
    config = DriverWrappersPool.get_default_wrapper().config
    try:
        config.add_section('AI')
    except Exception:
        pass
    config.set('AI', 'provider', 'azure')
    assert_answer_evaluation(
        llm_answer=llm_answer,
        reference_answers=reference_answer,
        question=question,
        threshold=expected_low,
    )
