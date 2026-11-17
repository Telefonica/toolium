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

import json
import logging
from copy import deepcopy
from dataclasses import asdict, dataclass
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version

from toolium.driver_wrappers_pool import DriverWrappersPool

_DEEPEVAL_IMPORT_ERROR = None

try:
    from deepeval.metrics import (
        AnswerRelevancyMetric,
        ContextualPrecisionMetric,
        ContextualRecallMetric,
        ContextualRelevancyMetric,
        ConversationalGEval,
        ConversationCompletenessMetric,
        FaithfulnessMetric,
        GEval,
        HallucinationMetric,
        JsonCorrectnessMetric,
        KnowledgeRetentionMetric,
        PIILeakageMetric,
        SummarizationMetric,
        ToolCorrectnessMetric,
        ToxicityMetric,
        TurnRelevancyMetric,
    )
    from deepeval.models import GPTModel
    from deepeval.models.llms import AzureOpenAIModel
    from deepeval.test_case import (
        ConversationalTestCase,
        LLMTestCase,
        MultiTurnParams,
        SingleTurnParams,
        ToolCall,
        ToolCallParams,
        Turn,
    )
except ImportError as exc:
    _DEEPEVAL_IMPORT_ERROR = exc
    AnswerRelevancyMetric = ContextualPrecisionMetric = ContextualRecallMetric = ContextualRelevancyMetric = (
        FaithfulnessMetric
    ) = GEval = HallucinationMetric = JsonCorrectnessMetric = PIILeakageMetric = SummarizationMetric = (
        ToolCorrectnessMetric
    ) = ToxicityMetric = LLMTestCase = SingleTurnParams = ToolCall = ToolCallParams = None
    ConversationalGEval = ConversationCompletenessMetric = KnowledgeRetentionMetric = TurnRelevancyMetric = None
    ConversationalTestCase = MultiTurnParams = Turn = None
    GPTModel = None
    AzureOpenAIModel = None

logger = logging.getLogger(__name__)


def _require_deepeval():
    if _DEEPEVAL_IMPORT_ERROR is None:
        return
    if isinstance(_DEEPEVAL_IMPORT_ERROR, ModuleNotFoundError) and _DEEPEVAL_IMPORT_ERROR.name == 'deepeval':
        raise ImportError(
            "DeepEval is not installed. Please run 'pip install toolium[deepeval]'"
        ) from _DEEPEVAL_IMPORT_ERROR
    try:
        installed_version = version('deepeval')
    except PackageNotFoundError:
        installed_version = 'unknown (package metadata unavailable)'
    raise ImportError(
        f'Could not import DeepEval (installed version: {installed_version}; required: deepeval~=3.9.9). '
        f'Check version compatibility and dependencies. Original error: {_DEEPEVAL_IMPORT_ERROR}'
    ) from _DEEPEVAL_IMPORT_ERROR


def _get_deepeval_config(config, key, default=None):
    """Resolve each evaluator setting from DeepEval, AI, then its default."""
    missing = object()
    value = config.get_optional('DeepEval', key, missing)
    if value is missing:
        value = config.get_optional('AI', key, default)
    return value


def _get_model(provider, model_name, kwargs, config=None):
    if config is None:
        config = DriverWrappersPool.get_default_wrapper().config
    deepeval_provider = provider if provider is not None else _get_deepeval_config(config, 'provider', 'openai')
    deepeval_model = (
        model_name if model_name is not None else _get_deepeval_config(config, 'openai_model', 'gpt-4o-mini')
    )
    deepeval_model_kwargs = {
        'model': deepeval_model,
        'api_key': _get_deepeval_config(config, f'{deepeval_provider}_api_key'),
        'temperature': config.get_optional('DeepEval', f'{deepeval_provider}_temperature', 0.0),
    }
    if deepeval_provider == 'openai':
        deepeval_model_class = GPTModel
    elif deepeval_provider == 'azure':
        deepeval_model_class = AzureOpenAIModel
        deepeval_model_kwargs.update(
            base_url=_get_deepeval_config(config, 'azure_endpoint'),
            deployment_name=_get_deepeval_config(config, 'azure_deployment', deepeval_model),
            api_version=_get_deepeval_config(config, 'api_version'),
        )
    else:
        raise ValueError(f"Unknown provider: '{deepeval_provider}', please use 'openai' or 'azure'")
    deepeval_model_kwargs.update(kwargs)
    return deepeval_model_class(**deepeval_model_kwargs)


@dataclass(frozen=True)
class _MetricResult:
    score: float
    reason: str
    passed: bool


def _measure(metric, test_case):
    metric.measure(test_case)
    return _MetricResult(float(metric.score), getattr(metric, 'reason', '') or '', bool(metric.is_successful()))


def _assert_metric_result(result, label, threshold):
    if not result.passed:
        raise AssertionError(
            f'{label} evaluation failed: score={result.score}, requested threshold={threshold}\nReason: {result.reason}'
        )


def create_deepeval_model(model_name=None, provider=None, config=None, **kwargs):
    """Create a judge using explicit options, [DeepEval], [AI], then defaults.

    Pass a Toolium config parser to avoid consulting the default driver wrapper.
    Temperature only falls back to [DeepEval], then 0.0.
    The caller owns the returned model and its lifecycle.
    """
    _require_deepeval()
    return _get_model(provider, model_name, kwargs, config=config)


def _resolve_model(provider, model_name, options):
    model = options.pop('model', None)
    model_kwargs = options.pop('model_kwargs', {})
    if model is not None:
        if provider is not None or model_name is not None or model_kwargs:
            raise ValueError('model cannot be combined with provider, model_name or model_kwargs')
        return model
    return _get_model(provider, model_name, model_kwargs)


# These default rubrics are versioned with Toolium's source. Never mutate them.
_SIMILARITY_STEPS = (
    'Compare the meaning of the actual output with the expected output.',
    'Penalize contradictions and missing or changed essential information, but allow equivalent wording.',
    'Assign a higher score when both outputs convey the same meaning.',
)
_ANSWER_STEPS = (
    'Use the expected output as the reference and the input as the question, when provided.',
    'Check the actual output for factual agreement, completeness and relevance.',
    'Penalize contradictions, unsupported claims and missing essential details; allow equivalent wording.',
)
_CONVERSATION_STEPS = (
    'Read the user and assistant turns in order and identify the user requests.',
    'Check whether assistant replies address those requests and remain consistent across turns.',
    'Penalize contradictions, ignored corrections and unresolved requests; do not infer unobserved actions.',
)


def _geval_options(options, default_steps):
    options = deepcopy(options)
    if 'evaluation_steps' not in options and 'criteria' not in options:
        options['evaluation_steps'] = list(default_steps)
    return options


_CONTEXTUAL_METRICS = {
    'faithfulness': 'FaithfulnessMetric',
    'contextual_relevancy': 'ContextualRelevancyMetric',
    'contextual_precision': 'ContextualPrecisionMetric',
    'contextual_recall': 'ContextualRecallMetric',
}


def evaluate_contextual_with_deepeval(
    input_text,
    actual_output,
    retrieved_context,
    expected_output=None,
    metrics='faithfulness',
    metric_config=None,
    model_name=None,
    threshold=0.7,
    provider=None,
    **kwargs,
):
    """Evaluate one or more contextual metrics against the same test case.

    ``metrics`` accepts one metric name or a list of names. Alternatively, ``metric_config``
    defines each metric, its required threshold and metric-specific options. The retrieved context may
    contain plain strings or JSON-compatible dictionaries/lists. Returns per-metric scores,
    reasons and pass/fail values, plus an aggregated ``passed`` value.

    :raises ValueError: if metrics are unknown, configuration is incomplete, or a required
        expected output is missing.
    """
    _require_deepeval()
    if metric_config is not None:
        if metrics != 'faithfulness' or threshold != 0.7 or kwargs.get('metric_kwargs'):
            raise ValueError('Use either metric_config or metrics/threshold/metric_kwargs, not both')
        if not metric_config:
            raise ValueError('metric_config must contain at least one metric')
        metric_names = list(metric_config)
    else:
        metric_names = [metrics] if isinstance(metrics, str) else list(metrics)
    if metric_config is None:
        if len(set(metric_names)) != len(metric_names):
            raise ValueError('Duplicate contextual metrics are not allowed')
        metric_options = kwargs.pop('metric_kwargs', {})
        metric_config = {
            name: {
                **metric_options,
                'threshold': threshold.get(name, 0.7) if isinstance(threshold, dict) else threshold,
            }
            for name in metric_names
        }
    _validate_metric_config(metric_config, _CONTEXTUAL_METRICS, 'contextual')
    if any(name in ('contextual_precision', 'contextual_recall') for name in metric_config) and expected_output is None:
        raise ValueError('expected_output is required for contextual_precision and contextual_recall')
    model = _resolve_model(provider, model_name, kwargs)
    if kwargs:
        raise TypeError(f'Unexpected evaluation options: {", ".join(kwargs)}')
    test_case = LLMTestCase(
        input=input_text,
        actual_output=actual_output,
        expected_output=expected_output,
        retrieval_context=_serialize_context(retrieved_context),
    )
    return _evaluate_metrics(test_case, metric_config, _CONTEXTUAL_METRICS, model)


def assert_contextual_with_deepeval(*args, **kwargs):
    """Assert that every requested contextual metric meets its threshold.

    The assertion includes all failed metric results in the error message so callers can
    diagnose multiple failures from one evaluation.
    """
    evaluation = evaluate_contextual_with_deepeval(*args, **kwargs)
    if not evaluation['passed']:
        failed = {name: result for name, result in evaluation['results'].items() if not result['passed']}
        raise AssertionError(f'Contextual DeepEval evaluation failed: {failed}')


def _evaluate_text_similarity_with_deepeval(
    text, expected_text, model_name=None, threshold=0.7, provider=None, **kwargs
):
    """Return an LLM-as-a-Judge semantic similarity score for two texts.

    The score is between 0 and 1. ``model_name`` and ``provider`` select the evaluator;
    additional DeepEval ``GEval`` options can be passed through ``kwargs``.
    """
    _require_deepeval()
    model = _resolve_model(provider, model_name, kwargs)
    kwargs = _geval_options(kwargs, _SIMILARITY_STEPS)
    metric = GEval(
        name='Text semantic similarity',
        criteria=kwargs.pop('criteria', 'The actual output conveys the same meaning as the expected output.'),
        evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
        threshold=threshold,
        model=model,
        **kwargs,
    )
    result = _measure(metric, LLMTestCase(input='', actual_output=text, expected_output=expected_text))
    score, _ = result.score, result.reason
    logger.info("DeepEval semantic similarity: %s between '%s' and '%s'", score, text, expected_text)
    return result


def get_text_similarity_with_deepeval(text, expected_text, model_name=None, threshold=0.7, provider=None, **kwargs):
    """Return an LLM-as-a-Judge semantic similarity score for two texts.

    The score is between 0 and 1. ``model_name`` and ``provider`` select the evaluator;
    additional DeepEval ``GEval`` options can be passed through ``kwargs``.

        Pass ``model=judge`` to reuse a caller-owned DeepEval model.
    """
    result = _evaluate_text_similarity_with_deepeval(text, expected_text, model_name, threshold, provider, **kwargs)
    return result.score


def _serialize_context(context_items):
    """Normalize a string, dictionary or iterable of context items to DeepEval strings.

    A string or dictionary is one item. A list contains separate items; wrap a JSON
    array in an outer list to serialize the entire array as a single item.
    """
    if isinstance(context_items, (str, dict)):
        context_items = [context_items]
    return [
        json.dumps(item, ensure_ascii=False, indent=2) if isinstance(item, (dict, list)) else item
        for item in context_items
    ]


def _evaluate_summarization_with_deepeval(
    source_text, summary, model_name=None, threshold=0.7, provider=None, **kwargs
):
    """Return (score, reason) for a summary against its original source text."""
    _require_deepeval()
    model = _resolve_model(provider, model_name, kwargs)
    metric = SummarizationMetric(threshold=threshold, model=model, **kwargs)
    result = _measure(metric, LLMTestCase(input=source_text, actual_output=summary))
    return result


def get_summarization_with_deepeval(source_text, summary, model_name=None, threshold=0.7, provider=None, **kwargs):
    """Return (score, reason) for a summary against its original source text.

    Pass ``model=judge`` to reuse a caller-owned DeepEval model.
    """
    result = _evaluate_summarization_with_deepeval(source_text, summary, model_name, threshold, provider, **kwargs)
    return (result.score, result.reason)


def assert_summarization_with_deepeval(source_text, summary, threshold, model_name=None, provider=None, **kwargs):
    """Assert that the summary passes DeepEval's decision for the source text."""
    result = _evaluate_summarization_with_deepeval(source_text, summary, model_name, threshold, provider, **kwargs)
    _assert_metric_result(result, 'DeepEval summarization', threshold)


def _evaluate_pii_leakage_with_deepeval(
    actual_output, model_name=None, threshold=1.0, provider=None, input_text='', **kwargs
):
    """Evaluate possible personally identifiable information leakage.

    A higher score indicates better privacy protection; 1.0 means no PII leakage
    was detected. The threshold is the minimum acceptable privacy score.
    """
    _require_deepeval()
    model = _resolve_model(provider, model_name, kwargs)
    metric = PIILeakageMetric(threshold=threshold, model=model, **kwargs)
    result = _measure(metric, LLMTestCase(input=input_text, actual_output=actual_output))
    score = result.score
    logger.info('DeepEval PII leakage: %s', score)
    return result


def get_pii_leakage_with_deepeval(
    actual_output, model_name=None, threshold=1.0, provider=None, input_text='', **kwargs
):
    """Evaluate possible personally identifiable information leakage.

    A higher score indicates better privacy protection; 1.0 means no PII leakage
    was detected. The threshold is the minimum acceptable privacy score.

        Pass ``model=judge`` to reuse a caller-owned DeepEval model.
    """
    result = _evaluate_pii_leakage_with_deepeval(actual_output, model_name, threshold, provider, input_text, **kwargs)
    return (result.score, result.reason)


def assert_pii_leakage_with_deepeval(actual_output, threshold, model_name=None, provider=None, input_text='', **kwargs):
    """Assert that an output meets the minimum PII privacy score."""
    result = _evaluate_pii_leakage_with_deepeval(actual_output, model_name, threshold, provider, input_text, **kwargs)
    _assert_metric_result(result, 'DeepEval PII privacy score', threshold)


def _evaluate_toxicity_with_deepeval(
    actual_output, model_name=None, threshold=0.7, provider=None, input_text='', **kwargs
):
    """Evaluate the toxicity of an output."""
    _require_deepeval()
    model = _resolve_model(provider, model_name, kwargs)
    metric = ToxicityMetric(threshold=threshold, model=model, **kwargs)
    result = _measure(metric, LLMTestCase(input=input_text, actual_output=actual_output))
    score = result.score
    logger.info('DeepEval toxicity: %s', score)
    return result


def get_toxicity_with_deepeval(actual_output, model_name=None, threshold=0.7, provider=None, input_text='', **kwargs):
    """Evaluate the toxicity of an output.

    Pass ``model=judge`` to reuse a caller-owned DeepEval model.
    """
    result = _evaluate_toxicity_with_deepeval(actual_output, model_name, threshold, provider, input_text, **kwargs)
    return (result.score, result.reason)


def assert_toxicity_with_deepeval(actual_output, threshold, model_name=None, provider=None, input_text='', **kwargs):
    """Assert that an output stays below the toxicity threshold."""
    result = _evaluate_toxicity_with_deepeval(actual_output, model_name, threshold, provider, input_text, **kwargs)
    _assert_metric_result(result, 'DeepEval toxicity', threshold)


def _evaluate_tool_correctness_with_deepeval(
    input_text, tools_called, expected_tools, model_name=None, threshold=0.7, provider=None, **kwargs
):
    """Evaluate expected tool calls using DeepEval's selected comparison fields.

    By default, only tool names are compared. Pass ``evaluation_params`` containing
    ``ToolCallParams.INPUT_PARAMETERS`` and/or ``ToolCallParams.OUTPUT`` to also
    compare arguments and/or output. Providing those values in ``expected_tools``
    alone does not enable their comparison.
    """
    _require_deepeval()
    model = _resolve_model(provider, model_name, kwargs)
    available_tools = kwargs.pop('available_tools', None)
    evaluation_params = kwargs.pop('evaluation_params', None)
    metric_kwargs = {'threshold': threshold, 'model': model}
    if available_tools is not None:
        metric_kwargs['available_tools'] = available_tools
    if evaluation_params is not None:
        metric_kwargs['evaluation_params'] = evaluation_params
    metric = ToolCorrectnessMetric(**metric_kwargs, **kwargs)
    result = _measure(
        metric,
        LLMTestCase(
            input=input_text,
            actual_output='',
            tools_called=deepcopy(tools_called),
            expected_tools=deepcopy(expected_tools),
        ),
    )
    score = result.score
    logger.info('DeepEval tool correctness: %s for input %s', score, input_text)
    return result


def get_tool_correctness_with_deepeval(
    input_text, tools_called, expected_tools, model_name=None, threshold=0.7, provider=None, **kwargs
):
    """Return (score, reason) for the expected tool calls.

    By default, only tool names are compared. To also compare arguments and output,
    pass ``evaluation_params=[ToolCallParams.INPUT_PARAMETERS, ToolCallParams.OUTPUT]``.
    Either field can be selected independently. Providing arguments or output in
    ``expected_tools`` alone does not enable their comparison.

    Pass ``model=judge`` to reuse a caller-owned DeepEval model.
    """
    result = _evaluate_tool_correctness_with_deepeval(
        input_text, tools_called, expected_tools, model_name, threshold, provider, **kwargs
    )
    return (result.score, result.reason)


def assert_tool_correctness_with_deepeval(
    input_text, tools_called, expected_tools, threshold, model_name=None, provider=None, **kwargs
):
    """Assert that the tool calls pass DeepEval's decision for the selected fields.

    By default, only tool names are compared. To also compare arguments and output,
    pass ``evaluation_params=[ToolCallParams.INPUT_PARAMETERS, ToolCallParams.OUTPUT]``.
    Either field can be selected independently. Providing arguments or output in
    ``expected_tools`` alone does not enable their comparison.
    """
    result = _evaluate_tool_correctness_with_deepeval(
        input_text, tools_called, expected_tools, model_name, threshold, provider, **kwargs
    )
    _assert_metric_result(result, 'DeepEval tool correctness', threshold)


def _evaluate_contextual_recall_with_deepeval(
    input_text,
    actual_output,
    expected_output,
    retrieved_context,
    model_name=None,
    threshold=0.7,
    provider=None,
    **kwargs,
):
    """Evaluate whether the retrieved context covers the expected answer information."""
    _require_deepeval()
    model = _resolve_model(provider, model_name, kwargs)
    metric = ContextualRecallMetric(threshold=threshold, model=model, **kwargs)
    result = _measure(
        metric,
        LLMTestCase(
            input=input_text,
            actual_output=actual_output,
            expected_output=expected_output,
            retrieval_context=_serialize_context(retrieved_context),
        ),
    )
    score = result.score
    logger.info('DeepEval contextual recall: %s for input %s', score, input_text)
    return result


def get_contextual_recall_with_deepeval(
    input_text,
    actual_output,
    expected_output,
    retrieved_context,
    model_name=None,
    threshold=0.7,
    provider=None,
    **kwargs,
):
    """Evaluate whether the retrieved context covers the expected answer information.

    Pass ``model=judge`` to reuse a caller-owned DeepEval model.
    """
    result = _evaluate_contextual_recall_with_deepeval(
        input_text, actual_output, expected_output, retrieved_context, model_name, threshold, provider, **kwargs
    )
    return (result.score, result.reason)


def assert_contextual_recall_with_deepeval(
    input_text, actual_output, expected_output, retrieved_context, threshold, model_name=None, provider=None, **kwargs
):
    """Assert that the retrieved context covers the expected answer information."""
    result = _evaluate_contextual_recall_with_deepeval(
        input_text, actual_output, expected_output, retrieved_context, model_name, threshold, provider, **kwargs
    )
    _assert_metric_result(result, 'DeepEval contextual recall', threshold)


def _evaluate_contextual_precision_with_deepeval(
    input_text,
    actual_output,
    expected_output,
    retrieved_context,
    model_name=None,
    threshold=0.7,
    provider=None,
    **kwargs,
):
    """Evaluate whether retrieved context is precise and relevant to the expected answer."""
    _require_deepeval()
    model = _resolve_model(provider, model_name, kwargs)
    metric = ContextualPrecisionMetric(threshold=threshold, model=model, **kwargs)
    result = _measure(
        metric,
        LLMTestCase(
            input=input_text,
            actual_output=actual_output,
            expected_output=expected_output,
            retrieval_context=_serialize_context(retrieved_context),
        ),
    )
    score = result.score
    logger.info('DeepEval contextual precision: %s for input %s', score, input_text)
    return result


def get_contextual_precision_with_deepeval(
    input_text,
    actual_output,
    expected_output,
    retrieved_context,
    model_name=None,
    threshold=0.7,
    provider=None,
    **kwargs,
):
    """Evaluate whether retrieved context is precise and relevant to the expected answer.

    Pass ``model=judge`` to reuse a caller-owned DeepEval model.
    """
    result = _evaluate_contextual_precision_with_deepeval(
        input_text, actual_output, expected_output, retrieved_context, model_name, threshold, provider, **kwargs
    )
    return (result.score, result.reason)


def assert_contextual_precision_with_deepeval(
    input_text, actual_output, expected_output, retrieved_context, threshold, model_name=None, provider=None, **kwargs
):
    """Assert that retrieved context is precise and relevant."""
    result = _evaluate_contextual_precision_with_deepeval(
        input_text, actual_output, expected_output, retrieved_context, model_name, threshold, provider, **kwargs
    )
    _assert_metric_result(result, 'DeepEval contextual precision', threshold)


def _evaluate_contextual_relevancy_with_deepeval(
    input_text, actual_output, retrieved_context, model_name=None, threshold=0.7, provider=None, **kwargs
):
    """Evaluate whether the retrieved context is relevant to the input and answer."""
    _require_deepeval()
    model = _resolve_model(provider, model_name, kwargs)
    metric = ContextualRelevancyMetric(threshold=threshold, model=model, **kwargs)
    result = _measure(
        metric,
        LLMTestCase(
            input=input_text,
            actual_output=actual_output,
            retrieval_context=_serialize_context(retrieved_context),
        ),
    )
    score = result.score
    logger.info('DeepEval contextual relevancy: %s for input %s', score, input_text)
    return result


def get_contextual_relevancy_with_deepeval(
    input_text, actual_output, retrieved_context, model_name=None, threshold=0.7, provider=None, **kwargs
):
    """Evaluate whether the retrieved context is relevant to the input and answer.

    Pass ``model=judge`` to reuse a caller-owned DeepEval model.
    """
    result = _evaluate_contextual_relevancy_with_deepeval(
        input_text, actual_output, retrieved_context, model_name, threshold, provider, **kwargs
    )
    return (result.score, result.reason)


def assert_contextual_relevancy_with_deepeval(
    input_text, actual_output, retrieved_context, threshold, model_name=None, provider=None, **kwargs
):
    """Assert that the retrieved context is relevant."""
    result = _evaluate_contextual_relevancy_with_deepeval(
        input_text, actual_output, retrieved_context, model_name, threshold, provider, **kwargs
    )
    _assert_metric_result(result, 'DeepEval contextual relevancy', threshold)


def _evaluate_json_correctness_with_deepeval(
    actual_output, expected_schema, model_name=None, threshold=0.7, provider=None, **kwargs
):
    """Evaluate whether a JSON response matches a Pydantic schema."""
    _require_deepeval()
    model = _resolve_model(provider, model_name, kwargs)
    metric = JsonCorrectnessMetric(expected_schema=expected_schema, model=model, threshold=threshold, **kwargs)
    result = _measure(metric, LLMTestCase(input='', actual_output=actual_output))
    score = result.score
    logger.info('DeepEval JSON correctness: %s', score)
    return result


def get_json_correctness_with_deepeval(
    actual_output, expected_schema, model_name=None, threshold=0.7, provider=None, **kwargs
):
    """Evaluate whether a JSON response matches a Pydantic schema.

    Pass ``model=judge`` to reuse a caller-owned DeepEval model.
    """
    result = _evaluate_json_correctness_with_deepeval(
        actual_output, expected_schema, model_name, threshold, provider, **kwargs
    )
    return (result.score, result.reason)


def assert_json_correctness_with_deepeval(
    actual_output, expected_schema, threshold, model_name=None, provider=None, **kwargs
):
    """Assert that a JSON response matches a Pydantic schema."""
    result = _evaluate_json_correctness_with_deepeval(
        actual_output, expected_schema, model_name, threshold, provider, **kwargs
    )
    _assert_metric_result(result, 'DeepEval JSON correctness', threshold)


def _evaluate_hallucination_evaluation_with_deepeval(
    actual_output, retrieved_context, model_name=None, threshold=0.7, provider=None, input_text='', **kwargs
):
    """Evaluate whether an output contains unsupported information."""
    _require_deepeval()
    model = _resolve_model(provider, model_name, kwargs)
    metric = HallucinationMetric(threshold=threshold, model=model, **kwargs)
    result = _measure(
        metric,
        LLMTestCase(input=input_text, actual_output=actual_output, context=_serialize_context(retrieved_context)),
    )
    score = result.score
    logger.info('DeepEval hallucination score: %s for output %s', score, actual_output)
    return result


def get_hallucination_evaluation_with_deepeval(
    actual_output, retrieved_context, model_name=None, threshold=0.7, provider=None, input_text='', **kwargs
):
    """Evaluate whether an output contains unsupported information.

    Pass ``model=judge`` to reuse a caller-owned DeepEval model.
    """
    result = _evaluate_hallucination_evaluation_with_deepeval(
        actual_output, retrieved_context, model_name, threshold, provider, input_text, **kwargs
    )
    return (result.score, result.reason)


def assert_hallucination_evaluation_with_deepeval(
    actual_output, retrieved_context, threshold, model_name=None, provider=None, input_text='', **kwargs
):
    """Assert that an output stays below the hallucination threshold."""
    result = _evaluate_hallucination_evaluation_with_deepeval(
        actual_output, retrieved_context, model_name, threshold, provider, input_text, **kwargs
    )
    _assert_metric_result(result, 'DeepEval hallucination', threshold)


def _evaluate_answer_relevancy_with_deepeval(
    actual_output, input_text, model_name=None, threshold=0.7, provider=None, **kwargs
):
    """Evaluate whether an answer is relevant to the input question."""
    _require_deepeval()
    model = _resolve_model(provider, model_name, kwargs)
    metric = AnswerRelevancyMetric(threshold=threshold, model=model, **kwargs)
    result = _measure(metric, LLMTestCase(input=input_text, actual_output=actual_output))
    score = result.score
    logger.info('DeepEval answer relevancy: %s for input %s', score, input_text)
    return result


def get_answer_relevancy_with_deepeval(
    actual_output, input_text, model_name=None, threshold=0.7, provider=None, **kwargs
):
    """Evaluate whether an answer is relevant to the input question.

    Pass ``model=judge`` to reuse a caller-owned DeepEval model.
    """
    result = _evaluate_answer_relevancy_with_deepeval(
        actual_output, input_text, model_name, threshold, provider, **kwargs
    )
    return (result.score, result.reason)


def assert_answer_relevancy_with_deepeval(
    actual_output, input_text, threshold, model_name=None, provider=None, **kwargs
):
    """Assert that an answer is relevant to the input question."""
    result = _evaluate_answer_relevancy_with_deepeval(
        actual_output, input_text, model_name, threshold, provider, **kwargs
    )
    _assert_metric_result(result, 'DeepEval answer relevancy', threshold)


def _evaluate_faithfulness_evaluation_with_deepeval(
    actual_output, retrieved_context, model_name=None, threshold=0.7, provider=None, input_text='', **kwargs
):
    """Evaluate whether an output is supported by text or JSON API context."""
    _require_deepeval()
    retrieved_context = _serialize_context(retrieved_context)
    model = _resolve_model(provider, model_name, kwargs)
    metric = FaithfulnessMetric(threshold=threshold, model=model, **kwargs)
    result = _measure(
        metric,
        LLMTestCase(input=input_text, actual_output=actual_output, retrieval_context=retrieved_context),
    )
    score = result.score
    logger.info('DeepEval faithfulness: %s for output %s', score, actual_output)
    return result


def get_faithfulness_evaluation_with_deepeval(
    actual_output, retrieved_context, model_name=None, threshold=0.7, provider=None, input_text='', **kwargs
):
    """Evaluate whether an output is supported by text or JSON API context.

    Pass ``model=judge`` to reuse a caller-owned DeepEval model.
    """
    result = _evaluate_faithfulness_evaluation_with_deepeval(
        actual_output, retrieved_context, model_name, threshold, provider, input_text, **kwargs
    )
    return (result.score, result.reason)


def assert_faithfulness_with_deepeval(
    actual_output, retrieved_context, threshold, model_name=None, provider=None, input_text='', **kwargs
):
    """Assert that an output is supported by the supplied context."""
    result = _evaluate_faithfulness_evaluation_with_deepeval(
        actual_output, retrieved_context, model_name, threshold, provider, input_text, **kwargs
    )
    _assert_metric_result(result, 'DeepEval faithfulness', threshold)


def _evaluate_answer_evaluation_with_deepeval(
    llm_answer, reference_answer, model_name=None, question=None, threshold=0.7, provider=None, **kwargs
):
    """Return answer correctness score and DeepEval explanation."""
    _require_deepeval()
    model = _resolve_model(provider, model_name, kwargs)
    kwargs = _geval_options(kwargs, _ANSWER_STEPS)
    criteria = kwargs.pop(
        'criteria',
        'The actual answer must be semantically equivalent, factually correct, complete, and relevant to the question.',
    )
    metric = GEval(
        name='Answer correctness',
        criteria=criteria,
        evaluation_params=[
            SingleTurnParams.INPUT,
            SingleTurnParams.ACTUAL_OUTPUT,
            SingleTurnParams.EXPECTED_OUTPUT,
        ],
        threshold=threshold,
        model=model,
        **kwargs,
    )
    result = _measure(
        metric,
        LLMTestCase(input=question or '', actual_output=llm_answer, expected_output=reference_answer),
    )
    return result


def get_answer_evaluation_with_deepeval(
    llm_answer, reference_answer, model_name=None, question=None, threshold=0.7, provider=None, **kwargs
):
    """Return answer correctness score and DeepEval explanation.

    Pass ``model=judge`` to reuse a caller-owned DeepEval model.
    """
    result = _evaluate_answer_evaluation_with_deepeval(
        llm_answer, reference_answer, model_name, question, threshold, provider, **kwargs
    )
    return (result.score, result.reason)


def get_text_criteria_analysis_with_deepeval(
    text_input, text_criteria, model_name=None, threshold=0.7, provider=None, **kwargs
):
    """Evaluate each text characteristic independently using DeepEval GEval."""
    _require_deepeval()
    if 'criteria' in kwargs:
        raise ValueError('Use text_criteria to select characteristics, not criteria')
    model = _resolve_model(provider, model_name, kwargs)
    text_criteria = [text_criteria] if isinstance(text_criteria, str) else list(text_criteria)
    if not text_criteria:
        raise ValueError('text_criteria must contain at least one characteristic')
    features = []
    scores = []
    for criterion in text_criteria:
        metric_options = _geval_options(
            kwargs,
            (
                f'Check the actual output for this characteristic: {criterion}',
                'Assign a higher score when the text satisfies the characteristic; cite concrete failures.',
            ),
        )
        metric = GEval(
            name='Text criterion',
            criteria=f'The text satisfies this characteristic: {criterion}',
            evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT],
            threshold=threshold,
            model=model,
            **metric_options,
        )
        result = _measure(metric, LLMTestCase(input='', actual_output=text_input))
        score, reason = result.score, result.reason
        scores.append(score)
        if not result.passed:
            features.append({'name': criterion, 'score': score, 'explanation': reason})
    overall_match = sum(scores) / len(scores) if scores else 0.0
    return {'overall_match': overall_match, 'features': features, 'passed': not features}


def assert_text_similarity_with_deepeval(text, expected_texts, threshold, model_name=None, provider=None, **kwargs):
    """Assert that text is semantically similar to at least one expected text."""
    expected_texts = [expected_texts] if isinstance(expected_texts, str) else expected_texts
    failures = []
    for expected_text in expected_texts:
        result = _evaluate_text_similarity_with_deepeval(text, expected_text, model_name, threshold, provider, **kwargs)
        if result.passed:
            return
        failures.append(f'{result.score} (requested threshold: {threshold}): {expected_text}')
    raise AssertionError('DeepEval similarity evaluation failed:\n' + '\n'.join(failures))


def assert_answer_evaluation_with_deepeval(
    llm_answer, reference_answers, threshold, model_name=None, question=None, **kwargs
):
    """Assert that an answer meets the threshold for at least one reference answer."""
    reference_answers = [reference_answers] if isinstance(reference_answers, str) else reference_answers
    failures = []
    for reference_answer in reference_answers:
        result = _evaluate_answer_evaluation_with_deepeval(
            llm_answer, reference_answer, model_name, question, threshold, **kwargs
        )
        if result.passed:
            return
        failures.append(f'{result.score} (requested threshold: {threshold}): {reference_answer}')
    raise AssertionError('DeepEval answer evaluation evaluation failed:\n' + '\n'.join(failures))


def assert_text_criteria_with_deepeval(text_input, text_criteria, threshold, model_name=None, **kwargs):
    """Assert that every selected characteristic passes; the average is informational."""
    analysis = get_text_criteria_analysis_with_deepeval(text_input, text_criteria, model_name, threshold, **kwargs)
    if not analysis['passed']:
        raise AssertionError(
            f'DeepEval text criteria analysis failed: one or more characteristics did not pass.\n'
            f'Overall match (informational mean): {analysis["overall_match"]}; requested threshold: {threshold}\n'
            f'Failed features: {analysis["features"]}'
        )


_RESPONSE_METRICS = {
    **_CONTEXTUAL_METRICS,
    'answer_relevancy': 'AnswerRelevancyMetric',
    'toxicity': 'ToxicityMetric',
    'pii_leakage': 'PIILeakageMetric',
    'hallucination': 'HallucinationMetric',
    'json_correctness': 'JsonCorrectnessMetric',
    'tool_correctness': 'ToolCorrectnessMetric',
    'text_similarity': 'GEval',
    'answer_correctness': 'GEval',
    'geval': 'GEval',
}
_CONVERSATION_METRICS = {
    'turn_relevancy': 'TurnRelevancyMetric',
    'knowledge_retention': 'KnowledgeRetentionMetric',
    'conversation_completeness': 'ConversationCompletenessMetric',
    'conversational_geval': 'ConversationalGEval',
}


def _validate_metric_config(metric_config, registry, kind):
    if not isinstance(metric_config, dict) or not metric_config:
        raise ValueError('metric_config must contain at least one metric')
    unknown = set(metric_config) - set(registry)
    if unknown:
        raise ValueError(f'Unknown {kind} metric(s): {", ".join(sorted(unknown))}')
    for name, options in metric_config.items():
        if not isinstance(options, dict) or 'threshold' not in options:
            raise ValueError(f"Missing threshold for metric '{name}'")
        threshold = options['threshold']
        if not isinstance(threshold, (int, float)) or not 0 <= threshold <= 1:
            raise ValueError(f"Threshold for metric '{name}' must be between 0 and 1")
        if 'model' in options:
            raise ValueError('Pass the judge model at evaluation level, not inside metric_config')
        if name == 'geval' and not (options.get('criteria') or options.get('evaluation_steps')):
            raise ValueError('geval requires criteria or evaluation_steps')


def _evaluation_metadata(model, metrics):
    from deepeval.models import DeepEvalBaseLLM, GPTModel
    from deepeval.models.llms import AzureOpenAIModel

    judge = {}
    if isinstance(model, AzureOpenAIModel):
        judge.update(provider='azure', deployment=model.deployment_name, temperature=model.temperature)
    elif isinstance(model, GPTModel):
        judge.update(provider='openai', temperature=model.temperature)
    if isinstance(model, DeepEvalBaseLLM):
        model_name = model.name if judge else model.get_model_name()
        if isinstance(model_name, str):
            judge['model'] = model_name

    metadata = {'judge': judge, 'metrics': metrics}
    for package in ('toolium', 'deepeval'):
        try:
            metadata[f'{package}_version'] = version(package)
        except PackageNotFoundError:
            metadata[f'{package}_version'] = None
    return metadata


def _evaluate_metrics(test_case, metric_config, registry, model, *, include_metadata=False):
    results = {}
    metric_metadata = {}
    for name, options in deepcopy(metric_config).items():
        if name in ('text_similarity', 'answer_correctness', 'geval'):
            defaults = _SIMILARITY_STEPS if name == 'text_similarity' else _ANSWER_STEPS
            options = _geval_options(options, defaults)
            options.setdefault('name', name)
            params = [SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT]
            if name == 'answer_correctness':
                params.insert(0, SingleTurnParams.INPUT)
            options.setdefault('evaluation_params', params)
        elif name == 'conversational_geval':
            options = _geval_options(options, _CONVERSATION_STEPS)
            options.setdefault('name', 'Conversation quality')
            options.setdefault('evaluation_params', [MultiTurnParams.CONTENT])
        metric = globals()[registry[name]](model=model, **options)
        results[name] = asdict(_measure(metric, test_case))
        if include_metadata:
            details = {'threshold': metric.threshold}
            steps = getattr(metric, 'evaluation_steps', None)
            if steps:
                encoded_steps = json.dumps(steps, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
                details['evaluation_steps_sha256'] = sha256(encoded_steps).hexdigest()
            metric_metadata[name] = details

    evaluation = {'results': results, 'passed': all(result['passed'] for result in results.values())}
    if include_metadata:
        evaluation['metadata'] = _evaluation_metadata(model, metric_metadata)
    return evaluation


def _assert_evaluation(evaluation, label):
    if not evaluation['passed']:
        failed = {name: result for name, result in evaluation['results'].items() if not result['passed']}
        raise AssertionError(f'{label} DeepEval evaluation failed: {failed}')


def evaluate_response_with_deepeval(
    input_text,
    actual_output,
    metric_config=None,
    expected_output=None,
    retrieved_context=None,
    model=None,
    model_name=None,
    provider=None,
    model_kwargs=None,
    reference_context=None,
    *,
    include_metadata=False,
    **test_case_options,
):
    """Evaluate selected single-turn metrics, returning results and an aggregate passed value.

    Set ``include_metadata=True`` to include versions, judge details and metric settings.

    Additional test case fields, such as tools_called and expected_tools, are forwarded
    to LLMTestCase. Summaries use the separate source_text/summary API.

    ``retrieved_context`` supplies retrieved evidence for faithfulness and contextual
    metrics. ``reference_context`` supplies reference facts for hallucination; when
    omitted (None), it defaults to ``retrieved_context``. Both accept a single string
    or dictionary, or a list of items. Wrap a JSON array in an outer list to use it
    as a single item. ``context`` is reserved for Behave context in Toolium and
    is not accepted here. Only the internal DeepEval test case uses that field name.

    The tool_correctness metric compares only tool names by default. To also compare
    arguments and output, set ``evaluation_params`` in its ``metric_config`` options
    to ``[ToolCallParams.INPUT_PARAMETERS, ToolCallParams.OUTPUT]``. Either field can
    be selected independently; expected_tools values alone do not enable comparison.
    """
    _require_deepeval()
    if 'context' in test_case_options:
        raise TypeError(
            'context is reserved for Behave context in Toolium; use reference_context for hallucination reference facts'
        )
    if metric_config is None:
        metric_config = {'answer_relevancy': {'threshold': 0.7}}
    _validate_metric_config(metric_config, _RESPONSE_METRICS, 'response')
    judge = _resolve_model(provider, model_name, {'model': model, 'model_kwargs': model_kwargs or {}})
    serialized = _serialize_context(retrieved_context) if retrieved_context is not None else None
    test_case = LLMTestCase(
        input=input_text,
        actual_output=actual_output,
        expected_output=expected_output,
        retrieval_context=serialized,
        context=_serialize_context(reference_context) if reference_context is not None else serialized,
        **deepcopy(test_case_options),
    )
    return _evaluate_metrics(test_case, metric_config, _RESPONSE_METRICS, judge, include_metadata=include_metadata)


def assert_response_with_deepeval(*args, **kwargs):
    """Assert that all selected response metrics pass."""
    _assert_evaluation(evaluate_response_with_deepeval(*args, **kwargs), 'Response')


def evaluate_conversation_with_deepeval(
    messages,
    metric_config=None,
    model=None,
    model_name=None,
    provider=None,
    model_kwargs=None,
    **test_case_options,
):
    """Evaluate an explicit conversation, independently of Behave or pytest.

    messages is a non-empty sequence of role/content dictionaries or DeepEval Turn
    objects. Roles are user or assistant. Additional fields are passed to
    ConversationalTestCase (for example scenario and expected_outcome).
    """
    _require_deepeval()
    if metric_config is None:
        metric_config = {'turn_relevancy': {'threshold': 0.7}}
    _validate_metric_config(metric_config, _CONVERSATION_METRICS, 'conversation')
    turns = [Turn(**deepcopy(message)) if isinstance(message, dict) else deepcopy(message) for message in messages]
    if not turns or not all(isinstance(turn, Turn) for turn in turns):
        raise ValueError('messages must contain at least one user or assistant Turn')
    test_case = ConversationalTestCase(turns=turns, **deepcopy(test_case_options))
    judge = _resolve_model(provider, model_name, {'model': model, 'model_kwargs': model_kwargs or {}})
    return _evaluate_metrics(test_case, metric_config, _CONVERSATION_METRICS, judge)


def assert_conversation_with_deepeval(*args, **kwargs):
    """Assert that all selected conversational metrics pass."""
    _assert_evaluation(evaluate_conversation_with_deepeval(*args, **kwargs), 'Conversation')


class DeepEvalEvaluator:
    """Optional reusable judge and metric definitions; no per-evaluation state is retained.

    A supplied model is owned by the caller. Otherwise a model is created once at
    construction. Concurrent calls create separate cases and metrics, but sharing
    this evaluator requires the judge model itself to support concurrent use.
    """

    def __init__(
        self,
        model=None,
        metric_config=None,
        conversation_metric_config=None,
        model_name=None,
        provider=None,
        config=None,
        **model_kwargs,
    ):
        _require_deepeval()
        if model is not None and (model_name is not None or provider is not None or config is not None or model_kwargs):
            raise ValueError('model cannot be combined with model construction options')
        self._metric_config = deepcopy(
            {'answer_relevancy': {'threshold': 0.7}} if metric_config is None else metric_config
        )
        self._conversation_metric_config = deepcopy(
            {'turn_relevancy': {'threshold': 0.7}} if conversation_metric_config is None else conversation_metric_config
        )
        _validate_metric_config(self._metric_config, _RESPONSE_METRICS, 'response')
        _validate_metric_config(self._conversation_metric_config, _CONVERSATION_METRICS, 'conversation')
        self._model = (
            model
            if model is not None
            else create_deepeval_model(model_name=model_name, provider=provider, config=config, **model_kwargs)
        )

    def evaluate_response(
        self, input_text, actual_output, metric_config=None, *, include_metadata=False, **test_case_options
    ):
        """Evaluate this response using an override selection or the evaluator defaults."""
        selection = self._metric_config if metric_config is None else metric_config
        return evaluate_response_with_deepeval(
            input_text,
            actual_output,
            metric_config=selection,
            model=self._model,
            include_metadata=include_metadata,
            **test_case_options,
        )

    def evaluate_conversation(self, messages, metric_config=None, **test_case_options):
        """Evaluate this conversation using an override selection or the evaluator defaults."""
        selection = self._conversation_metric_config if metric_config is None else metric_config
        return evaluate_conversation_with_deepeval(
            messages,
            metric_config=selection,
            model=self._model,
            **test_case_options,
        )

    def evaluate_summary(self, source_text, summary, threshold=0.7, **metric_options):
        """Evaluate a summary against its source, separately from question/answer metrics."""
        result = _evaluate_summarization_with_deepeval(
            source_text,
            summary,
            threshold=threshold,
            model=self._model,
            **metric_options,
        )
        return {'results': {'summarization': asdict(result)}, 'passed': result.passed}

    def assert_response(self, *args, **kwargs):
        """Assert that all metrics selected for this response pass."""
        _assert_evaluation(self.evaluate_response(*args, **kwargs), 'Response')

    def assert_conversation(self, *args, **kwargs):
        """Assert that all metrics selected for this conversation pass."""
        _assert_evaluation(self.evaluate_conversation(*args, **kwargs), 'Conversation')

    def assert_summary(self, *args, **kwargs):
        """Assert that this summary passes."""
        _assert_evaluation(self.evaluate_summary(*args, **kwargs), 'Summary')
