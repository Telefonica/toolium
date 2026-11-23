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
        1) Evaluate every characteristic on a scale from 0.0 (does not satisfy it at all) to 1.0 (perfectly satisfies it). Consider style, tone and content when relevant.
        2) For each characteristic with a score strictly below 0.2, output:
           - "name": the exact characteristic name as listed above.
           - "score": a float between 0.0 and 0.2.
        3) Compute an overall score "overall_match" between 0.0 and 1.0 that summarizes
           how well the text matches the complete set of characteristics. Consider all
           characteristics, giving more weight to significant deficiencies. The score does
           not need to be an arithmetic mean, but must be consistent with the individual
           scores and remain within [0.0, 1.0].

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
        - Do NOT include scores for characteristics with scores greater than or equal to 0.2 in the features list.
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
    response, _ = openai_request(system_message, text_input, model_name, azure, **kwargs)
    return response


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
    if (not isinstance(overall_match, (int, float)) or isinstance(overall_match, bool)
            or not 0.0 <= overall_match <= 1.0):
        raise AssertionError(f'Invalid overall_match: {overall_match!r}')
    if overall_match < threshold:
        error = (
            f'Text criteria analysis failed: overall match {overall_match} '
            f'is below threshold {threshold}\n'
            f'Failed features: {analysis.get("features", [])}'
        )
        logger.error(error)
        raise AssertionError(error)
    logger.info(
        'Text criteria analysis passed: overall match %s is above threshold %s. Low scored features: %s',
        float(overall_match),
        threshold,
        analysis.get('features', []),
    )
