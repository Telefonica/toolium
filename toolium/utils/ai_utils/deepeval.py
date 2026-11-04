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

try:
    from deepeval.metrics import (
        AnswerRelevancyMetric,
        ContextualPrecisionMetric,
        ContextualRecallMetric,
        ContextualRelevancyMetric,
        FaithfulnessMetric,
        GEval,
        HallucinationMetric,
        JsonCorrectnessMetric,
        PIILeakageMetric,
        SummarizationMetric,
        ToolCorrectnessMetric,
        ToxicityMetric,
    )
    from deepeval.test_case import LLMTestCase, SingleTurnParams, ToolCall, ToolCallParams
except ImportError:
    AnswerRelevancyMetric = ContextualPrecisionMetric = ContextualRecallMetric = ContextualRelevancyMetric = (
        FaithfulnessMetric
    ) = GEval = HallucinationMetric = JsonCorrectnessMetric = PIILeakageMetric = SummarizationMetric = (
        ToolCorrectnessMetric
    ) = ToxicityMetric = LLMTestCase = SingleTurnParams = ToolCall = ToolCallParams = None

try:
    from deepeval.models import GPTModel
except ImportError:
    GPTModel = None

try:
    from deepeval.models.llms import AzureOpenAIModel
except ImportError:
    AzureOpenAIModel = None

from toolium.driver_wrappers_pool import DriverWrappersPool

logger = logging.getLogger(__name__)


def _require_deepeval():
    if LLMTestCase is None:
        raise ImportError("DeepEval is not installed. Please run 'pip install toolium[ai]'")


def _get_model(provider, model_name, kwargs):
    config = DriverWrappersPool.get_default_wrapper().config
    provider = provider or config.get_optional('AI', 'provider', 'openai')
    model_name = model_name or config.get_optional('AI', 'openai_model', 'gpt-4o-mini')
    model_kwargs = {
        'model': model_name,
        'api_key': config.get_optional('AI', f'{provider}_api_key'),
        'temperature': config.get_optional('AI', f'{provider}_temperature', None),
    }
    if provider == 'openai':
        model_class = GPTModel
    elif provider == 'azure':
        model_class = AzureOpenAIModel
        model_kwargs.update(
            base_url=config.get_optional('AI', 'azure_endpoint'),
            deployment_name=config.get_optional('AI', 'azure_deployment', model_name),
            api_version=config.get_optional('AI', 'api_version'),
        )
    else:
        raise ValueError(f"Unknown provider: '{provider}', please use 'openai' or 'azure'")
    model_kwargs.update(kwargs)
    return model_class(**model_kwargs)
    raise ValueError(f"Unknown provider: '{provider}', please use 'openai' or 'azure'")


def _measure(metric, test_case):
    metric.measure(test_case)
    return float(metric.score), getattr(metric, 'reason', '')


_CONTEXTUAL_METRICS = {
    'faithfulness': 'FaithfulnessMetric',
    'contextual_relevancy': 'ContextualRelevancyMetric',
    'contextual_precision': 'ContextualPrecisionMetric',
    'contextual_recall': 'ContextualRecallMetric',
    'summarization': 'SummarizationMetric',
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
    unknown = set(metric_names) - set(_CONTEXTUAL_METRICS)
    if unknown:
        raise ValueError(f'Unknown contextual metric(s): {", ".join(sorted(unknown))}')
    if metric_config is not None:
        for metric_name, config in metric_config.items():
            if 'threshold' not in config:
                raise ValueError(f"Missing threshold for metric '{metric_name}'")
            if not 0 <= config['threshold'] <= 1:
                raise ValueError(f"Threshold for metric '{metric_name}' must be between 0 and 1")
        if (
            any(name in ('contextual_precision', 'contextual_recall') for name in metric_names)
            and expected_output is None
        ):
            raise ValueError('expected_output is required for contextual_precision and contextual_recall')
    model = _get_model(provider, model_name, kwargs.pop('model_kwargs', {}))
    metric_kwargs = kwargs.pop('metric_kwargs', {}) if metric_config is None else {}
    retrieved_context = _serialize_context(retrieved_context)
    test_case = LLMTestCase(
        input=input_text,
        actual_output=actual_output,
        expected_output=expected_output,
        retrieval_context=retrieved_context,
        context=retrieved_context,
    )
    results = {}
    for metric_name in metric_names:
        config = metric_config[metric_name] if metric_config is not None else {}
        metric_threshold = (
            config['threshold']
            if metric_config is not None
            else (threshold.get(metric_name, 0.7) if isinstance(threshold, dict) else threshold)
        )
        metric_options = (
            {key: value for key, value in config.items() if key != 'threshold'} if metric_config else metric_kwargs
        )
        metric = globals()[_CONTEXTUAL_METRICS[metric_name]](
            threshold=metric_threshold, model=model, **metric_options
        )
        score, reason = _measure(metric, test_case)
        results[metric_name] = {
            'score': score,
            'reason': reason,
            'passed': score >= metric_threshold,
        }
    return {'results': results, 'passed': all(result['passed'] for result in results.values())}


def assert_contextual_with_deepeval(*args, **kwargs):
    """Assert that every requested contextual metric meets its threshold.

    The assertion includes all failed metric results in the error message so callers can
    diagnose multiple failures from one evaluation.
    """
    evaluation = evaluate_contextual_with_deepeval(*args, **kwargs)
    if not evaluation['passed']:
        failed = {name: result for name, result in evaluation['results'].items() if not result['passed']}
        raise AssertionError(f'Contextual DeepEval evaluation failed: {failed}')


def get_text_similarity_with_deepeval(text, expected_text, model_name=None, threshold=0.7, provider=None, **kwargs):
    """Return an LLM-as-a-Judge semantic similarity score for two texts.

    The score is between 0 and 1. ``model_name`` and ``provider`` select the evaluator;
    additional DeepEval ``GEval`` options can be passed through ``kwargs``.
    """
    _require_deepeval()
    model = _get_model(provider, model_name, kwargs.pop('model_kwargs', {}))
    metric = GEval(
        name='Text semantic similarity',
        criteria='The actual output conveys the same meaning as the expected output.',
        evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
        threshold=threshold,
        model=model,
        **kwargs,
    )
    score, _ = _measure(metric, LLMTestCase(input='', actual_output=text, expected_output=expected_text))
    logger.info("DeepEval semantic similarity: %s between '%s' and '%s'", score, text, expected_text)
    return score


def _serialize_context(context_items):
    """Convert JSON-compatible context items to readable strings for DeepEval."""
    return [
        json.dumps(item, ensure_ascii=False, indent=2) if isinstance(item, (dict, list)) else item
        for item in context_items
    ]


def get_summarization_with_deepeval(
    input_text, actual_output, source_context, model_name=None, threshold=0.7, provider=None, **kwargs
):
    """Evaluate a summary against its source context.

    The metric checks coverage and factual consistency. ``source_context`` accepts text or
    JSON-compatible API response objects and the result is ``(score, reason)``.
    """
    _require_deepeval()
    model = _get_model(provider, model_name, kwargs.pop('model_kwargs', {}))
    metric = SummarizationMetric(threshold=threshold, model=model, **kwargs)
    score, reason = _measure(
        metric,
        LLMTestCase(input=input_text, actual_output=actual_output, context=_serialize_context(source_context)),
    )
    logger.info('DeepEval summarization: %s', score)
    return score, reason


def assert_summarization_with_deepeval(
    input_text, actual_output, retrieved_context, threshold, model_name=None, provider=None, **kwargs
):
    """Assert that a summary meets the threshold."""
    score, reason = get_summarization_with_deepeval(
        input_text, actual_output, retrieved_context, model_name, threshold, provider, **kwargs
    )
    if score < threshold:
        raise AssertionError(f'DeepEval summarization is below threshold: {score} < {threshold}\nReason: {reason}')


def get_pii_leakage_with_deepeval(
    actual_output, model_name=None, threshold=0.7, provider=None, input_text='', **kwargs
):
    """Evaluate possible personally identifiable information leakage.

    A higher score indicates more leakage. Use the dedicated assertion with a
    threshold that represents the maximum acceptable leakage.
    """
    _require_deepeval()
    model = _get_model(provider, model_name, kwargs.pop('model_kwargs', {}))
    metric = PIILeakageMetric(threshold=threshold, model=model, **kwargs)
    score, reason = _measure(metric, LLMTestCase(input=input_text, actual_output=actual_output))
    logger.info('DeepEval PII leakage: %s', score)
    return score, reason


def assert_pii_leakage_with_deepeval(actual_output, threshold, model_name=None, provider=None, input_text='', **kwargs):
    """Assert that an output stays below the PII leakage threshold."""
    score, reason = get_pii_leakage_with_deepeval(actual_output, model_name, threshold, provider, input_text, **kwargs)
    if score > threshold:
        raise AssertionError(f'DeepEval PII leakage is above threshold: {score} > {threshold}\nReason: {reason}')


def get_toxicity_with_deepeval(actual_output, model_name=None, threshold=0.7, provider=None, input_text='', **kwargs):
    """Evaluate the toxicity of an output."""
    _require_deepeval()
    model = _get_model(provider, model_name, kwargs.pop('model_kwargs', {}))
    metric = ToxicityMetric(threshold=threshold, model=model, **kwargs)
    score, reason = _measure(metric, LLMTestCase(input=input_text, actual_output=actual_output))
    logger.info('DeepEval toxicity: %s', score)
    return score, reason


def assert_toxicity_with_deepeval(actual_output, threshold, model_name=None, provider=None, input_text='', **kwargs):
    """Assert that an output stays below the toxicity threshold."""
    score, reason = get_toxicity_with_deepeval(actual_output, model_name, threshold, provider, input_text, **kwargs)
    if score > threshold:
        raise AssertionError(f'DeepEval toxicity is above threshold: {score} > {threshold}\nReason: {reason}')


def get_tool_correctness_with_deepeval(
    input_text, tools_called, expected_tools, model_name=None, threshold=0.7, provider=None, **kwargs
):
    """Evaluate whether an agent called the expected tools with correct arguments and output."""
    _require_deepeval()
    model = _get_model(provider, model_name, kwargs.pop('model_kwargs', {}))
    available_tools = kwargs.pop('available_tools', None)
    evaluation_params = kwargs.pop('evaluation_params', None)
    metric_kwargs = {'threshold': threshold, 'model': model}
    if available_tools is not None:
        metric_kwargs['available_tools'] = available_tools
    if evaluation_params is not None:
        metric_kwargs['evaluation_params'] = evaluation_params
    metric = ToolCorrectnessMetric(**metric_kwargs, **kwargs)
    score, reason = _measure(
        metric,
        LLMTestCase(
            input=input_text,
            actual_output='',
            tools_called=tools_called,
            expected_tools=expected_tools,
        ),
    )
    logger.info('DeepEval tool correctness: %s for input %s', score, input_text)
    return score, reason


def assert_tool_correctness_with_deepeval(
    input_text, tools_called, expected_tools, threshold, model_name=None, provider=None, **kwargs
):
    """Assert that an agent used the expected tools correctly."""
    score, reason = get_tool_correctness_with_deepeval(
        input_text, tools_called, expected_tools, model_name, threshold, provider, **kwargs
    )
    if score < threshold:
        raise AssertionError(f'DeepEval tool correctness is below threshold: {score} < {threshold}\nReason: {reason}')


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
    """Evaluate whether the retrieved context covers the expected answer information."""
    _require_deepeval()
    model = _get_model(provider, model_name, kwargs.pop('model_kwargs', {}))
    metric = ContextualRecallMetric(threshold=threshold, model=model, **kwargs)
    score, reason = _measure(
        metric,
        LLMTestCase(
            input=input_text,
            actual_output=actual_output,
            expected_output=expected_output,
            retrieval_context=_serialize_context(retrieved_context),
        ),
    )
    logger.info('DeepEval contextual recall: %s for input %s', score, input_text)
    return score, reason


def assert_contextual_recall_with_deepeval(
    input_text, actual_output, expected_output, retrieved_context, threshold, model_name=None, provider=None, **kwargs
):
    """Assert that the retrieved context covers the expected answer information."""
    score, reason = get_contextual_recall_with_deepeval(
        input_text, actual_output, expected_output, retrieved_context, model_name, threshold, provider, **kwargs
    )
    if score < threshold:
        raise AssertionError(f'DeepEval contextual recall is below threshold: {score} < {threshold}\nReason: {reason}')


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
    """Evaluate whether retrieved context is precise and relevant to the expected answer."""
    _require_deepeval()
    model = _get_model(provider, model_name, kwargs.pop('model_kwargs', {}))
    metric = ContextualPrecisionMetric(threshold=threshold, model=model, **kwargs)
    score, reason = _measure(
        metric,
        LLMTestCase(
            input=input_text,
            actual_output=actual_output,
            expected_output=expected_output,
            retrieval_context=_serialize_context(retrieved_context),
        ),
    )
    logger.info('DeepEval contextual precision: %s for input %s', score, input_text)
    return score, reason


def assert_contextual_precision_with_deepeval(
    input_text, actual_output, expected_output, retrieved_context, threshold, model_name=None, provider=None, **kwargs
):
    """Assert that retrieved context is precise and relevant."""
    score, reason = get_contextual_precision_with_deepeval(
        input_text, actual_output, expected_output, retrieved_context, model_name, threshold, provider, **kwargs
    )
    if score < threshold:
        raise AssertionError(f'DeepEval contextual precision is below threshold: {score} < {threshold}Reason: {reason}')


def get_contextual_relevancy_with_deepeval(
    input_text, actual_output, retrieved_context, model_name=None, threshold=0.7, provider=None, **kwargs
):
    """Evaluate whether the retrieved context is relevant to the input and answer."""
    _require_deepeval()
    model = _get_model(provider, model_name, kwargs.pop('model_kwargs', {}))
    metric = ContextualRelevancyMetric(threshold=threshold, model=model, **kwargs)
    score, reason = _measure(
        metric,
        LLMTestCase(
            input=input_text,
            actual_output=actual_output,
            retrieval_context=_serialize_context(retrieved_context),
        ),
    )
    logger.info('DeepEval contextual relevancy: %s for input %s', score, input_text)
    return score, reason


def assert_contextual_relevancy_with_deepeval(
    input_text, actual_output, retrieved_context, threshold, model_name=None, provider=None, **kwargs
):
    """Assert that the retrieved context is relevant."""
    score, reason = get_contextual_relevancy_with_deepeval(
        input_text, actual_output, retrieved_context, model_name, threshold, provider, **kwargs
    )
    if score < threshold:
        raise AssertionError(
            f'DeepEval contextual relevancy is below threshold: {score} < {threshold}\nReason: {reason}'
        )


def get_json_correctness_with_deepeval(
    actual_output, expected_schema, model_name=None, threshold=0.7, provider=None, **kwargs
):
    """Evaluate whether a JSON response matches a Pydantic schema."""
    _require_deepeval()
    model = _get_model(provider, model_name, kwargs.pop('model_kwargs', {}))
    metric = JsonCorrectnessMetric(expected_schema=expected_schema, model=model, threshold=threshold, **kwargs)
    score, reason = _measure(metric, LLMTestCase(input='', actual_output=actual_output))
    logger.info('DeepEval JSON correctness: %s', score)
    return score, reason


def assert_json_correctness_with_deepeval(
    actual_output, expected_schema, threshold, model_name=None, provider=None, **kwargs
):
    """Assert that a JSON response matches a Pydantic schema."""
    score, reason = get_json_correctness_with_deepeval(
        actual_output, expected_schema, model_name, threshold, provider, **kwargs
    )
    if score < threshold:
        raise AssertionError(f'DeepEval JSON correctness is below threshold: {score} < {threshold}\nReason: {reason}')


def get_hallucination_evaluation_with_deepeval(
    actual_output, retrieved_context, model_name=None, threshold=0.7, provider=None, input_text='', **kwargs
):
    """Evaluate whether an output contains unsupported information."""
    _require_deepeval()
    model = _get_model(provider, model_name, kwargs.pop('model_kwargs', {}))
    metric = HallucinationMetric(threshold=threshold, model=model, **kwargs)
    score, reason = _measure(
        metric,
        LLMTestCase(input=input_text, actual_output=actual_output, context=_serialize_context(retrieved_context)),
    )
    logger.info('DeepEval hallucination score: %s for output %s', score, actual_output)
    return score, reason


def assert_hallucination_evaluation_with_deepeval(
    actual_output, retrieved_context, threshold, model_name=None, provider=None, input_text='', **kwargs
):
    """Assert that an output stays below the hallucination threshold."""
    score, reason = get_hallucination_evaluation_with_deepeval(
        actual_output, retrieved_context, model_name, threshold, provider, input_text, **kwargs
    )
    if score > threshold:
        raise AssertionError(f'DeepEval hallucination is above threshold: {score} > {threshold}\nReason: {reason}')


def get_answer_relevancy_with_deepeval(
    actual_output, input_text, model_name=None, threshold=0.7, provider=None, **kwargs
):
    """Evaluate whether an answer is relevant to the input question."""
    _require_deepeval()
    model = _get_model(provider, model_name, kwargs.pop('model_kwargs', {}))
    metric = AnswerRelevancyMetric(threshold=threshold, model=model, **kwargs)
    score, reason = _measure(metric, LLMTestCase(input=input_text, actual_output=actual_output))
    logger.info('DeepEval answer relevancy: %s for input %s', score, input_text)
    return score, reason


def assert_answer_relevancy_with_deepeval(
    actual_output, input_text, threshold, model_name=None, provider=None, **kwargs
):
    """Assert that an answer is relevant to the input question."""
    score, reason = get_answer_relevancy_with_deepeval(
        actual_output, input_text, model_name, threshold, provider, **kwargs
    )
    if score < threshold:
        raise AssertionError(f'DeepEval answer relevancy is below threshold: {score} < {threshold}\nReason: {reason}')


def get_faithfulness_evaluation_with_deepeval(
    actual_output, retrieved_context, model_name=None, threshold=0.7, provider=None, input_text='', **kwargs
):
    """Evaluate whether an output is supported by text or JSON API context."""
    _require_deepeval()
    retrieved_context = _serialize_context(retrieved_context)
    model = _get_model(provider, model_name, kwargs.pop('model_kwargs', {}))
    metric = FaithfulnessMetric(threshold=threshold, model=model, **kwargs)
    score, reason = _measure(
        metric,
        LLMTestCase(input=input_text, actual_output=actual_output, retrieval_context=retrieved_context),
    )
    logger.info('DeepEval faithfulness: %s for output %s', score, actual_output)
    return score, reason


def assert_faithfulness_with_deepeval(
    actual_output, retrieved_context, threshold, model_name=None, provider=None, input_text='', **kwargs
):
    """Assert that an output is supported by the supplied context."""
    score, reason = get_faithfulness_evaluation_with_deepeval(
        actual_output, retrieved_context, model_name, threshold, provider, input_text, **kwargs
    )
    if score < threshold:
        raise AssertionError(f'DeepEval faithfulness is below threshold: {score} < {threshold}\nReason: {reason}')


def get_answer_evaluation_with_deepeval(
    llm_answer, reference_answer, model_name=None, question=None, threshold=0.7, provider=None, **kwargs
):
    """Return answer correctness score and DeepEval explanation."""
    _require_deepeval()
    model = _get_model(provider, model_name, kwargs.pop('model_kwargs', {}))
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
    score, reason = _measure(
        metric,
        LLMTestCase(input=question or '', actual_output=llm_answer, expected_output=reference_answer),
    )
    return score, reason


def get_text_criteria_analysis_with_deepeval(
    text_input, text_criteria, model_name=None, threshold=0.7, provider=None, **kwargs
):
    """Evaluate each text characteristic independently using DeepEval GEval."""
    _require_deepeval()
    model = _get_model(provider, model_name, kwargs.pop('model_kwargs', {}))
    features = []
    scores = []
    for criterion in text_criteria:
        metric = GEval(
            name='Text criterion',
            criteria=f'The text satisfies this characteristic: {criterion}',
            evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT],
            threshold=threshold,
            model=model,
            **kwargs,
        )
        score, reason = _measure(metric, LLMTestCase(actual_output=text_input))
        scores.append(score)
        if score < threshold:
            features.append({'name': criterion, 'score': score, 'explanation': reason})
    overall_match = sum(scores) / len(scores) if scores else 0.0
    return {'overall_match': overall_match, 'features': features}


def assert_text_similarity_with_deepeval(text, expected_texts, threshold, model_name=None, provider=None, **kwargs):
    """Assert that text is semantically similar to at least one expected text."""
    expected_texts = [expected_texts] if isinstance(expected_texts, str) else expected_texts
    failures = []
    for expected_text in expected_texts:
        score = get_text_similarity_with_deepeval(text, expected_text, model_name, threshold, provider, **kwargs)
        if score >= threshold:
            return
        failures.append(f'{score} < {threshold}: {expected_text}')
    raise AssertionError('DeepEval similarity is below threshold:\n' + '\n'.join(failures))


def assert_answer_evaluation_with_deepeval(
    llm_answer, reference_answers, threshold, model_name=None, question=None, **kwargs
):
    """Assert that an answer meets the threshold for at least one reference answer."""
    reference_answers = [reference_answers] if isinstance(reference_answers, str) else reference_answers
    failures = []
    for reference_answer in reference_answers:
        score, _ = get_answer_evaluation_with_deepeval(
            llm_answer, reference_answer, model_name, question, threshold, **kwargs
        )
        if score >= threshold:
            return
        failures.append(f'{score} < {threshold}: {reference_answer}')
    raise AssertionError('DeepEval answer evaluation is below threshold:\n' + '\n'.join(failures))


def assert_text_criteria_with_deepeval(text_input, text_criteria, threshold, model_name=None, **kwargs):
    """Assert that the overall criteria score meets the threshold."""
    analysis = get_text_criteria_analysis_with_deepeval(text_input, text_criteria, model_name, threshold, **kwargs)
    if analysis['overall_match'] < threshold:
        raise AssertionError(
            f'DeepEval text criteria analysis is below threshold: '
            f'{analysis["overall_match"]} < {threshold}\nFailed features: {analysis["features"]}'
        )
