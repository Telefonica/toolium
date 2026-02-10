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

import json
import logging
import os

import pytest

from toolium.utils.ai_utils.ai_agent import create_react_agent, execute_agent

# Global variable to keep track of mock responses in the agent
mock_response_id = 0

logger = logging.getLogger(__name__)


def tv_recommendations(user_question):  # noqa: ARG001
    """
    Tool to help users find TV content.
    Asks questions to the user to understand their preferences and then recommends specific content.
    Takes into account previous questions to make increasingly accurate recommendations.

    :param user_question: The question from the user to the tool
    :returns: A response from the tool based on the user's question
    """
    mocked_responses = [
        'Hola, ¿hoy te encuentras triste o feliz?',
        '¿Te gustaría que busque contenidos cómicos o de acción?',
        'He encontrado estas series que pueden gustarte: "The Office", "Parks and Recreation" and "Brooklyn Nine-Nine"',
    ]

    # Return the next response in the list for each call, and loop back to the start after the last one
    global mock_response_id
    response = mocked_responses[mock_response_id]
    mock_response_id = mock_response_id + 1 if mock_response_id < len(mocked_responses) - 1 else 0
    return response


TV_CONTENT_SYSTEM_MESSAGE = (
    'You are a user looking for TV content. '
    'To do this, you will be helped by an assistant who will guide you with questions. '
    "Answer the assistant's questions until it recommends specific content to you. "
    'CRITICAL RULE: As soon as the TV assistant responds with concrete results, '
    '(I found ..., Here you have ...), stop asking questions immediately, analyze the response '
    "and return an analysis about the assistant's performance, to see if it answered correctly. "
    'If after 5 questions, the assistant has not given any recommendation, do not continue asking '
    'and return the analysis. '
    'Respond in JSON format: '
    '{"result": RESULT, "analysis": "your analysis"} '
    'where RESULT = true if it worked well and returned relevant content, false if not.'
)


@pytest.mark.skipif(not os.getenv('AZURE_OPENAI_API_KEY'), reason='AZURE_OPENAI_API_KEY environment variable not set')
def test_react_agent():
    agent = create_react_agent(TV_CONTENT_SYSTEM_MESSAGE, tool_method=tv_recommendations, model_name='gpt-4o-mini')
    agent_results = execute_agent(agent)

    # Check if the agent's final response contains a valid JSON with the expected structure and analyze the result
    try:
        ai_agent_response = json.loads(agent_results['messages'][-1].content)
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise AssertionError('AI Agent did not return a valid response') from e
    error_message = f'TV recommendations use case did not return a valid response: {ai_agent_response["analysis"]}'
    assert ai_agent_response['result'] is True, error_message
