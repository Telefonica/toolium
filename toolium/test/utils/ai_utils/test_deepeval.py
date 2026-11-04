"""Tests for the optional DeepEval integration."""

from unittest import mock

import pytest

from toolium.utils.ai_utils import deepeval


class FakeTestCase:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


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


def test_evaluate_contextual_with_metric_config():
    metric = mock.Mock(score=0.9, reason='Supported')
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
        ('summarization', 'SummarizationMetric'),
    ],
)
def test_metric_config_passes_common_options(metric_name, metric_attribute):
    metric = mock.Mock(score=0.9, reason='Good')
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
    metric = mock.Mock(score=0.9, reason='Good')
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


def test_summarization_metric_config_passes_specific_options():
    metric = mock.Mock(score=0.9, reason='Good')
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'SummarizationMetric', return_value=metric) as metric_class,
        mock.patch.object(deepeval, '_get_model', return_value=mock.sentinel.model),
    ):
        deepeval.evaluate_contextual_with_deepeval(
            'question',
            'summary',
            ['context'],
            metric_config={
                'summarization': {
                    'threshold': 0.8,
                    'n': 3,
                    'assessment_questions': ['Does it include the status?'],
                    'truths_extraction_limit': 10,
                }
            },
        )

    metric_class.assert_called_once_with(
        threshold=0.8,
        model=mock.sentinel.model,
        n=3,
        assessment_questions=['Does it include the status?'],
        truths_extraction_limit=10,
    )


def test_metric_config_supports_metric_options():
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(
            deepeval, 'SummarizationMetric', return_value=mock.Mock(score=0.9, reason='Good')
        ) as metric_class,
        mock.patch.object(deepeval, '_get_model', return_value=mock.sentinel.model),
    ):
        deepeval.evaluate_contextual_with_deepeval(
            'question',
            'summary',
            ['context'],
            metric_config={'summarization': {'threshold': 0.8, 'n': 3}},
        )

    metric_class.assert_called_once_with(threshold=0.8, model=mock.sentinel.model, n=3)


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
    metric = mock.Mock(score=0.9, reason='Supported')
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
    metrics = [mock.Mock(score=0.9, reason='Relevant'), mock.Mock(score=0.6, reason='Incomplete')]
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
    metric = mock.Mock(score=0.85)
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
        evaluation_params=[FakeParams.ACTUAL_OUTPUT, FakeParams.EXPECTED_OUTPUT],
        threshold=0.8,
        model=mock.ANY,
    )
    metric.measure.assert_called_once()
    test_case = metric.measure.call_args.args[0]
    assert test_case.actual_output == 'actual'
    assert test_case.expected_output == 'expected'


def test_get_summarization_with_deepeval():
    metric = mock.Mock(score=0.9, reason='Complete and consistent summary')
    with (
        mock.patch.object(deepeval, 'LLMTestCase', FakeTestCase),
        mock.patch.object(deepeval, 'SummarizationMetric', return_value=metric) as metric_class,
        mock.patch.object(deepeval, '_get_model', return_value=mock.sentinel.model),
    ):
        score, reason = deepeval.get_summarization_with_deepeval(
            input_text='Summarize the order update.',
            actual_output='The order is ready for pickup.',
            source_context=[{'status': 'ready', 'delivery': 'pickup'}],
            provider='azure',
            threshold=0.8,
        )

    assert (score, reason) == (0.9, 'Complete and consistent summary')
    metric_class.assert_called_once_with(threshold=0.8, model=mock.sentinel.model)
    test_case = metric.measure.call_args.args[0]
    assert test_case.input == 'Summarize the order update.'
    assert test_case.actual_output == 'The order is ready for pickup.'
    assert test_case.context == ['{\n  "status": "ready",\n  "delivery": "pickup"\n}']


def test_assert_summarization_with_deepeval_fails_below_threshold():
    with mock.patch.object(deepeval, 'get_summarization_with_deepeval', return_value=(0.4, 'Incomplete')):
        with pytest.raises(AssertionError, match='DeepEval summarization is below threshold'):
            deepeval.assert_summarization_with_deepeval('summarize', 'summary', ['context'], threshold=0.7)


def test_get_pii_leakage_with_deepeval():
    metric = mock.Mock(score=0.1, reason='No PII detected')
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

    assert (score, reason) == (0.1, 'No PII detected')
    metric_class.assert_called_once_with(threshold=0.5, model=mock.sentinel.model)
    test_case = metric.measure.call_args.args[0]
    assert test_case.input == 'Tell me the order status.'
    assert test_case.actual_output == 'Your order is ready for pickup.'


def test_assert_pii_leakage_with_deepeval_fails_above_threshold():
    with mock.patch.object(deepeval, 'get_pii_leakage_with_deepeval', return_value=(0.8, 'PII detected')):
        with pytest.raises(AssertionError, match='DeepEval PII leakage is above threshold'):
            deepeval.assert_pii_leakage_with_deepeval('Email: user@example.com', threshold=0.5)


def test_get_toxicity_with_deepeval():
    metric = mock.Mock(score=0.1, reason='Non-toxic')
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


def test_assert_toxicity_with_deepeval_fails_above_threshold():
    with mock.patch.object(deepeval, 'get_toxicity_with_deepeval', return_value=(0.8, 'Toxic')):
        with pytest.raises(AssertionError, match='DeepEval toxicity is above threshold'):
            deepeval.assert_toxicity_with_deepeval('offensive output', threshold=0.5)


def test_get_tool_correctness_with_deepeval():
    metric = mock.Mock(score=0.9, reason='Correct tool usage')
    tools_called = [mock.sentinel.called_tool]
    expected_tools = [mock.sentinel.expected_tool]
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


def test_assert_tool_correctness_with_deepeval_fails_below_threshold():
    with mock.patch.object(deepeval, 'get_tool_correctness_with_deepeval', return_value=(0.4, 'Wrong tool')):
        with pytest.raises(AssertionError, match='DeepEval tool correctness is below threshold'):
            deepeval.assert_tool_correctness_with_deepeval('question', ['called'], ['expected'], threshold=0.7)


def test_get_contextual_recall_with_deepeval():
    metric = mock.Mock(score=0.9, reason='Context covers the answer')
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


def test_assert_contextual_recall_with_deepeval_fails_below_threshold():
    with mock.patch.object(deepeval, 'get_contextual_recall_with_deepeval', return_value=(0.4, 'Missing context')):
        with pytest.raises(AssertionError, match='DeepEval contextual recall is below threshold'):
            deepeval.assert_contextual_recall_with_deepeval(
                'question', 'answer', 'expected', ['context'], threshold=0.7
            )


def test_get_contextual_precision_with_deepeval():
    metric = mock.Mock(score=0.9, reason='Precise context')
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


def test_assert_contextual_precision_with_deepeval_fails_below_threshold():
    with mock.patch.object(deepeval, 'get_contextual_precision_with_deepeval', return_value=(0.4, 'Imprecise')):
        with pytest.raises(AssertionError, match='DeepEval contextual precision is below threshold'):
            deepeval.assert_contextual_precision_with_deepeval(
                'question', 'answer', 'expected', ['context'], threshold=0.7
            )


def test_get_contextual_relevancy_with_deepeval():
    metric = mock.Mock(score=0.9, reason='Relevant context')
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


def test_assert_contextual_relevancy_with_deepeval_fails_below_threshold():
    with mock.patch.object(deepeval, 'get_contextual_relevancy_with_deepeval', return_value=(0.4, 'Irrelevant')):
        with pytest.raises(AssertionError, match='DeepEval contextual relevancy is below threshold'):
            deepeval.assert_contextual_relevancy_with_deepeval('question', 'answer', ['context'], threshold=0.7)


def test_get_json_correctness_with_deepeval():
    metric = mock.Mock(score=0.95, reason='Valid JSON')
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


def test_assert_json_correctness_with_deepeval_fails_below_threshold():
    with mock.patch.object(deepeval, 'get_json_correctness_with_deepeval', return_value=(0.4, 'Invalid')):
        with pytest.raises(AssertionError, match='DeepEval JSON correctness is below threshold'):
            deepeval.assert_json_correctness_with_deepeval('{}', mock.sentinel.schema, threshold=0.7)


def test_get_hallucination_evaluation_with_deepeval():
    metric = mock.Mock(score=0.1, reason='Supported by context')
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


def test_assert_hallucination_evaluation_with_deepeval_fails_above_threshold():
    with mock.patch.object(
        deepeval, 'get_hallucination_evaluation_with_deepeval', return_value=(0.8, 'Unsupported claim')
    ):
        with pytest.raises(AssertionError, match='DeepEval hallucination is above threshold'):
            deepeval.assert_hallucination_evaluation_with_deepeval('answer', ['context'], threshold=0.5)


def test_get_answer_relevancy_with_deepeval():
    metric = mock.Mock(score=0.9, reason='Relevant')
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


def test_assert_answer_relevancy_with_deepeval_fails_below_threshold():
    with mock.patch.object(deepeval, 'get_answer_relevancy_with_deepeval', return_value=(0.4, 'Irrelevant')):
        with pytest.raises(AssertionError, match='DeepEval answer relevancy is below threshold'):
            deepeval.assert_answer_relevancy_with_deepeval('answer', 'question', threshold=0.7)


def test_get_faithfulness_evaluation_with_json_api_context():
    metric = mock.Mock(score=0.9, reason='Supported by context')
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
    metric = mock.Mock(score=0.9, reason='Supported by context')
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


def test_assert_faithfulness_with_deepeval_fails_below_threshold():
    with mock.patch.object(
        deepeval, 'get_faithfulness_evaluation_with_deepeval', return_value=(0.4, 'Unsupported claim')
    ):
        with pytest.raises(AssertionError, match='DeepEval faithfulness is below threshold'):
            deepeval.assert_faithfulness_with_deepeval('answer', ['context'], threshold=0.7)


def test_get_answer_evaluation_with_deepeval():
    metric = mock.Mock(score=0.9, reason='Correct answer')
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
    metrics = [mock.Mock(score=0.9, reason='Good'), mock.Mock(score=0.2, reason='Missing')]
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
        'features': [{'name': 'criterion two', 'score': 0.2, 'explanation': 'Missing'}],
    }
    assert all(metric.measure.call_count == 1 for metric in metrics)


def test_assert_text_similarity_with_deepeval_passes_when_any_expected_text_matches():
    with mock.patch.object(deepeval, 'get_text_similarity_with_deepeval', side_effect=[0.2, 0.8]) as similarity:
        deepeval.assert_text_similarity_with_deepeval('actual', ['wrong', 'right'], threshold=0.7)

    assert similarity.call_count == 2


def test_assert_text_similarity_with_deepeval_fails_when_no_text_matches():
    with mock.patch.object(deepeval, 'get_text_similarity_with_deepeval', return_value=0.2):
        with pytest.raises(AssertionError, match='DeepEval similarity is below threshold'):
            deepeval.assert_text_similarity_with_deepeval('actual', ['wrong'], threshold=0.7)


def test_assert_answer_evaluation_with_deepeval_passes_when_any_reference_matches():
    with mock.patch.object(
        deepeval, 'get_answer_evaluation_with_deepeval', side_effect=[(0.3, 'wrong'), (0.9, 'right')]
    ) as evaluation:
        deepeval.assert_answer_evaluation_with_deepeval(
            'actual', ['wrong reference', 'right reference'], threshold=0.7, question='question'
        )

    assert evaluation.call_count == 2
    assert evaluation.call_args.args[3] == 'question'


def test_assert_answer_evaluation_with_deepeval_fails_when_no_reference_matches():
    with mock.patch.object(deepeval, 'get_answer_evaluation_with_deepeval', return_value=(0.2, 'wrong')):
        with pytest.raises(AssertionError, match='DeepEval answer evaluation is below threshold'):
            deepeval.assert_answer_evaluation_with_deepeval('actual', 'reference', threshold=0.7)


def test_assert_text_criteria_with_deepeval():
    analysis = {'overall_match': 0.8, 'features': []}
    with mock.patch.object(deepeval, 'get_text_criteria_analysis_with_deepeval', return_value=analysis):
        deepeval.assert_text_criteria_with_deepeval('text', ['criterion'], threshold=0.7)


def test_assert_text_criteria_with_deepeval_fails_below_threshold():
    analysis = {'overall_match': 0.6, 'features': [{'name': 'criterion', 'score': 0.2}]}
    with mock.patch.object(deepeval, 'get_text_criteria_analysis_with_deepeval', return_value=analysis):
        with pytest.raises(AssertionError, match='DeepEval text criteria analysis is below threshold'):
            deepeval.assert_text_criteria_with_deepeval('text', ['criterion'], threshold=0.7)


def test_deepeval_functions_fail_with_clear_error_when_dependency_is_missing():
    with mock.patch.object(deepeval, 'LLMTestCase', None):
        with pytest.raises(ImportError, match='DeepEval is not installed'):
            deepeval.get_text_similarity_with_deepeval('actual', 'expected')
