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

import logging

# AI library imports must be optional to allow installing Toolium without `ai` extra dependency
try:
    from openai import AzureOpenAI, OpenAI
except ImportError:
    OpenAI = None
    AzureOpenAI = None

from toolium.driver_wrappers_pool import DriverWrappersPool

logger = logging.getLogger(__name__)


def openai_request(system_message, user_message, model_name=None, azure=False, **kwargs):
    """
    Make a request to OpenAI API (Azure or standard)

    :param system_message: system message to set the behavior of the assistant
    :param user_message: user message with the request
    :param model_name: name of the model to use
    :param azure: whether to use Azure OpenAI or standard OpenAI
    :param kwargs: additional parameters to be passed to the OpenAI client (azure_endpoint, timeout, etc.)
    :returns: tuple with response from OpenAI and token usage dict
    """
    if OpenAI is None:
        raise ImportError("OpenAI is not installed. Please run 'pip install toolium[ai]' to use OpenAI features")
    config = DriverWrappersPool.get_default_wrapper().config
    model_name = model_name or config.get_optional('AI', 'openai_model', 'gpt-4o-mini')
    logger.info('Calling to OpenAI API with model %s', model_name)

    response_format = None
    if kwargs.get('response_format'):
        response_format = kwargs.pop('response_format')
        kwargs.pop('response_format', None)
    client = AzureOpenAI(**kwargs) if azure else OpenAI(**kwargs)
    messages = []
    if isinstance(system_message, list):
        for prompt in system_message:
            messages.append({'role': 'system', 'content': prompt})
    else:
        messages.append({'role': 'system', 'content': system_message})
    messages.append({'role': 'user', 'content': user_message})

    if response_format:
        completion = client.beta.chat.completions.parse(
            model=model_name, messages=messages, response_format=response_format
        )
        response = completion.choices[0].message.parsed
    else:
        completion = client.chat.completions.create(model=model_name, messages=messages)
        response = completion.choices[0].message.content
    token_usage = {}
    if completion.usage:
        token_usage = completion.usage.model_dump()
        logger.info(
            'OpenAI token usage: prompt_tokens=%d, completion_tokens=%d, total_tokens=%d',
            completion.usage.prompt_tokens,
            completion.usage.completion_tokens,
            completion.usage.total_tokens,
        )
    logger.debug('OpenAI response: %s', response)
    return response, token_usage
