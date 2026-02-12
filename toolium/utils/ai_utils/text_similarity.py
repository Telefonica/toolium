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

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.utils.ai_utils.openai import openai_request
from toolium.utils.ai_utils.spacy import get_spacy_model, preprocess_with_ud_negation

# Configure logger
logger = logging.getLogger(__name__)


def get_text_similarity_with_spacy(text, expected_text, model_name=None, **kwargs):
    """
    Return similarity between two texts using spaCy.
    This method normalize both texts before comparing them.

    :param text: string to compare
    :param expected_text: string with the expected text
    :param model_name: name of the spaCy model to use
    :param kwargs: additional parameters to be used by spaCy (disable, exclude, etc.)
    :returns: similarity score between the two texts
    """
    # NOTE: spaCy similarity performance can be enhanced using some strategies like:
    # - Normalizing texts (lowercase, extra points, etc.)
    # - Use only models that include word vectors (e.g., 'en_core_news_md' or 'en_core_news_lg')
    # - Preprocessing texts. Now we only preprocess negations.
    config = DriverWrappersPool.get_default_wrapper().config
    model_name = model_name or config.get_optional('AI', 'spacy_model', 'en_core_web_md')
    model = get_spacy_model(model_name, **kwargs)
    if model is None:
        raise ImportError("spaCy is not installed. Please run 'pip install toolium[ai]' to use spaCy features")
    text = model(preprocess_with_ud_negation(text, model))
    expected_text = model(preprocess_with_ud_negation(expected_text, model))
    similarity = model(text).similarity(model(expected_text))
    logger.info("spaCy similarity: %s between '%s' and '%s'", similarity, text, expected_text)
    return similarity


def get_text_similarity_with_sentence_transformers(text, expected_text, model_name=None, **kwargs):
    """
    Return similarity between two texts using Sentence Transformers

    :param text: string to compare
    :param expected_text: string with the expected text
    :param model_name: name of the Sentence Transformers model to use
    :param kwargs: additional parameters to be used by SentenceTransformer (modules, device, prompts, etc.)
    :returns: similarity score between the two texts
    """
    if SentenceTransformer is None:
        raise ImportError(
            "Sentence Transformers is not installed. Please run 'pip install toolium[ai]'"
            ' to use Sentence Transformers features',
        )
    config = DriverWrappersPool.get_default_wrapper().config
    model_name = model_name or config.get_optional('AI', 'sentence_transformers_model', 'all-mpnet-base-v2')
    model = SentenceTransformer(model_name, **kwargs)
    similarity = float(model.similarity(model.encode(expected_text), model.encode(text)))
    # similarity can be slightly > 1 due to float precision
    similarity = 1 if similarity > 1 else similarity
    logger.info("Sentence Transformers similarity: %s between '%s' and '%s'", similarity, text, expected_text)
    return similarity


def get_text_similarity_with_openai(text, expected_text, model_name=None, azure=False, **kwargs):
    """
    Return semantic similarity between two texts using OpenAI LLM

    :param text: string to compare
    :param expected_text: string with the expected text
    :param model_name: name of the OpenAI model to use
    :param azure: whether to use Azure OpenAI or standard OpenAI
    :param kwargs: additional parameters to be used by OpenAI client
    :returns: tuple with similarity score between the two texts and explanation
    """
    system_message = (
        'You have to decide if the LLM answer is correct or not, comparing it with the expected answer.'
        ' Respond with a percentage between 0 and 1 (in <PERCENTAGE>) depending on how correct you think the answer is'
        ' and with an explanation of why (in <EXPLANATION>), returning a json object:'
        ' {"similarity": <PERCENTAGE>, "explanation": <EXPLANATION>}'
        ' The answer is correct if it is semantically similar to the expected answer, it does not have to be identical,'
        ' but its meaning should be similar.'
    )
    user_message = f'The expected answer is: {expected_text}. The LLM answer is: {text}.'
    response = openai_request(system_message, user_message, model_name, azure, **kwargs)
    try:
        response = json.loads(response)
        similarity = float(response['similarity'])
        explanation = response['explanation']
    except (KeyError, ValueError, TypeError) as e:
        raise ValueError(f'Unexpected response format from OpenAI: {response}') from e
    logger.info("OpenAI LLM similarity: %s between '%s' and '%s'", similarity, text, expected_text)
    logger.info('OpenAI LLM explanation: %s', explanation)
    return similarity


def get_text_similarity_with_azure_openai(text, expected_text, model_name=None, **kwargs):
    """
    Return semantic similarity between two texts using Azure OpenAI LLM

    :param text: string to compare
    :param expected_text: string with the expected text
    :param model_name: name of the Azure OpenAI model to use
    :param kwargs: additional parameters to be used by Azure OpenAI client
    :returns: tuple with similarity score between the two texts and explanation
    """
    return get_text_similarity_with_openai(text, expected_text, model_name, azure=True, **kwargs)


def assert_text_similarity(text, expected_texts, threshold, similarity_method=None, model_name=None, **kwargs):
    """
    Get similarity between one text and a list of expected texts and assert if any of the expected texts is similar.

    :param text: string to compare
    :param expected_texts: string or list of strings with the expected texts
    :param threshold: minimum similarity score to consider texts similar
    :param similarity_method: method to use for text comparison ('spacy', 'sentence_transformers', 'openai'
                              or 'azure_openai')
    :param model_name: model name to use for the similarity method
    :param kwargs: additional parameters to be used by comparison methods
    """
    config = DriverWrappersPool.get_default_wrapper().config
    similarity_method = similarity_method or config.get_optional('AI', 'text_similarity_method', 'spacy')
    expected_texts = [expected_texts] if isinstance(expected_texts, str) else expected_texts
    error_message = ''
    for expected_text in expected_texts:
        try:
            similarity = globals()[f'get_text_similarity_with_{similarity_method}'](
                text,
                expected_text,
                model_name,
                **kwargs,
            )
        except KeyError as e:
            raise ValueError(
                f"Unknown similarity_method: '{similarity_method}', please use 'spacy',"
                f" 'sentence_transformers', 'openai' or 'azure_openai'",
            ) from e

        texts_message = f'Received text: {text}\nExpected text: {expected_text}'
        if similarity < threshold:
            error_message = f'{error_message}\n' if error_message else ''
            error_message = (
                f'{error_message}Similarity between received and expected texts'
                f' is below threshold: {similarity} < {threshold}\n{texts_message}'
            )
        else:
            logger.info(
                'Similarity between received and expected texts is above threshold: %s >= %s\n%s',
                similarity,
                threshold,
                texts_message,
            )
            return

    # Any expected text did not meet the threshold
    logger.error(error_message)
    raise AssertionError(error_message)
