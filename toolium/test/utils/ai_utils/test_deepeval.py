"""Tests for the optional DeepEval integration."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import mock

import pytest
from deepeval.models import DeepEvalBaseLLM

from toolium.utils.ai_utils import deepeval

# Keep DeepEval's real validation even when the metric itself is mocked.
FakeTestCase = deepeval.LLMTestCase


def _metric(score, reason='', passed=None):
    return mock.Mock(
        score=score, reason=reason, is_successful=mock.Mock(return_value=score >= 0.7 if passed is None else passed)
    )


class FakeParams:
    INPUT = 'input'
    ACTUAL_OUTPUT = 'actual_output'
    EXPECTED_OUTPUT = 'expected_output'


@pytest.fixture(autouse=True)
def deepeval_models():
    with (
        mock.patch.object(deepeval, 'GPTModel', return_value=mock.Mock()),
        mock.patch.object(deepeval, 'AzureOpenAIModel', return_value=mock.Mock()),
    ):
        yield


@pytest.fixture
def deepeval_installed():
    with mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase):
        yield


def test_get_model_with_openai_configuration():
    config = mock.Mock()
    config.get_optional.side_effect = lambda _section, key, default=None: {
        'openai_model': 'configured-model',
        'openai_api_key': 'configured-key',
        'openai_temperature': 0.2,
    }.get(key, default)
    wrapper = mock.Mock(config=config)
    with (
        mock.patch.object(deepeval.DriverWrappersPool, 'get_default_wrapper', return_value=wrapper),
        mock.patch.object(deepeval, 'GPTModel', return_value=mock.sentinel.model) as model_class,
    ):
        model = deepeval._get_model(None, None, {'custom_option': True})

    assert model is mock.sentinel.model
    model_class.assert_called_once_with(
        model='configured-model',
        api_key='configured-key',
        temperature=0.2,
        custom_option=True,
    )


def test_get_model_with_azure_configuration():
    config = mock.Mock()
    config.get_optional.side_effect = lambda _section, key, default=None: {
        'provider': 'azure',
        'openai_model': 'configured-model',
        'azure_api_key': 'azure-key',
        'azure_endpoint': 'https://example.openai.azure.com',
        'azure_deployment': 'configured-deployment',
        'api_version': '2025-01-01-preview',
        'azure_temperature': 0.1,
    }.get(key, default)
    wrapper = mock.Mock(config=config)
    with (
        mock.patch.object(deepeval.DriverWrappersPool, 'get_default_wrapper', return_value=wrapper),
        mock.patch.object(deepeval, 'AzureOpenAIModel', return_value=mock.sentinel.model) as model_class,
    ):
        model = deepeval._get_model(None, None, {'custom_option': True})

    assert model is mock.sentinel.model
    model_class.assert_called_once_with(
        model='configured-model',
        api_key='azure-key',
        base_url='https://example.openai.azure.com',
        deployment_name='configured-deployment',
        api_version='2025-01-01-preview',
        temperature=0.1,
        custom_option=True,
    )


def test_get_model_explicit_arguments_override_configuration():
    config = mock.Mock()
    config.get_optional.return_value = 'configured-value'
    wrapper = mock.Mock(config=config)
    with (
        mock.patch.object(deepeval.DriverWrappersPool, 'get_default_wrapper', return_value=wrapper),
        mock.patch.object(deepeval, 'GPTModel', return_value=mock.sentinel.model) as model_class,
    ):
        deepeval._get_model('openai', 'explicit-model', {})

    assert model_class.call_args.kwargs['model'] == 'explicit-model'


def test_get_model_rejects_unknown_provider():
    config = mock.Mock()
    config.get_optional.return_value = 'unsupported'
    wrapper = mock.Mock(config=config)
    with mock.patch.object(deepeval.DriverWrappersPool, 'get_default_wrapper', return_value=wrapper):
        with pytest.raises(ValueError, match="Unknown provider: 'unsupported'"):
            deepeval._get_model(None, None, {})


@pytest.mark.parametrize(
    ('sections', 'expected_model', 'expected_key', 'expected_temperature'),
    [
        ({}, 'gpt-4o-mini', None, 0.0),
        (
            {'AI': {'openai_model': 'agent', 'openai_api_key': 'shared', 'openai_temperature': '0.7'}},
            'agent',
            'shared',
            '0.7',
        ),
        (
            {
                'AI': {'openai_model': 'agent', 'openai_api_key': 'shared', 'openai_temperature': '0.7'},
                'DeepEval': {'openai_model': 'judge', 'openai_temperature': '0'},
            },
            'judge',
            'shared',
            '0',
        ),
        ({'DeepEval': {'openai_model': 'judge', 'openai_api_key': 'judge-key'}}, 'judge', 'judge-key', 0.0),
    ],
)
def test_get_model_configuration_precedence(sections, expected_model, expected_key, expected_temperature):
    from toolium.config_parser import ExtendedConfigParser

    config = ExtendedConfigParser()
    config.read_dict(sections)
    with (
        mock.patch.object(deepeval.DriverWrappersPool, 'get_default_wrapper', return_value=mock.Mock(config=config)),
        mock.patch.object(deepeval, 'GPTModel') as model_class,
    ):
        deepeval._get_model(None, None, {})
    model_class.assert_called_once_with(model=expected_model, api_key=expected_key, temperature=expected_temperature)


def test_get_model_resolves_provider_before_connection_and_allows_explicit_overrides():
    from toolium.config_parser import ExtendedConfigParser

    config = ExtendedConfigParser()
    config.read_dict(
        {
            'AI': {'provider': 'openai', 'azure_api_key': 'shared-azure', 'azure_temperature': '0.7'},
            'DeepEval': {
                'provider': 'azure',
                'openai_model': 'judge',
                'azure_endpoint': 'https://judge',
                'api_version': 'version',
            },
        }
    )
    with (
        mock.patch.object(deepeval.DriverWrappersPool, 'get_default_wrapper', return_value=mock.Mock(config=config)),
        mock.patch.object(deepeval, 'AzureOpenAIModel') as model_class,
    ):
        deepeval._get_model(None, 'explicit-model', {'temperature': 0.1, 'api_key': 'explicit-key'})
    model_class.assert_called_once_with(
        model='explicit-model',
        api_key='explicit-key',
        temperature=0.1,
        base_url='https://judge',
        deployment_name='explicit-model',
        api_version='version',
    )


def test_evaluate_contextual_with_metric_config():
    metric = _metric(score=0.9, reason='Supported')
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'FaithfulnessMetric', return_value=metric) as metric_class,
        mock.patch.object(deepeval, '_get_model', return_value=mock.sentinel.model),
    ):
        result = deepeval.evaluate_contextual_with_deepeval(
            'question', 'answer', ['context'], metric_config={'faithfulness': {'threshold': 0.8}}
        )

    assert result['passed'] is True
    metric_class.assert_called_once_with(threshold=0.8, model=mock.sentinel.model)


@pytest.mark.parametrize(
    ('metric_name', 'metric_attribute'),
    [
        ('faithfulness', 'FaithfulnessMetric'),
        ('contextual_relevancy', 'ContextualRelevancyMetric'),
        ('contextual_precision', 'ContextualPrecisionMetric'),
        ('contextual_recall', 'ContextualRecallMetric'),
    ],
)
def test_metric_config_passes_common_options(metric_name, metric_attribute):
    metric = _metric(score=0.9, reason='Good')
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, metric_attribute, return_value=metric) as metric_class,
        mock.patch.object(deepeval, '_get_model', return_value=mock.sentinel.model),
    ):
        deepeval.evaluate_contextual_with_deepeval(
            'question',
            'answer',
            ['context'],
            expected_output='expected' if metric_name in {'contextual_precision', 'contextual_recall'} else None,
            metric_config={
                metric_name: {
                    'threshold': 0.8,
                    'include_reason': False,
                    'async_mode': False,
                    'strict_mode': True,
                    'verbose_mode': True,
                    'evaluation_template': mock.sentinel.template,
                }
            },
        )

    metric_class.assert_called_once_with(
        threshold=0.8,
        model=mock.sentinel.model,
        include_reason=False,
        async_mode=False,
        strict_mode=True,
        verbose_mode=True,
        evaluation_template=mock.sentinel.template,
    )


def test_faithfulness_metric_config_passes_specific_options():
    metric = _metric(score=0.9, reason='Good')
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'FaithfulnessMetric', return_value=metric) as metric_class,
        mock.patch.object(deepeval, '_get_model', return_value=mock.sentinel.model),
    ):
        deepeval.evaluate_contextual_with_deepeval(
            'question',
            'answer',
            ['context'],
            metric_config={
                'faithfulness': {
                    'threshold': 0.8,
                    'truths_extraction_limit': 10,
                    'penalize_ambiguous_claims': True,
                }
            },
        )

    metric_class.assert_called_once_with(
        threshold=0.8,
        model=mock.sentinel.model,
        truths_extraction_limit=10,
        penalize_ambiguous_claims=True,
    )


def test_summarization_passes_specific_options():
    metric = _metric(score=0.9, reason='Complete')
    with mock.patch.object(deepeval, 'SummarizationMetric', return_value=metric) as metric_class:
        deepeval.get_summarization_with_deepeval(
            'The order is ready.',
            'Order ready.',
            n=3,
            assessment_questions=['Does it include the status?'],
            truths_extraction_limit=10,
        )
    metric_class.assert_called_once_with(
        threshold=0.7,
        model=mock.ANY,
        n=3,
        assessment_questions=['Does it include the status?'],
        truths_extraction_limit=10,
    )


def test_contextual_rejects_summary_metric():
    with pytest.raises(ValueError, match=r'Unknown contextual metric.*summarization'):
        deepeval.evaluate_contextual_with_deepeval(
            'question',
            'summary',
            ['source'],
            metric_config={'summarization': {'threshold': 0.8}},
        )


def test_metric_config_validates_configuration():
    with pytest.raises(ValueError, match='Missing threshold'):
        deepeval.evaluate_contextual_with_deepeval('question', 'answer', [], metric_config={'faithfulness': {}})
    with pytest.raises(ValueError, match='between 0 and 1'):
        deepeval.evaluate_contextual_with_deepeval(
            'question', 'answer', [], metric_config={'faithfulness': {'threshold': 1.1}}
        )
    with pytest.raises(ValueError, match='expected_output is required'):
        deepeval.evaluate_contextual_with_deepeval(
            'question', 'answer', [], metric_config={'contextual_recall': {'threshold': 0.7}}
        )


def test_evaluate_contextual_with_one_metric():
    metric = _metric(score=0.9, reason='Supported')
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'FaithfulnessMetric', return_value=metric) as metric_class,
        mock.patch.object(deepeval, '_get_model', return_value=mock.sentinel.model),
    ):
        result = deepeval.evaluate_contextual_with_deepeval(
            'question', 'answer', [{'source': 'context'}], metrics='faithfulness', threshold=0.8
        )

    assert result == {
        'results': {'faithfulness': {'score': 0.9, 'reason': 'Supported', 'passed': True}},
        'passed': True,
    }
    metric_class.assert_called_once_with(threshold=0.8, model=mock.sentinel.model)


def test_evaluate_contextual_with_multiple_metrics_and_thresholds():
    metrics = [_metric(score=0.9, reason='Relevant'), _metric(score=0.6, reason='Incomplete')]
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'ContextualRelevancyMetric', return_value=metrics[0]) as relevancy,
        mock.patch.object(deepeval, 'FaithfulnessMetric', return_value=metrics[1]) as faithfulness,
        mock.patch.object(deepeval, '_get_model', return_value=mock.sentinel.model),
    ):
        result = deepeval.evaluate_contextual_with_deepeval(
            'question',
            'answer',
            ['context'],
            metrics=['contextual_relevancy', 'faithfulness'],
            threshold={'contextual_relevancy': 0.8, 'faithfulness': 0.7},
        )

    assert result['results']['contextual_relevancy']['passed'] is True
    assert result['results']['faithfulness']['passed'] is False
    assert result['passed'] is False
    relevancy.assert_called_once_with(threshold=0.8, model=mock.sentinel.model)
    faithfulness.assert_called_once_with(threshold=0.7, model=mock.sentinel.model)


def test_evaluate_contextual_rejects_unknown_metric():
    with pytest.raises(ValueError, match='Unknown contextual metric'):
        deepeval.evaluate_contextual_with_deepeval('question', 'answer', [], metrics='toxicity')


def test_assert_contextual_with_deepeval_reports_failed_metrics():
    result = {'results': {'faithfulness': {'score': 0.2, 'reason': 'Unsupported', 'passed': False}}, 'passed': False}
    with mock.patch.object(deepeval, 'evaluate_contextual_with_deepeval', return_value=result):
        with pytest.raises(AssertionError, match='Contextual DeepEval evaluation failed'):
            deepeval.assert_contextual_with_deepeval('question', 'answer', [], metrics='faithfulness')


def test_get_text_similarity_with_deepeval():
    metric = _metric(score=0.85)
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'SingleTurnParams', FakeParams),
        mock.patch.object(deepeval, 'GEval', return_value=metric) as metric_class,
    ):
        score = deepeval.get_text_similarity_with_deepeval('actual', 'expected', 'model', threshold=0.8)

    assert score == 0.85
    metric_class.assert_called_once_with(
        name='Text semantic similarity',
        criteria='The actual output conveys the same meaning as the expected output.',
        evaluation_steps=list(deepeval._SIMILARITY_STEPS),
        evaluation_params=[FakeParams.ACTUAL_OUTPUT, FakeParams.EXPECTED_OUTPUT],
        threshold=0.8,
        model=mock.ANY,
    )
    metric.measure.assert_called_once()
    test_case = metric.measure.call_args.args[0]
    assert test_case.actual_output == 'actual'
    assert test_case.expected_output == 'expected'


def test_get_summarization_with_deepeval():
    metric = _metric(score=0.9, reason='Complete and consistent summary')
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'SummarizationMetric', return_value=metric) as metric_class,
        mock.patch.object(deepeval, '_get_model', return_value=mock.sentinel.model),
    ):
        score, reason = deepeval.get_summarization_with_deepeval(
            source_text='The order is ready for pickup.',
            summary='The order is ready for pickup.',
            provider='azure',
            threshold=0.8,
        )

    assert (score, reason) == (0.9, 'Complete and consistent summary')
    metric_class.assert_called_once_with(threshold=0.8, model=mock.sentinel.model)
    test_case = metric.measure.call_args.args[0]
    assert test_case.input == 'The order is ready for pickup.'
    assert test_case.actual_output == 'The order is ready for pickup.'
    assert test_case.context is None


def test_get_pii_leakage_with_deepeval():
    metric = _metric(score=1.0, reason='No PII detected')
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'PIILeakageMetric', return_value=metric) as metric_class,
        mock.patch.object(deepeval, '_get_model', return_value=mock.sentinel.model),
    ):
        score, reason = deepeval.get_pii_leakage_with_deepeval(
            actual_output='Your order is ready for pickup.',
            input_text='Tell me the order status.',
            provider='azure',
            threshold=0.5,
        )

    assert (score, reason) == (1.0, 'No PII detected')
    metric_class.assert_called_once_with(threshold=0.5, model=mock.sentinel.model)
    test_case = metric.measure.call_args.args[0]
    assert test_case.input == 'Tell me the order status.'
    assert test_case.actual_output == 'Your order is ready for pickup.'


def test_get_toxicity_with_deepeval():
    metric = _metric(score=0.1, reason='Non-toxic')
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'ToxicityMetric', return_value=metric) as metric_class,
        mock.patch.object(deepeval, '_get_model', return_value=mock.sentinel.model),
    ):
        score, reason = deepeval.get_toxicity_with_deepeval(
            actual_output='The order is ready for pickup.',
            input_text='Tell me the order status.',
            provider='azure',
            threshold=0.5,
        )

    assert (score, reason) == (0.1, 'Non-toxic')
    metric_class.assert_called_once_with(threshold=0.5, model=mock.sentinel.model)
    test_case = metric.measure.call_args.args[0]
    assert test_case.input == 'Tell me the order status.'
    assert test_case.actual_output == 'The order is ready for pickup.'


def test_get_tool_correctness_with_deepeval():
    metric = _metric(score=0.9, reason='Correct tool usage')
    tools_called = [deepeval.ToolCall(name='lookup_order')]
    expected_tools = [deepeval.ToolCall(name='lookup_order')]
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'ToolCorrectnessMetric', return_value=metric) as metric_class,
        mock.patch.object(deepeval, '_get_model', return_value=mock.sentinel.model),
    ):
        score, reason = deepeval.get_tool_correctness_with_deepeval(
            input_text='Find the order status.',
            tools_called=tools_called,
            expected_tools=expected_tools,
            provider='azure',
            threshold=0.8,
        )

    assert (score, reason) == (0.9, 'Correct tool usage')
    metric_class.assert_called_once_with(threshold=0.8, model=mock.sentinel.model)
    test_case = metric.measure.call_args.args[0]
    assert test_case.input == 'Find the order status.'
    assert test_case.tools_called == tools_called
    assert test_case.expected_tools == expected_tools


def test_get_contextual_recall_with_deepeval():
    metric = _metric(score=0.9, reason='Context covers the answer')
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'ContextualRecallMetric', return_value=metric) as metric_class,
        mock.patch.object(deepeval, '_get_model', return_value=mock.sentinel.model),
    ):
        score, reason = deepeval.get_contextual_recall_with_deepeval(
            input_text='What is the order status?',
            actual_output='The order is preparing.',
            expected_output='The order status is preparing.',
            retrieved_context=[{'status': 'preparing'}],
            provider='azure',
            threshold=0.8,
        )

    assert (score, reason) == (0.9, 'Context covers the answer')
    metric_class.assert_called_once_with(threshold=0.8, model=mock.sentinel.model)
    test_case = metric.measure.call_args.args[0]
    assert test_case.input == 'What is the order status?'
    assert test_case.actual_output == 'The order is preparing.'
    assert test_case.expected_output == 'The order status is preparing.'
    assert test_case.retrieval_context == ['{\n  "status": "preparing"\n}']


def test_get_contextual_precision_with_deepeval():
    metric = _metric(score=0.9, reason='Precise context')
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'ContextualPrecisionMetric', return_value=metric) as metric_class,
        mock.patch.object(deepeval, '_get_model', return_value=mock.sentinel.model),
    ):
        score, reason = deepeval.get_contextual_precision_with_deepeval(
            input_text='What is the order status?',
            actual_output='The order is preparing.',
            expected_output='The order status is preparing.',
            retrieved_context=[{'status': 'preparing'}],
            provider='azure',
            threshold=0.8,
        )

    assert (score, reason) == (0.9, 'Precise context')
    metric_class.assert_called_once_with(threshold=0.8, model=mock.sentinel.model)
    test_case = metric.measure.call_args.args[0]
    assert test_case.input == 'What is the order status?'
    assert test_case.actual_output == 'The order is preparing.'
    assert test_case.expected_output == 'The order status is preparing.'
    assert test_case.retrieval_context == ['{\n  "status": "preparing"\n}']


def test_get_contextual_relevancy_with_deepeval():
    metric = _metric(score=0.9, reason='Relevant context')
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'ContextualRelevancyMetric', return_value=metric) as metric_class,
        mock.patch.object(deepeval, '_get_model', return_value=mock.sentinel.model),
    ):
        score, reason = deepeval.get_contextual_relevancy_with_deepeval(
            input_text='What is the order status?',
            actual_output='The order is preparing.',
            retrieved_context=[{'status': 'preparing'}],
            provider='azure',
            threshold=0.8,
        )

    assert (score, reason) == (0.9, 'Relevant context')
    metric_class.assert_called_once_with(threshold=0.8, model=mock.sentinel.model)
    test_case = metric.measure.call_args.args[0]
    assert test_case.input == 'What is the order status?'
    assert test_case.actual_output == 'The order is preparing.'
    assert test_case.retrieval_context == ['{\n  "status": "preparing"\n}']


def test_get_json_correctness_with_deepeval():
    metric = _metric(score=0.95, reason='Valid JSON')
    schema = mock.sentinel.schema
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'JsonCorrectnessMetric', return_value=metric) as metric_class,
        mock.patch.object(deepeval, '_get_model', return_value=mock.sentinel.model),
    ):
        score, reason = deepeval.get_json_correctness_with_deepeval(
            '{"status": "ok"}', schema, provider='azure', threshold=0.8
        )

    assert (score, reason) == (0.95, 'Valid JSON')
    metric_class.assert_called_once_with(expected_schema=schema, model=mock.sentinel.model, threshold=0.8)
    assert metric.measure.call_args.args[0].actual_output == '{"status": "ok"}'


def test_get_hallucination_evaluation_with_deepeval():
    metric = _metric(score=0.1, reason='Supported by context')
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'HallucinationMetric', return_value=metric) as metric_class,
        mock.patch.object(deepeval, '_get_model', return_value=mock.sentinel.model),
    ):
        score, reason = deepeval.get_hallucination_evaluation_with_deepeval(
            actual_output='Paris is the capital of France.',
            retrieved_context=[{'country': 'France', 'capital': 'Paris'}],
            input_text='What is the capital of France?',
            provider='azure',
            threshold=0.2,
        )

    assert (score, reason) == (0.1, 'Supported by context')
    metric_class.assert_called_once_with(threshold=0.2, model=mock.sentinel.model)
    test_case = metric.measure.call_args.args[0]
    assert test_case.input == 'What is the capital of France?'
    assert test_case.context == ['{\n  "country": "France",\n  "capital": "Paris"\n}']


def test_get_answer_relevancy_with_deepeval():
    metric = _metric(score=0.9, reason='Relevant')
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'AnswerRelevancyMetric', return_value=metric) as metric_class,
        mock.patch.object(deepeval, '_get_model', return_value=mock.sentinel.model),
    ):
        score, reason = deepeval.get_answer_relevancy_with_deepeval(
            actual_output='Paris is the capital of France.',
            input_text='What is the capital of France?',
            provider='azure',
            threshold=0.8,
        )

    assert (score, reason) == (0.9, 'Relevant')
    metric_class.assert_called_once_with(threshold=0.8, model=mock.sentinel.model)
    test_case = metric.measure.call_args.args[0]
    assert test_case.input == 'What is the capital of France?'
    assert test_case.actual_output == 'Paris is the capital of France.'


def test_get_faithfulness_evaluation_with_json_api_context():
    metric = _metric(score=0.9, reason='Supported by context')
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'FaithfulnessMetric', return_value=metric),
        mock.patch.object(deepeval, '_get_model', return_value=mock.sentinel.model),
    ):
        score, _ = deepeval.get_faithfulness_evaluation_with_deepeval(
            actual_output='The order is being prepared.',
            retrieved_context=[{'order_id': '12345', 'status': 'preparing'}],
            threshold=0.7,
        )

    assert score == 0.9
    test_case = metric.measure.call_args.args[0]
    assert test_case.retrieval_context == ['{\n  "order_id": "12345",\n  "status": "preparing"\n}']


def test_get_faithfulness_evaluation_with_deepeval():
    metric = _metric(score=0.9, reason='Supported by context')
    configured_model = mock.sentinel.configured_model
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'FaithfulnessMetric', return_value=metric) as metric_class,
        mock.patch.object(deepeval, '_get_model', return_value=configured_model) as get_model,
    ):
        score, reason = deepeval.get_faithfulness_evaluation_with_deepeval(
            actual_output='Paris is the capital of France.',
            retrieved_context=['France has Paris as its capital.'],
            input_text='What is the capital of France?',
            model_name='model',
            provider='azure',
            threshold=0.8,
        )

    assert (score, reason) == (0.9, 'Supported by context')
    get_model.assert_called_once_with('azure', 'model', {})
    metric_class.assert_called_once_with(threshold=0.8, model=configured_model)
    test_case = metric.measure.call_args.args[0]
    assert test_case.input == 'What is the capital of France?'
    assert test_case.actual_output == 'Paris is the capital of France.'
    assert test_case.retrieval_context == ['France has Paris as its capital.']


def test_get_answer_evaluation_with_deepeval():
    metric = _metric(score=0.9, reason='Correct answer')
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'SingleTurnParams', FakeParams),
        mock.patch.object(deepeval, 'GEval', return_value=metric) as metric_class,
    ):
        score, reason = deepeval.get_answer_evaluation_with_deepeval(
            'actual', 'expected', 'model', question='question', threshold=0.8
        )

    assert (score, reason) == (0.9, 'Correct answer')
    metric_class.assert_called_once()
    metric_kwargs = metric_class.call_args.kwargs
    assert metric_kwargs['model'] is not None
    assert metric_kwargs['threshold'] == 0.8
    metric.measure.assert_called_once()
    test_case = metric.measure.call_args.args[0]
    assert test_case.input == 'question'
    assert test_case.actual_output == 'actual'
    assert test_case.expected_output == 'expected'


def test_get_text_criteria_analysis_with_deepeval_returns_failed_features():
    metrics = [_metric(score=0.9, reason='Good'), _metric(score=0.2, reason='Missing')]
    configured_model = mock.sentinel.configured_model
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'SingleTurnParams', FakeParams),
        mock.patch.object(deepeval, 'GEval', side_effect=metrics) as metric_class,
        mock.patch.object(deepeval, '_get_model', return_value=configured_model) as get_model,
    ):
        result = deepeval.get_text_criteria_analysis_with_deepeval(
            'text', ['criterion one', 'criterion two'], model_name='model', provider='azure', threshold=0.7
        )

    get_model.assert_called_once_with('azure', 'model', {})
    assert all(call.kwargs['model'] is configured_model for call in metric_class.call_args_list)
    assert result == {
        'overall_match': 0.55,
        'passed': False,
        'features': [{'name': 'criterion two', 'score': 0.2, 'explanation': 'Missing'}],
    }
    assert all(metric.measure.call_count == 1 for metric in metrics)


def test_deepeval_functions_fail_with_clear_error_when_dependency_is_missing():
    error = ModuleNotFoundError("No module named 'deepeval'", name='deepeval')
    with mock.patch.object(deepeval, '_DEEPEVAL_IMPORT_ERROR', error):
        with pytest.raises(ImportError, match='DeepEval is not installed') as caught:
            deepeval.get_text_similarity_with_deepeval('actual', 'expected')
    assert caught.value.__cause__ is error


@pytest.mark.parametrize(
    'error',
    [
        ImportError("cannot import name 'SingleTurnParams' from 'deepeval.test_case'"),
        ModuleNotFoundError("No module named 'dependency'", name='dependency'),
        ImportError("cannot import name 'GPTModel' from 'deepeval.models'"),
    ],
)
def test_deepeval_import_failure_reports_version_and_original_cause(error):
    with (
        mock.patch.object(deepeval, '_DEEPEVAL_IMPORT_ERROR', error),
        mock.patch.object(deepeval, 'version', return_value='3.0.0'),
    ):
        with pytest.raises(ImportError, match=r'installed version: 3.0.0; required: deepeval~=3.9.9') as caught:
            deepeval.get_text_similarity_with_deepeval('actual', 'expected')
    assert caught.value.__cause__ is error
    assert str(error) in str(caught.value)


def test_deepeval_import_failure_without_package_metadata():
    error = ImportError('Broken dependency')
    with (
        mock.patch.object(deepeval, '_DEEPEVAL_IMPORT_ERROR', error),
        mock.patch.object(deepeval, 'version', side_effect=deepeval.PackageNotFoundError('deepeval')),
    ):
        with pytest.raises(ImportError, match='package metadata unavailable') as caught:
            deepeval._require_deepeval()
    assert caught.value.__cause__ is error


class OfflineJudge(DeepEvalBaseLLM):
    """Deterministic local judge: real DeepEval execution without provider calls."""

    def load_model(self):
        return self

    def get_model_name(self):
        return 'offline-judge'

    def generate(self, _prompt, schema=None):
        if schema.__name__ == 'Steps':
            return schema(steps=['Check the requested custom criterion.'])
        return schema(score=8, reason='Offline verdict')

    async def a_generate(self, prompt, schema=None):
        return self.generate(prompt, schema=schema)


_ASSERT_CASES = [
    ('assert_summarization_with_deepeval', 'SummarizationMetric', ('source', 'summary')),
    ('assert_pii_leakage_with_deepeval', 'PIILeakageMetric', ('answer',)),
    ('assert_toxicity_with_deepeval', 'ToxicityMetric', ('answer',)),
    ('assert_tool_correctness_with_deepeval', 'ToolCorrectnessMetric', ('question', [], [])),
    (
        'assert_contextual_recall_with_deepeval',
        'ContextualRecallMetric',
        ('question', 'answer', 'expected', ['source']),
    ),
    (
        'assert_contextual_precision_with_deepeval',
        'ContextualPrecisionMetric',
        ('question', 'answer', 'expected', ['source']),
    ),
    ('assert_contextual_relevancy_with_deepeval', 'ContextualRelevancyMetric', ('question', 'answer', ['source'])),
    ('assert_json_correctness_with_deepeval', 'JsonCorrectnessMetric', ('{}', mock.sentinel.schema)),
    ('assert_hallucination_evaluation_with_deepeval', 'HallucinationMetric', ('answer', ['source'])),
    ('assert_answer_relevancy_with_deepeval', 'AnswerRelevancyMetric', ('answer', 'question')),
    ('assert_faithfulness_with_deepeval', 'FaithfulnessMetric', ('answer', ['source'])),
    ('assert_text_similarity_with_deepeval', 'GEval', ('answer', 'expected')),
    ('assert_answer_evaluation_with_deepeval', 'GEval', ('answer', 'expected')),
]


@pytest.mark.parametrize(('function_name', 'metric_class', 'args'), _ASSERT_CASES)
@pytest.mark.parametrize('passed', [False, True])
def test_all_asserts_use_native_decision_and_measure_once(function_name, metric_class, args, passed):
    # Deliberately disagree with a manual >= comparison, including zero thresholds.
    metric = _metric(score=0.9 if not passed else 0.0, reason='Native decision', passed=passed)
    with mock.patch.object(deepeval, metric_class, return_value=metric):
        function = getattr(deepeval, function_name)
        if passed:
            function(*args, threshold=0.7, model=mock.sentinel.judge)
        else:
            with pytest.raises(AssertionError, match='evaluation failed'):
                function(*args, threshold=0.0, model=mock.sentinel.judge)
    metric.measure.assert_called_once()
    metric.is_successful.assert_called_once()


@pytest.mark.parametrize(
    'function_name', ['assert_text_similarity_with_deepeval', 'assert_answer_evaluation_with_deepeval']
)
def test_reference_asserts_accept_any_successful_reference(function_name):
    metrics = [_metric(0.9, passed=False), _metric(0.0, passed=True)]
    with mock.patch.object(deepeval, 'GEval', side_effect=metrics):
        getattr(deepeval, function_name)('answer', ['wrong', 'right'], threshold=0.7, model=mock.sentinel.judge)
    assert all(metric.measure.call_count == 1 for metric in metrics)


@pytest.mark.parametrize(
    'function_name', ['assert_text_similarity_with_deepeval', 'assert_answer_evaluation_with_deepeval']
)
def test_reference_asserts_fail_without_references(function_name):
    with pytest.raises(AssertionError):
        getattr(deepeval, function_name)('answer', [], threshold=0.7, model=mock.sentinel.judge)


def test_criteria_assert_fails_when_average_passes_but_one_characteristic_fails():
    metrics = [_metric(1.0, passed=True), _metric(0.6, reason='Not brief', passed=False)]
    with mock.patch.object(deepeval, 'GEval', side_effect=metrics):
        with pytest.raises(AssertionError, match='Not brief') as caught:
            deepeval.assert_text_criteria_with_deepeval(
                'text',
                ['formal', 'brief'],
                threshold=0.7,
                model=mock.sentinel.judge,
            )
    message = str(caught.value)
    assert 'one or more characteristics did not pass' in message
    assert 'Overall match (informational mean): 0.8; requested threshold: 0.7' in message
    assert "Failed features: [{'name': 'brief', 'score': 0.6, 'explanation': 'Not brief'}]" in message
    assert '<' not in message
    assert all(metric.measure.call_count == 1 for metric in metrics)
    assert all(metric.measure.call_args.args[0].input == '' for metric in metrics)


def test_criteria_assert_passes_when_all_selected_characteristics_pass():
    with mock.patch.object(deepeval, 'GEval', return_value=_metric(1.0, passed=True)) as constructor:
        deepeval.assert_text_criteria_with_deepeval('text', ['formal'], threshold=0.7, model=mock.sentinel.judge)
    assert constructor.call_count == 1
    assert 'formal' in constructor.call_args.kwargs['evaluation_steps'][0]


def test_criteria_rejects_empty_selection():
    with pytest.raises(ValueError, match='at least one'):
        deepeval.get_text_criteria_analysis_with_deepeval('text', [], model=mock.sentinel.judge)


@pytest.mark.parametrize(
    'options',
    [
        {'provider': 'openai'},
        {'model_name': 'another'},
        {'model_kwargs': {'temperature': 0.1}},
    ],
)
def test_supplied_model_rejects_conflicting_construction_options(options):
    with pytest.raises(ValueError, match='cannot be combined'):
        deepeval.get_answer_relevancy_with_deepeval('answer', 'question', model=mock.sentinel.judge, **options)


def test_supplied_model_bypasses_default_wrapper_and_model_creation():
    with mock.patch.object(deepeval, '_get_model', side_effect=AssertionError('must not create a model')):
        with mock.patch.object(deepeval, 'AnswerRelevancyMetric', return_value=_metric(0.8)) as constructor:
            deepeval.get_answer_relevancy_with_deepeval('answer', 'question', model=mock.sentinel.judge)
    assert constructor.call_args.kwargs['model'] is mock.sentinel.judge


def test_public_model_factory_accepts_explicit_configuration():
    from toolium.config_parser import ExtendedConfigParser

    config = ExtendedConfigParser()
    config.read_dict({'DeepEval': {'openai_model': 'judge', 'openai_api_key': 'key'}})
    with (
        mock.patch.object(
            deepeval.DriverWrappersPool, 'get_default_wrapper', side_effect=AssertionError('global config')
        ),
        mock.patch.object(deepeval, 'GPTModel') as constructor,
    ):
        judge = deepeval.create_deepeval_model(config=config, temperature=0.2)
    assert judge is constructor.return_value
    constructor.assert_called_once_with(model='judge', api_key='key', temperature=0.2)


@pytest.mark.parametrize('async_mode', [False, True])
def test_default_geval_steps_skip_generation_with_real_metric(async_mode):
    judge = OfflineJudge()
    with mock.patch.object(judge, 'generate', wraps=judge.generate) as generate:
        score, reason = deepeval.get_answer_evaluation_with_deepeval(
            'answer',
            'expected',
            question='question',
            model=judge,
            async_mode=async_mode,
        )
    assert score == 0.8
    assert reason == 'Offline verdict'
    assert generate.call_count == 1
    assert generate.call_args.kwargs['schema'].__name__ != 'Steps'


def test_custom_criteria_without_steps_allows_native_step_generation():
    judge = OfflineJudge()
    with mock.patch.object(judge, 'generate', wraps=judge.generate) as generate:
        deepeval.get_answer_evaluation_with_deepeval(
            'answer',
            'expected',
            criteria='Custom grading',
            model=judge,
            async_mode=False,
        )
    assert [call.kwargs['schema'].__name__ for call in generate.call_args_list] == ['Steps', 'ReasonScore']


def test_user_steps_override_defaults_without_mutating_input():
    steps = ['Custom step']
    with mock.patch.object(deepeval, 'GEval', return_value=_metric(0.8)) as constructor:
        deepeval.get_text_similarity_with_deepeval(
            'answer', 'expected', model=mock.sentinel.judge, evaluation_steps=steps
        )
    assert constructor.call_args.kwargs['evaluation_steps'] == steps
    assert steps == ['Custom step']


@pytest.mark.parametrize('metric_name', ['toxicity', 'hallucination', 'pii_leakage', 'faithfulness'])
def test_batch_results_use_native_success(metric_name):
    class_name = deepeval._RESPONSE_METRICS[metric_name]
    metric = _metric(0.9, reason='Rejected', passed=False)
    with mock.patch.object(deepeval, class_name, return_value=metric):
        result = deepeval.evaluate_response_with_deepeval(
            'question',
            'answer',
            metric_config={metric_name: {'threshold': 0.0}},
            retrieved_context=['source'],
            model=mock.sentinel.judge,
        )
    assert result == {'results': {metric_name: {'score': 0.9, 'reason': 'Rejected', 'passed': False}}, 'passed': False}


@pytest.mark.parametrize(
    'entry',
    [
        {},
        {'faithfulness': {}},
        {'faithfulness': {'threshold': 2}},
        {'summarization': {'threshold': 0.7}},
        {'turn_relevancy': {'threshold': 0.7}},
    ],
)
def test_response_rejects_invalid_metric_selection_before_creating_judge(entry):
    with mock.patch.object(deepeval, '_get_model', side_effect=AssertionError('must validate first')):
        with pytest.raises(ValueError, match=r'metric|threshold'):
            deepeval.evaluate_response_with_deepeval('question', 'answer', metric_config=entry)


@pytest.mark.parametrize('reference_facts', [None, [], ['Independent reference'], [{'status': 'ready'}]])
def test_response_maps_reference_facts_independently_from_retrieved_evidence(reference_facts):
    evaluator = deepeval.DeepEvalEvaluator(model=mock.sentinel.judge)
    evidence = ['Retrieved evidence']
    with mock.patch.object(deepeval, '_evaluate_metrics', return_value={'passed': True}) as evaluate:
        evaluator.assert_response('question', 'answer', retrieved_context=evidence, reference_context=reference_facts)

    test_case = evaluate.call_args.args[0]
    assert test_case.retrieval_context == evidence
    expected = evidence if reference_facts is None else deepeval._serialize_context(reference_facts)
    assert test_case.context == expected


def test_response_accepts_reference_facts_without_retrieved_evidence():
    with mock.patch.object(deepeval, '_evaluate_metrics') as evaluate:
        deepeval.evaluate_response_with_deepeval(
            'question', 'answer', reference_context=['Reference'], model=mock.sentinel.judge
        )
    test_case = evaluate.call_args.args[0]
    assert test_case.context == ['Reference']
    assert test_case.retrieval_context is None


def test_response_rejects_reserved_behave_context_before_creating_judge():
    with mock.patch.object(deepeval, '_get_model', side_effect=AssertionError('must validate first')):
        with pytest.raises(TypeError, match=r'context is reserved for Behave context.*reference_context'):
            deepeval.evaluate_response_with_deepeval('question', 'answer', context=mock.sentinel.behave_context)


def test_empty_contextual_selection_does_not_vacuously_pass():
    with pytest.raises(ValueError, match='at least one'):
        deepeval.evaluate_contextual_with_deepeval('question', 'answer', [], metrics=[])


@pytest.mark.parametrize(
    'metrics_options',
    [
        {'metrics': 'contextual_recall'},
        {'metric_config': {'contextual_precision': {'threshold': 0.7}}},
    ],
)
def test_expected_output_required_in_both_contextual_configuration_modes(metrics_options):
    with pytest.raises(ValueError, match='expected_output is required'):
        deepeval.evaluate_contextual_with_deepeval('question', 'answer', ['source'], **metrics_options)


def test_real_conversational_geval_runs_with_fixed_steps_and_explicit_turns():
    messages = [{'role': 'user', 'content': 'Hello'}, {'role': 'assistant', 'content': 'Hello!'}]
    judge = OfflineJudge()
    with mock.patch.object(judge, 'generate', wraps=judge.generate) as generate:
        result = deepeval.evaluate_conversation_with_deepeval(
            messages,
            metric_config={'conversational_geval': {'threshold': 0.7, 'async_mode': False}},
            model=judge,
        )
    assert result['passed'] is True
    assert result['results']['conversational_geval']['score'] == 0.8
    assert generate.call_count == 1
    assert messages == [{'role': 'user', 'content': 'Hello'}, {'role': 'assistant', 'content': 'Hello!'}]


@pytest.mark.parametrize('messages', [[], [{'role': 'system', 'content': 'Instruction'}], ['not a turn']])
def test_conversation_rejects_invalid_messages(messages):
    with pytest.raises((ValueError, TypeError)):
        deepeval.evaluate_conversation_with_deepeval(messages, model=mock.sentinel.judge)


def test_conversation_rejects_single_turn_metrics():
    with pytest.raises(ValueError, match='Unknown conversation metric'):
        deepeval.evaluate_conversation_with_deepeval(
            [{'role': 'user', 'content': 'Hello'}],
            metric_config={'faithfulness': {'threshold': 0.7}},
            model=mock.sentinel.judge,
        )


def test_conversation_and_response_asserts_report_failed_metrics():
    for function, metric_class, args in [
        (deepeval.assert_response_with_deepeval, 'AnswerRelevancyMetric', ('question', 'answer')),
        (deepeval.assert_conversation_with_deepeval, 'TurnRelevancyMetric', ([{'role': 'user', 'content': 'Hello'}],)),
    ]:
        with mock.patch.object(
            deepeval, metric_class, return_value=_metric(1.0, reason='Native failure', passed=False)
        ):
            with pytest.raises(AssertionError, match='Native failure'):
                function(*args, model=mock.sentinel.judge)


def test_evaluator_reuses_judge_but_copies_definitions_and_creates_new_metrics_and_cases():
    config = {'answer_relevancy': {'threshold': 0.7}}
    metrics = [_metric(0.8), _metric(0.9)]
    evaluator = deepeval.DeepEvalEvaluator(model=mock.sentinel.judge, metric_config=config)
    config['answer_relevancy']['threshold'] = 0.99
    with mock.patch.object(deepeval, 'AnswerRelevancyMetric', side_effect=metrics) as constructor:
        first = evaluator.evaluate_response('question A', 'answer A')
        second = evaluator.evaluate_response('question B', 'answer B')
    assert all(call.kwargs['threshold'] == 0.7 for call in constructor.call_args_list)
    assert all(call.kwargs['model'] is mock.sentinel.judge for call in constructor.call_args_list)
    assert metrics[0].measure.call_args.args[0] is not metrics[1].measure.call_args.args[0]
    first['results']['answer_relevancy']['score'] = 0
    assert second['results']['answer_relevancy']['score'] == 0.9


def test_evaluator_call_selection_replaces_defaults_only_for_that_call():
    evaluator = deepeval.DeepEvalEvaluator(model=mock.sentinel.judge)
    with (
        mock.patch.object(deepeval, 'ToxicityMetric', return_value=_metric(0.0, passed=True)) as toxicity,
        mock.patch.object(deepeval, 'AnswerRelevancyMetric', return_value=_metric(0.8)) as relevancy,
    ):
        result = evaluator.evaluate_response('question', 'answer', metric_config={'toxicity': {'threshold': 0.2}})
        default_result = evaluator.evaluate_response('question', 'answer')
    assert list(result['results']) == ['toxicity']
    assert list(default_result['results']) == ['answer_relevancy']
    toxicity.assert_called_once()
    relevancy.assert_called_once()


def test_evaluator_constructs_model_once_and_supports_summary_and_conversation_asserts():
    with mock.patch.object(deepeval, 'create_deepeval_model', return_value=mock.sentinel.judge) as factory:
        evaluator = deepeval.DeepEvalEvaluator()
        with (
            mock.patch.object(deepeval, 'SummarizationMetric', return_value=_metric(0.8)) as summary,
            mock.patch.object(deepeval, 'TurnRelevancyMetric', return_value=_metric(0.8)),
            mock.patch.object(deepeval, 'AnswerRelevancyMetric', return_value=_metric(0.8)),
        ):
            evaluator.assert_summary('original source', 'summary')
            evaluator.assert_conversation([{'role': 'user', 'content': 'Hello'}])
            evaluator.assert_response('question', 'answer')
    factory.assert_called_once()
    assert summary.return_value.measure.call_args.args[0].input == 'original source'


@pytest.mark.parametrize('async_mode', [False, True])
def test_real_metrics_support_parallel_calls_with_a_stateless_judge(async_mode):
    evaluator = deepeval.DeepEvalEvaluator(
        model=OfflineJudge(),
        metric_config={'text_similarity': {'threshold': 0.7, 'async_mode': async_mode}},
        conversation_metric_config={'conversational_geval': {'threshold': 0.7, 'async_mode': async_mode}},
    )
    barrier = Barrier(2)

    def evaluate(index):
        barrier.wait(timeout=10)
        if index == 0:
            return evaluator.evaluate_response('question', 'answer', expected_output='expected')
        return evaluator.evaluate_conversation(
            [{'role': 'user', 'content': 'Hello'}, {'role': 'assistant', 'content': 'Hello!'}]
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(evaluate, range(2)))
    assert all(result['passed'] for result in results)
    assert list(results[0]['results']) == ['text_similarity']
    assert list(results[1]['results']) == ['conversational_geval']


@pytest.mark.parametrize('metric_name', list(deepeval._RESPONSE_METRICS))
def test_registered_response_metrics_accept_real_constructors_and_native_success(metric_name):
    from pydantic import BaseModel

    class ExpectedSchema(BaseModel):
        answer: str

    options = {'threshold': 0.7, 'strict_mode': True}
    if metric_name == 'json_correctness':
        options['expected_schema'] = ExpectedSchema
    if metric_name == 'geval':
        options['evaluation_steps'] = ['Check correctness.']
    metric_class = getattr(deepeval, deepeval._RESPONSE_METRICS[metric_name])

    def measured(metric, _test_case):
        metric.score = 0.8
        metric.reason = 'Native strict-mode decision'

    with mock.patch.object(metric_class, 'measure', measured):
        result = deepeval.evaluate_response_with_deepeval(
            'question',
            '{"answer": "yes"}',
            expected_output='yes',
            retrieved_context=['source'],
            tools_called=[],
            expected_tools=[],
            metric_config={metric_name: options},
            model=OfflineJudge(),
        )
    # Native strict thresholds are 1 for positive metrics and 0 for risk metrics.
    assert result['passed'] is False


@pytest.mark.parametrize('metric_name', list(deepeval._CONVERSATION_METRICS))
def test_registered_conversation_metrics_accept_real_constructors(metric_name):
    metric_class = getattr(deepeval, deepeval._CONVERSATION_METRICS[metric_name])

    def measured(metric, _test_case):
        metric.score = 0.8
        metric.reason = 'Native decision'
        metric.success = metric.score >= metric.threshold

    with mock.patch.object(metric_class, 'measure', measured):
        result = deepeval.evaluate_conversation_with_deepeval(
            [deepeval.Turn(role='user', content='Hello'), deepeval.Turn(role='assistant', content='Hello!')],
            metric_config={metric_name: {'threshold': 0.7}},
            model=OfflineJudge(),
        )
    assert result['passed'] is True


def test_real_metric_error_prevents_success_even_with_high_score():
    def measured(metric, _test_case):
        metric.score = 1.0
        metric.reason = 'Incomplete evaluation'
        metric.error = 'Judge failed'

    with mock.patch.object(deepeval.AnswerRelevancyMetric, 'measure', measured):
        with pytest.raises(AssertionError, match='Incomplete evaluation'):
            deepeval.assert_answer_relevancy_with_deepeval('answer', 'question', threshold=0.7, model=OfflineJudge())


@pytest.mark.parametrize('matches', [True, False])
def test_tool_correctness_runs_real_measurement_without_an_llm_call(matches):
    expected = deepeval.ToolCall(name='lookup_order')
    called = expected if matches else deepeval.ToolCall(name='cancel_order')
    judge = OfflineJudge()
    with mock.patch.object(judge, 'generate', side_effect=AssertionError('No LLM call expected')):
        result = deepeval.evaluate_response_with_deepeval(
            'Find the order',
            '',
            tools_called=[called],
            expected_tools=[expected],
            metric_config={'tool_correctness': {'threshold': 0.7, 'async_mode': False}},
            model=judge,
        )
    assert result['passed'] is matches


def test_evaluator_rejects_model_with_construction_options():
    with pytest.raises(ValueError, match='cannot be combined'):
        deepeval.DeepEvalEvaluator(model=mock.sentinel.judge, provider='azure')


def test_response_custom_geval_requires_an_explicit_rubric():
    with pytest.raises(ValueError, match='requires criteria or evaluation_steps'):
        deepeval.evaluate_response_with_deepeval(
            'question',
            'answer',
            metric_config={'geval': {'threshold': 0.7}},
            model=OfflineJudge(),
        )


def test_criteria_options_do_not_allow_overriding_selected_characteristics():
    with pytest.raises(ValueError, match='Use text_criteria'):
        deepeval.get_text_criteria_analysis_with_deepeval('text', ['formal'], criteria='another', model=OfflineJudge())
