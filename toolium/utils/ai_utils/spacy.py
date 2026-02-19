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
from functools import lru_cache

# AI library imports must be optional to allow installing Toolium without `ai` extra dependency
try:
    import spacy
except ImportError:
    spacy = None


logger = logging.getLogger(__name__)


@lru_cache(maxsize=8)
def get_spacy_model(model_name, **kwargs):
    """
    get spaCy model.
    This method uses lru cache to get spaCy model to improve performance.

    :param model_name: spaCy model name
    :param kwargs: additional parameters to be used by spaCy (disable, exclude, etc.)
    :return: spaCy model
    """
    if spacy is None:
        return None
    return spacy.load(model_name, **kwargs)


def is_negator(tok):
    """
    Check if a token is a negator using Universal Dependencies guidelines
    Note: some languages may have different negation markers. That's why we use UD guidelines.

    :param tok: spaCy token
    """
    # Universal Dependencies negation detection (e.g., Spanish "no", "nunca", etc.)
    if tok.dep_ == 'neg':
        return True
    # Some languages use Polarity=Neg for negation words (e.g., Spanish "no", "sin", etc.)
    if 'Neg' in tok.morph.get('Polarity'):
        return True
    # Some languages use PronType=Neg for negation words (e.g., Spanish "nunca", "nadie", etc.)
    if 'Neg' in tok.morph.get('PronType'):
        return True
    return False


def preprocess_with_ud_negation(text, nlp):
    """
    Preprocess text using Universal Dependencies negation handling.
    It tags negated words with "NEG_" prefix and replaces negators with "NEGATOR" token.
    Stop words are removed.

    :param text: input text
    :param nlp: spaCy language model
    """
    doc = nlp(text)
    # 1) Negators indexes
    neg_idxs = {t.i for t in doc if is_negator(t)}
    # 2) Negated heads indexes
    negated_heads = set()
    for i in neg_idxs:
        head = doc[i].head
        if head.is_alpha and not head.is_stop:
            negated_heads.add(head.i)

    toks = []
    for t in doc:
        if not t.is_alpha:
            continue
        # Keep negators as is
        if is_negator(t):
            toks.append('NEGATOR')
            continue
        if t.is_stop:
            continue

        lemma = t.lemma_.lower()
        if t.i in negated_heads:
            toks.append('NEG_' + lemma)
        else:
            toks.append(lemma)
    return ' '.join(toks)
