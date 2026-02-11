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

from toolium.utils.ai_utils.openai import openai_request

# Configure logger
logger = logging.getLogger(__name__)


def build_system_message(characteristics):
    """
    Build system message for text criteria analysis prompt.

    :param characteristics: list of target characteristics to evaluate
    """
    feature_list = '\n'.join(f'- {c}' for c in characteristics)
    base_prompt = f"""
        You are an assistant that scores how well a given text matches a set of target characteristics and returns a JSON object.

        You will receive a user message that contains ONLY the text to analyze.

        Target characteristics:
        {feature_list}

        Tasks:
        1) For EACH characteristic, decide how well the text satisfies it on a scale from 0.0 (does not satisfy it at all) to 1.0 (perfectly satisfies it). Consider style, tone and content when relevant.
        2) ONLY for each low scored characteristic (<=0.2), output:
           - "name": the exact characteristic name as listed above.
           - "score": a float between 0.0 and 0.2.
        3) Compute an overall score "overall_match" between 0.0 and 1.0 that summarizes how well the text matches the whole set. It does not have to be a simple arithmetic mean, but must still be in [0.0, 1.0].

        Output format (IMPORTANT):
        Return ONLY a single valid JSON object with this exact top-level structure and property names:

        {{
          "overall_match": float,
          "features": [
            {{
              "name": string,
              "score": float
            }}
          ]
        }}

        Constraints:
        - Do NOT include scores for high valued (<=0.2) features at features list.
        - Use a dot as decimal separator (e.g. 0.75, not 0,75).
        - Use at most 2 decimal places for all scores.
        - Do NOT include any text outside the JSON (no Markdown, no comments, no explanations).
        - If a characteristic is not applicable to the text, give it a low score (<= 0.2).
        """  # noqa: E501
    return base_prompt.strip()


def get_text_criteria_analysis(text_input, text_criteria, model_name=None, azure=False, **kwargs):
    """
    Get text criteria analysis using OpenAI. To analyze how well a given text matches a set of target characteristics.
    The response is a structured JSON object with overall match score, individual feature scores for
    low scored features.

    :param text_input: text to analyze
    :param text_criteria: list of target characteristics to evaluate
    :param model_name: name of the OpenAI model to use
    :param azure: whether to use Azure OpenAI or standard OpenAI
    :param kwargs: additional parameters to be used by OpenAI client
    :returns: response from OpenAI
    """
    # Build prompt using base prompt and target features
    system_message = build_system_message(text_criteria)
    return openai_request(system_message, text_input, model_name, azure, **kwargs)


def assert_text_criteria(text_input, text_criteria, threshold, model_name=None, azure=False, **kwargs):
    """
    Get text criteria analysis and assert if overall match score is above threshold.

    :param text_input: text to analyze
    :param text_criteria: list of target characteristics to evaluate
    :param threshold: minimum overall match score to consider the text acceptable
    :param model_name: name of the OpenAI model to use
    :param azure: whether to use Azure OpenAI or standard OpenAI
    :param kwargs: additional parameters to be used by OpenAI client
    :raises AssertionError: if overall match score is below threshold
    """
    analysis = json.loads(get_text_criteria_analysis(text_input, text_criteria, model_name, azure, **kwargs))
    overall_match = analysis.get('overall_match', 0.0)
    if overall_match < threshold:
        error = (
            f'Text criteria analysis failed: overall match {overall_match} '
            f'is below threshold {threshold}\n'
            f'Failed features: {analysis.get("features", [])}'
        )
        logger.error(error)
        raise AssertionError(error)
    logger.info(
        f'Text criteria analysis passed: overall match {overall_match} '
        f'is above threshold {threshold}.'
        f'Low scored features: {analysis.get("features", [])}',
    )
