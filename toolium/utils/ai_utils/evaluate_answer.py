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

import inspect
import json
import logging

try:
    from pydantic import BaseModel
except ImportError:
    BaseModel = None

from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.utils.ai_utils.openai import openai_request

logger = logging.getLogger(__name__)


def _validate_model(model):
    """
    Validate that the provided model is a valid Pydantic BaseModel class with required fields.

    :param model: Pydantic model class to validate
    :return: The validated model class if valid, None otherwise
    """
    if model is None:
        return None

    if BaseModel is None:
        logger.warning('Pydantic not installed, ignoring response_format parameter')
        return None

    if not inspect.isclass(model) or not issubclass(model, BaseModel):
        logger.warning('Provided response_format is not a valid Pydantic BaseModel, ignoring response_format parameter')
        return None

    required_fields = {'similarity', 'explanation'}
    field_names = set(model.model_fields.keys())
    if not required_fields.issubset(field_names):
        logger.warning(
            'Provided response_format model does not have "similarity" and "explanation" fields,'
            ' ignoring response_format parameter'
        )
        return None

    return model


def get_answer_evaluation_with_openai(
    llm_answer, reference_answer, model_name=None, azure=False, question=None, response_format=None, **kwargs
):
    """
    Evaluate semantic similarity between an LLM answer an a reference answer using OpenAI LLM-as-a-Judge approach.
    Use this method if you need context awareness including the user's question and optionally
    a Pydantic structured criteria

    :param llm_answer: string to compare (LLM answer)
    :param reference_answer: string with the expected text
    :param model_name: name of the OpenAI model to use
    :param azure: whether to use Azure OpenAI or standard OpenAI
    :param question: optional question that both texts are answering (provides context)
    :param response_format: optional Pydantic model for structured output (requires pydantic and compatible model)
    :param kwargs: additional parameters to be used by OpenAI client (e.g., temperature=0.1 for consistency)
    :returns: similarity score between the two texts and full response to process extra fields
    """
    response_format = _validate_model(response_format)

    system_message = """You are an expert evaluator assessing if an LLM answer is semantically equivalent to an
    expected answer.

    Evaluate the LLM answer based on:
    - Semantic similarity: Does the LLM answer convey the same meaning as the expected answer,
    even if phrased differently?
    - Factual accuracy: How factually correct is it compared to the reference answer?
    - Completeness: How thoroughly does it address all aspects of the question, covering all the information
    from the reference answer?"""

    if question:
        system_message += """\n- Relevance: How well does it directly answer the specific question asked,
        giving no additional information"""

    if not response_format:
        system_message += """Respond with a JSON object:{"similarity": <PERCENTAGE>, "explanation": <EXPLANATION>}"""

    system_message += """
    Scoring guide:
    - 1.0: Perfect semantic match
    - 0.7-0.9: Similar meaning, minor differences
    - 0.4-0.6: Incomplete, partially similar with major differences
    - 0.0-0.3: Different, irrelevant or contradictory"""

    user_message = f"""
    Expected answer: "{reference_answer}"
    LLM answer: "{llm_answer}"
    """

    if question:
        user_message += f"""
    Question: "{question}"
    """

    if response_format:
        kwargs['response_format'] = response_format

    response, _ = openai_request(system_message, user_message, model_name, azure, **kwargs)

    try:
        if response_format and hasattr(response, 'similarity'):
            similarity = response.similarity
            explanation = response.explanation
        elif isinstance(response, dict):
            similarity = float(response['similarity'])
            explanation = response['explanation']
        else:
            response = json.loads(response)
            similarity = response['similarity']
            explanation = response['explanation']

        if not 0.0 <= similarity <= 1.0:
            logger.warning('Similarity score: %s  out of range [0,1], clamping', similarity)
            similarity = max(0.0, min(1.0, similarity))

    except (KeyError, ValueError, TypeError, json.JSONDecodeError) as e:
        raise ValueError(f'Unexpected response format from OpenAI: {response}') from e

    logger.info("OpenAI LLM-as-a-Judge similarity: %s between '%s' and '%s'", similarity, llm_answer, reference_answer)
    if question:
        logger.info("Question context: '%s'", question)
    logger.info('OpenAI LLM explanation: %s', explanation)
    return similarity, response


def get_answer_evaluation_with_azure_openai(
    llm_answer, reference_answer, model_name=None, question=None, response_format=None, **kwargs
):
    """
        Evaluate semantic similarity between an LLM answer an a reference answer using OpenAI LLM-as-a-Judge
        approach using Azure OpenAI.
    LLM
        :param llm_answer: string to compare
        :param reference_answer: string with the expected text
        :param model_name: name of the OpenAI model to use
        :param question: optional question that both texts are answering (provides context)
        :param response_format: optional Pydantic model for structured output (requires pydantic and compatible model)
        :param kwargs: additional parameters to be used by OpenAI client (e.g., temperature=0.1 for consistency)
        :returns: similarity score between the two texts and full response to process extra fields
    """
    return get_answer_evaluation_with_openai(
        llm_answer,
        reference_answer,
        question=question,
        model_name=model_name,
        response_format=response_format,
        azure=True,
        **kwargs,
    )


def assert_answer_evaluation(
    llm_answer,
    reference_answers,
    threshold,
    provider=None,
    model_name=None,
    question=None,
    response_format=None,
    **kwargs,
):
    """
    Evaluate semantic similarity between one text and a list of expected texts using LLM-as-a-Judge approach
    and assert if any of the expected texts meets the similarity threshold.

    :param llm_answer: string to compare (LLM answer)
    :param reference_answers: string or list of strings with the expected texts
    :param threshold: minimum similarity score to consider texts similar
    :param provider: method to use for evaluation ('openai' or 'azure_openai')
    :param model_name: model name to use for the evaluation method
    :param question: optional question that both texts are answering (provides context)
    :param response_format: optional Pydantic model for structured output (requires pydantic and compatible model)
    :param kwargs: additional parameters to be used by evaluation methods (e.g., temperature=0.1)
    """
    config = DriverWrappersPool.get_default_wrapper().config
    provider = provider or config.get_optional('AI', 'provider', 'openai')
    if provider not in ('openai', 'azure'):
        raise ValueError(
            f"Unknown provider: '{provider}', please use 'openai' or 'azure'",
        )

    provider = provider if provider == 'openai' else f'{provider}_openai'

    reference_answers = [reference_answers] if isinstance(reference_answers, str) else reference_answers
    error_message = ''

    for reference_answer in reference_answers:
        try:
            similarity, _ = globals()[f'get_answer_evaluation_with_{provider}'](
                llm_answer,
                reference_answer,
                model_name,
                question=question,
                response_format=response_format,
                **kwargs,
            )
        except KeyError as e:
            raise ValueError(
                f"Unknown provider: '{provider}', please use 'openai' or 'azure_openai'",
            ) from e

        texts_message = f'LLM answer: {llm_answer}\nReference answer: {reference_answer}'
        if question:
            texts_message += f'\nQuestion: {question}'

        if similarity < threshold:
            error_message = f'{error_message}\n' if error_message else ''
            error_message = (
                f'{error_message}Evaluation similarity between LLM answer and reference answer'
                f' is below threshold: {similarity} < {threshold}\n{texts_message}'
            )
        else:
            logger.info(
                'Evaluation similarity between LLM answer and reference answer is above threshold: %s >= %s\n%s',
                similarity,
                threshold,
                texts_message,
            )
            return

    # Any expected text did not meet the threshold
    logger.error(error_message)
    raise AssertionError(error_message)
