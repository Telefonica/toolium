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

import json
import logging

# Library imports must be optional to allow installing Toolium without `ai` extra dependency
try:
    import spacy
except ImportError:
    spacy = None
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
try:
    from openai import OpenAI, AzureOpenAI
except ImportError:
    OpenAI = None
    AzureOpenAI = None

from toolium.driver_wrappers_pool import DriverWrappersPool


# Configure logger
logger = logging.getLogger(__name__)


def get_text_similarity_with_spacy(text, expected_text, model_name=None):
    """
    Return similarity between two texts using spaCy

    :param text: string to compare
    :param expected_text: string with the expected text
    :param model_name: name of the spaCy model to use
    :returns: similarity score between the two texts
    """
    if spacy is None:
        raise ImportError("spaCy is not installed. Please run 'pip install toolium[ai]' to use spaCy features")
    config = DriverWrappersPool.get_default_wrapper().config
    model_name = model_name or config.get_optional('AI', 'spacy_model', 'en_core_web_sm')
    model = spacy.load(model_name)
    similarity = model(text).similarity(model(expected_text))
    logger.info(f"spaCy similarity: {similarity} between '{text}' and '{expected_text}'")
    return similarity


def get_text_similarity_with_sentence_transformers(text, expected_text, model_name=None):
    """
    Return similarity between two texts using Sentence Transformers

    :param text: string to compare
    :param expected_text: string with the expected text
    :param model_name: name of the Sentence Transformers model to use
    :returns: similarity score between the two texts
    """
    if SentenceTransformer is None:
        raise ImportError("Sentence Transformers is not installed. Please run 'pip install toolium[ai]'"
                          " to use Sentence Transformers features")
    config = DriverWrappersPool.get_default_wrapper().config
    model_name = model_name or config.get_optional('AI', 'sentence_transformers_model', 'all-mpnet-base-v2')
    model = SentenceTransformer(model_name)
    similarity = float(model.similarity(model.encode(expected_text), model.encode(text)))
    similarity = 1 if similarity > 1 else similarity  # similarity can be slightly > 1 due to float precision
    logger.info(f"Sentence Transformers similarity: {similarity} between '{text}' and '{expected_text}'")
    return similarity


def openai_request(system_message, user_message, model_name=None, azure=False):
    """
    Make a request to OpenAI API (Azure or standard)

    :param system_message: system message to set the behavior of the assistant
    :param user_message: user message with the request
    :param model: model to use
    :param azure: whether to use Azure OpenAI or standard OpenAI
    :returns: response from OpenAI
    """
    if OpenAI is None:
        raise ImportError("OpenAI is not installed. Please run 'pip install toolium[ai]' to use OpenAI features")
    config = DriverWrappersPool.get_default_wrapper().config
    model_name = model_name or config.get_optional('AI', 'openai_model', 'gpt-4o-mini')
    logger.info(f"Calling to OpenAI API with model {model_name}")
    client = AzureOpenAI() if azure else OpenAI()
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
    )
    response = completion.choices[0].message.content
    logger.debug(f"OpenAI response: {response}")
    return response


def get_text_similarity_with_openai(text, expected_text, azure=False):
    """
    Return semantic similarity between two texts using OpenAI LLM

    :param text: string to compare
    :param expected_text: string with the expected text
    :param azure: whether to use Azure OpenAI or standard OpenAI
    :returns: tuple with similarity score between the two texts and explanation
    """
    system_message = (
        "You have to decide if the LLM answer is correct or not, comparing it with the expected answer."
        " Respond with a percentage between 0 and 1 (in <PERCENTAGE>) depending on how correct you think the answer is"
        " and with an explanation of why (in <EXPLANATION>), returning a json object:"
        " {\"similarity\": <PERCENTAGE>, \"explanation\": <EXPLANATION>}"
        " The answer is correct if it is semantically similar to the expected answer, it does not have to be identical,"
        " but its meaning should be similar."
    )
    user_message = (
        f"The expected answer is: {expected_text}."
        f" The LLM answer is: {text}."
    )
    response = openai_request(system_message, user_message, azure=azure)
    try:
        response = json.loads(response)
        similarity = float(response['similarity'])
        explanation = response['explanation']
    except (KeyError, ValueError, TypeError) as e:
        raise ValueError(f"Unexpected response format from OpenAI: {response}") from e
    logger.info(f"OpenAI LLM similarity: {similarity} between '{text}' and '{expected_text}'."
                f" LLM explanation: {explanation}")
    return similarity


def get_text_similarity_with_azure_openai(text, expected_text):
    """
    Return semantic similarity between two texts using Azure OpenAI LLM

    :param text: string to compare
    :param expected_text: string with the expected text
    :returns: tuple with similarity score between the two texts and explanation
    """
    return get_text_similarity_with_openai(text, expected_text, azure=True)


def assert_text_similarity(text, expected_texts, threshold, similarity_method=None):
    """
    Get similarity between one text and a list of expected texts and assert if any of the expected texts is similar.

    :param text: string to compare
    :param expected_texts: string or list of strings with the expected texts
    :param threshold: minimum similarity score to consider texts similar
    :param similarity_method: method to use for text comparison ('spacy', 'sentence_transformers', 'openai'
                              or 'azure_openai')
    """
    config = DriverWrappersPool.get_default_wrapper().config
    similarity_method = similarity_method or config.get_optional('AI', 'text_similarity_method', 'spacy')
    expected_texts = [expected_texts] if isinstance(expected_texts, str) else expected_texts
    error_message = ""
    for expected_text in expected_texts:
        try:
            similarity = globals()[f'get_text_similarity_with_{similarity_method}'](text, expected_text)
        except KeyError:
            raise ValueError(f"Unknown similarity_method: '{similarity_method}', please use 'spacy',"
                             f" 'sentence_transformers', 'openai' or 'azure_openai'")

        texts_message = f"Received text: {text}\nExpected text: {expected_text}"
        if similarity < threshold:
            error_message = f'{error_message}\n' if error_message else ""
            error_message = (f"{error_message}Similarity between received and expected texts"
                             f" is below threshold: {similarity} < {threshold}\n{texts_message}")
        else:
            logger.info(f"Similarity between received and expected texts"
                        f" is above threshold: {similarity} >= {threshold}\n{texts_message}")
            return

    # Any expected text did not meet the threshold
    logger.error(error_message)
    assert False, error_message
