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
from unittest import mock

import pytest

from toolium.test.utils.ai_utils.common import (
    configure_default_openai_model,  # noqa: F401, fixture needed to set the OpenAI model for all tests in this module
)
from toolium.utils.ai_utils.openai import openai_request


def _build_mock_completion(content='test response', prompt_tokens=10, completion_tokens=5, total_tokens=15):
    """Build a mock OpenAI completion object with usage data"""
    mock_usage = mock.MagicMock()
    mock_usage.prompt_tokens = prompt_tokens
    mock_usage.completion_tokens = completion_tokens
    mock_usage.total_tokens = total_tokens

    mock_message = mock.MagicMock()
    mock_message.content = content

    mock_choice = mock.MagicMock()
    mock_choice.message = mock_message

    mock_completion = mock.MagicMock()
    mock_completion.choices = [mock_choice]
    mock_completion.usage = mock_usage
    return mock_completion


@mock.patch('toolium.utils.ai_utils.openai.OpenAI')
def test_openai_request_returns_token_usage(mock_openai_class):
    mock_client = mock.MagicMock()
    mock_openai_class.return_value = mock_client
    mock_client.chat.completions.create.return_value = _build_mock_completion(
        content='hello', prompt_tokens=20, completion_tokens=10, total_tokens=30
    )

    response, token_usage = openai_request('system', 'user')

    assert response == 'hello'
    assert token_usage == {'prompt_tokens': 20, 'completion_tokens': 10, 'total_tokens': 30}


@mock.patch('toolium.utils.ai_utils.openai.OpenAI')
def test_openai_request_returns_empty_token_usage_when_no_usage(mock_openai_class):
    mock_client = mock.MagicMock()
    mock_openai_class.return_value = mock_client
    mock_completion = _build_mock_completion()
    mock_completion.usage = None
    mock_client.chat.completions.create.return_value = mock_completion

    response, token_usage = openai_request('system', 'user')

    assert response == 'test response'
    assert token_usage == {}


@mock.patch('toolium.utils.ai_utils.openai.OpenAI')
def test_openai_request_with_response_format_returns_token_usage(mock_openai_class):
    mock_client = mock.MagicMock()
    mock_openai_class.return_value = mock_client

    mock_parsed = mock.MagicMock()
    mock_message = mock.MagicMock()
    mock_message.parsed = mock_parsed
    mock_choice = mock.MagicMock()
    mock_choice.message = mock_message
    mock_completion = mock.MagicMock()
    mock_completion.choices = [mock_choice]
    mock_usage = mock.MagicMock()
    mock_usage.prompt_tokens = 50
    mock_usage.completion_tokens = 25
    mock_usage.total_tokens = 75
    mock_completion.usage = mock_usage
    mock_client.beta.chat.completions.parse.return_value = mock_completion

    response, token_usage = openai_request('system', 'user', response_format=mock.MagicMock())

    assert response is mock_parsed
    assert token_usage == {'prompt_tokens': 50, 'completion_tokens': 25, 'total_tokens': 75}


@pytest.mark.skipif(not os.getenv('AZURE_OPENAI_API_KEY'), reason='AZURE_OPENAI_API_KEY environment variable not set')
def test_openai_request_returns_token_usage_with_azure():
    response, token_usage = openai_request('You are a helpful assistant.', 'Say hello.', azure=True)

    assert isinstance(response, str)
    assert len(response) > 0
    assert token_usage['prompt_tokens'] > 0
    assert token_usage['completion_tokens'] > 0
    assert token_usage['total_tokens'] > 0
