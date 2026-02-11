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

# Configure logger
logger = logging.getLogger(__name__)


def openai_request(system_message, user_message, model_name=None, azure=False, **kwargs):
    """
    Make a request to OpenAI API (Azure or standard)

    :param system_message: system message to set the behavior of the assistant
    :param user_message: user message with the request
    :param model_name: name of the model to use
    :param azure: whether to use Azure OpenAI or standard OpenAI
    :param kwargs: additional parameters to be passed to the OpenAI client (azure_endpoint, timeout, etc.)
    :returns: response from OpenAI
    """
    if OpenAI is None:
        raise ImportError("OpenAI is not installed. Please run 'pip install toolium[ai]' to use OpenAI features")
    config = DriverWrappersPool.get_default_wrapper().config
    model_name = model_name or config.get_optional('AI', 'openai_model', 'gpt-4o-mini')
    logger.info(f'Calling to OpenAI API with model {model_name}')
    client = AzureOpenAI(**kwargs) if azure else OpenAI(**kwargs)
    msg = []
    if isinstance(system_message, list):
        for prompt in system_message:
            msg.append({'role': 'system', 'content': prompt})
    else:
        msg.append({'role': 'system', 'content': system_message})
    msg.append({'role': 'user', 'content': user_message})
    completion = client.chat.completions.create(
        model=model_name,
        messages=msg,
    )
    response = completion.choices[0].message.content
    logger.debug(f'OpenAI response: {response}')
    return response
