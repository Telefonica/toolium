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

from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.utils.ai_utils.spacy import get_spacy_model

logger = logging.getLogger(__name__)


def get_text_readability_with_spacy(text, technical_chars=None, model_name=None, **kwargs):
    """
    Return the readability score of a text using spaCy.

    :param text: string to assess readability
    :param model_name: name of the spaCy model to use
    :param kwargs: additional parameters to be used by spaCy (disable, exclude, etc.)
    :returns: readability score between 0 and 1
    """
    # NOTE: spaCy readability performance can be enhanced using some strategies like:
    # - Use only models that include word vectors (e.g., 'en_core_news_md' or 'en_core_news_lg')
    config = DriverWrappersPool.get_default_wrapper().config
    model_name = model_name or config.get_optional('AI', 'spacy_model', 'en_core_web_md')
    model = get_spacy_model(model_name, **kwargs)
    if model is None:
        raise ImportError("spaCy is not installed. Please run 'pip install toolium[ai]' to use spaCy features")

    # Basic length and word count check: a friendly message should contain at least two words.
    word_tokens = text.split()
    if len(word_tokens) < 2:
        return 0.0

    # Counters for problematic categories
    doc = model(text)
    total_tokens = len(doc)
    non_linguistic_tokens_count = 0
    technical_chars = technical_chars or ['/', '|', '-', '_', '=', ':', '[', ']', '{', '}']

    for token in doc:
        # Check:
        #  - Out-Of-Vocabulary (OOV) tokens that are not recognized as standard words
        #  - POS Tags that indicate non-linguistic content or noise:
        #       SYM: Symbol (common in code traces or error structures)
        #       X: Other (typical of unrecognized characters or codes)
        #  - Punctuation or symbols that are overly frequent in error codes but not normal sentences
        is_suspicious_symbol = token.is_oov or token.pos_ in ['SYM', 'X'] or token.text in technical_chars

        if is_suspicious_symbol:
            non_linguistic_tokens_count += 1

    readability = (total_tokens - non_linguistic_tokens_count) / total_tokens

    logger.info('spaCy readability: %s', readability)
    return readability


def assert_text_readability(text, threshold, technical_chars=None, readability_method=None, model_name=None, **kwargs):
    """
    Get the readability of a text and assert if it is above a given threshold.

    :param text: string to compare
    :param threshold: minimum readability score to consider the text readable
    :param technical_chars: list of technical characters to consider as non-linguistic content
    :param readability_method: method to use for text readability ('spacy')
    :param model_name: model name to use for the readability method
    :param kwargs: additional parameters to be used by comparison methods
    """
    config = DriverWrappersPool.get_default_wrapper().config
    readability_method = readability_method or config.get_optional('AI', 'text_readability_method', 'spacy')
    try:
        readability = globals()[f'get_text_readability_with_{readability_method}'](
            text,
            technical_chars,
            model_name,
            **kwargs,
        )
    except KeyError as e:
        raise ValueError(f"Unknown readability_method: '{readability_method}', please use 'spacy'") from e

    texts_message = f'Received text: {text}'
    if readability < threshold:
        error_message = f'Text readability is below threshold: {readability} < {threshold}\n{texts_message}'
        logger.error(error_message)
        raise AssertionError(error_message)

    logger.info('Text readability is above threshold: %s >= %s\n%s', readability, threshold, texts_message)
    return
