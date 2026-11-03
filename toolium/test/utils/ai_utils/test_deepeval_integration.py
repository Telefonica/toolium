"""Integration tests for DeepEval against real OpenAI providers."""

import os

import pytest
from dotenv import load_dotenv

from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.utils.ai_utils.deepeval import (
    get_text_similarity_with_deepeval,
)

load_dotenv(override=True)

AZURE_REQUIRED_VARS = ('AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_ENDPOINT', 'OPENAI_API_VERSION')
AZURE_AVAILABLE = all(os.getenv(name) for name in AZURE_REQUIRED_VARS)


def _configure_ai(**values):
    config = DriverWrappersPool.get_default_wrapper().config
    try:
        config.add_section('AI')
    except Exception:
        pass
    for key, value in values.items():
        config.set('AI', key, value)


@pytest.fixture(scope='module', autouse=True)
def configure_models():
    _configure_ai(
        openai_model=os.getenv('DEEPEVAL_OPENAI_MODEL', 'gpt-4o-mini'),
        azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
        azure_api_key=os.getenv('AZURE_OPENAI_API_KEY'),
        api_version=os.getenv('OPENAI_API_VERSION'),
        azure_deployment=os.getenv('AZURE_OPENAI_DEPLOYMENT', os.getenv('AZURE_OPENAI_MODEL', 'gpt-4o-mini')),
    )


@pytest.mark.skipif(not AZURE_AVAILABLE, reason='Azure OpenAI credentials are not configured')
def test_text_similarity_with_real_azure_openai():
    similarity = get_text_similarity_with_deepeval(
        'Today is sunny',
        'The sun is shining today',
        provider='azure',
    )

    assert 0.0 <= similarity <= 1.0
    assert similarity >= 0.6
