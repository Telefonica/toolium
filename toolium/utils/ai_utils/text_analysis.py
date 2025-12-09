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
import logging

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    SentenceTransformer = None

from toolium.utils.ai_utils.openai import openai_request
from toolium.driver_wrappers_pool import DriverWrappersPool

# Configure logger
logger = logging.getLogger(__name__)

def build_system_message(characteristics):
    """
    Build system message for text criteria analysis prompt.

    :param characteristics: list of target characteristics to evaluate
    """
    feature_list = "\n".join(f"- {c}" for c in characteristics)
    base_prompt = f"""
        You are an assistant that scores how well a given text matches a set of target characteristics and returns a JSON object.

        You will receive a user message that contains ONLY the text to analyze.

        Target characteristics:
        {feature_list}

        Tasks:
        1) For EACH characteristic, decide how well the text satisfies it on a scale from 0.0 (does not satisfy it at all) to 1.0 (perfectly satisfies it). Consider style, tone and content when relevant.
        2) Only for each low scored characteristic (<=0.2), output:
           - "name": the exact characteristic name as listed above.
           - "score": a float between 0.0 and 0.2.
        3) Compute an overall score "overall_match" between 0.0 and 1.0 that summarizes how well the text matches the whole set. It does not have to be a simple arithmetic mean, but must still be in [0.0, 1.0].
        4) Produce a "data" object that can contain extra structured analysis sections:
           - "data" MUST always be present.
           - "data" MUST be a JSON object.
           - Each key in "data" is the title/name of a section (e.g. "genres", "entities", "style_breakdown").
           - Each value is a JSON array (the structure of its objects will be defined by additional system instructions).

        Output format (IMPORTANT):
        Return ONLY a single valid JSON object with this exact top-level structure and property names:

        {{
          "overall_match": float,
          "features": [
            {{
              "name": string,
              "score": float
            }}
          ],
          "data": {{
            "<section_title>": [
              {{}}
            ]
          }}
        }}

        Constraints:
        - The "data" field must ALWAYS be present. If there are no extra sections, it MUST be: "data": {{}}.
        - Use a dot as decimal separator (e.g. 0.75, not 0,75).
        - Use at most 2 decimal places for all scores.
        - Do NOT include any text outside the JSON (no Markdown, no comments, no explanations).
        - If a characteristic is not applicable to the text, give it a low score (<= 0.2).
        """
    return base_prompt.strip()


def get_text_criteria_analysis_openai(text_input, target_features, extra_tasks=None, model_name=None, azure=False, **kwargs):
    """
    Get text criteria analysis using Azure OpenAI. To analyze how well a given text
    matches a set of target characteristics.
    The response is a structured JSON object with overall match score, individual feature scores,
    and additional data sections.

    :param text_input: text to analyze
    :param target_features: list of target characteristics to evaluate
    :param extra_tasks: additional system messages for extra analysis sections (optional)
    :param model_name: name of the Azure OpenAI model to use
    :param azure: whether to use Azure OpenAI or standard OpenAI
    :param kwargs: additional parameters to be used by Azure OpenAI client
    :returns: response from Azure OpenAI
    """
    # Build prompt using base prompt and target features
    system_message = build_system_message(target_features)
    msg = [system_message]
    if extra_tasks:
        if isinstance(extra_tasks, list):
            for task in extra_tasks:
                msg.append(task)
        else:
            msg.append(extra_tasks)
    return openai_request(system_message, text_input, model_name, azure, **kwargs)


def get_text_criteria_analysis_sentence_transformers(text_input, target_features, extra_tasks=None,
                                                     model_name=None, azure=True, **kwargs):
    """
    Get text criteria analysis using Sentence Transformers. To analyze how well a given text
    matches a set of target characteristics.

    :param text_input: text to analyze
    :param target_features: list of target characteristics to evaluate
    :param extra_tasks: additional system messages for extra analysis sections (not used here, for compatibility)
    :param model_name: name of the Sentence Transformers model to use
    :param azure: whether to use Azure OpenAI or standard OpenAI (not used here, for compatibility)
    :param kwargs: additional parameters to be used by Sentence Transformers client
    """
    if SentenceTransformer is None:
        raise ImportError("Sentence Transformers is not installed. Please run 'pip install toolium[ai]'"
                          " to use Sentence Transformers features")
    config = DriverWrappersPool.get_default_wrapper().config
    model_name = model_name or config.get_optional('AI', 'sentence_transformers_model', 'all-mpnet-base-v2')
    model = SentenceTransformer(model_name, **kwargs)
    # Pre-compute feature embeddings
    feature_embs = model.encode([f for f in target_features], normalize_embeddings=True)
    # text_input embedding
    text_emb = model.encode(text_input, normalize_embeddings=True)
    # Computes cosine-similarities between the text and features tensors (range [-1, 1])
    sims = util.cos_sim(text_emb, feature_embs)[0].tolist()
    results = []
    # Generate contracted results
    for f, sim in zip(target_features, sims):
        # Normalize similarity from [-1, 1] to [0, 1]
        score = (sim + 1.0) / 2.0
        results.append({
            "name": f,
            "score": round(score, 2),
        })

    # overall score as average of feature scores
    overall = sum(r["score"] for r in results) / len(results)

    return {
        "overall_match": round(overall, 2),
        "features": results,
        "data": {}
    }
