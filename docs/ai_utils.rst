.. _ai_utilities:

AI Utils
========

Installation and configuration
------------------------------

Make sure to install the required libraries for the chosen method. For SpaCy, Sentence Transformers or OpenAI LLM, you
can install them with the following command:

.. code-block:: bash

    pip install toolium[ai]

**Additional Requirements:**

For SpaCy, you also need to download the language model, i.e. for small English model:

.. code-block:: bash

    python -m spacy download en_core_web_sm

For OpenAI LLM, you need to set up your configuration using environment variables or include it in the Toolium configuration.
The required parameters will vary depending on your access type (direct OpenAI or Azure OpenAI):

.. code-block:: bash

    # For example, to configure direct OpenAI access:
    OPENAI_API_KEY=<your_api_key>

.. code-block:: bash

    # For example, to configure Azure OpenAI:
    AZURE_OPENAI_API_KEY=<your_api_key>
    AZURE_OPENAI_ENDPOINT=<your_endpoint>
    OPENAI_API_VERSION=<your_api_version>

*[AI]* section::

[AI]
# If you are using Azure OpenAI
azure_api_key: your-azure-api-key
azure_endpoint: https://your-endpoint.azure.com
api_version: 2025-01-01-preview
azure_deployment: gpt-4o-mini
azure_temperature: 0.7 # Optional Temperature for OpenAI model, between 0 and 1.
# If you are using OpenAI directly
openai_api_key: your-openai-api-key
openai_temperature: 0.7 # Optional Temperature for OpenAI model, between 0 and 1.

Different AI providers can be used in the same project.

Text Similarity
---------------

Text similarity is a measure of how alike two pieces of text are in terms of meaning, structure, or content.
Toolium provides several methods to compare and validate text similarity using different AI techniques:

1. `SpaCy <https://spacy.io/>`_: Uses the SpaCy library to compute text similarity with pre-trained NLP models. Fast,
lightweight and good for general-purpose text analysis.

2. `Sentence Transformers <https://github.com/UKPLab/sentence-transformers>`_: Leverages Sentence Transformers for
semantic textual similarity using deep learning embeddings. Best balance of accuracy and performance for semantic
similarity.

3. `OpenAI <https://github.com/openai/openai-python>`_: Utilizes OpenAI's language models for advanced semantic text
comparison. Provides the most sophisticated analysis but requires API access and it may incur costs.

4. `DeepEval <https://deepeval.com/>`_: Provides additional semantic similarity and LLM-as-a-Judge metrics. It is optional and does not change the existing methods or defaults.

DeepEval can be used explicitly through `toolium.utils.ai_utils.deepeval`. Its methods are independent from the methods described above.

Usage
~~~~~

You can use the function `assert_text_similarity` from `toolium.utils.ai_utils.text_similarity` module to compare
two texts using any of these methods. You can specify the method to use with the `similarity_method` parameter and set a
threshold for similarity with the `threshold` parameter (a value between 0 and 1, where 1 means identical and 0 means
completely different).

.. code-block:: python

    from toolium.utils.ai_utils.text_similarity import assert_text_similarity

    # Basic usage
    input_text = "The quick brown fox jumps over the lazy dog"
    expected_text = "A fast brown fox leaps over a sleepy dog"  # Admits both a single expected text or a list of expected texts
    threshold = 0.8  # Similarity threshold between 0 and 1
    similarity_method = 'spacy'  # Options: 'spacy', 'sentence_transformers', 'openai', 'azure_openai'

    # Validate similarity
    assert_text_similarity(input_text, expected_text, threshold=threshold, similarity_method=similarity_method)

DeepEval alternative
~~~~~~~~~~~~~~~~~~~~

DeepEval is available as an additional implementation. It must be selected explicitly; it does not replace SpaCy,
Sentence Transformers or OpenAI, and it does not change the default similarity method.

.. code-block:: python

    from toolium.utils.ai_utils.deepeval import (
        assert_text_similarity_with_deepeval,
        get_text_similarity_with_deepeval,
    )

    similarity = get_text_similarity_with_deepeval(
        text="The quick brown fox jumps over the lazy dog",
        expected_text="A fast brown fox leaps over a sleepy dog",
        model_name="gpt-4o-mini",  # optional DeepEval evaluation model
        threshold=0.8,
    )

    assert_text_similarity_with_deepeval(
        text="The quick brown fox jumps over the lazy dog",
        expected_texts=["A fast brown fox leaps over a sleepy dog"],
        threshold=0.8,
    )

`get_text_similarity_with_deepeval()` returns a score between 0 and 1. The assertion succeeds when at least one
expected text reaches the threshold. DeepEval must be installed with `pip install toolium[ai]`.

When to use DeepEval
~~~~~~~~~~~~~~~~~~~~

DeepEval can provide better results when similarity depends on meaning, context and correctness instead of only shared
words or vector distance. It is particularly useful for evaluating generated answers, paraphrases and responses where
an explanation of the score is valuable.

For example, these texts express approximately the same idea even though they use different words:

.. code-block:: python

    received = "The payment was accepted and the order is being prepared."
    expected = "Your purchase went through successfully and is now in preparation."

    score = get_text_similarity_with_deepeval(
        text=received,
        expected_text=expected,
        provider="azure",
        threshold=0.6,
    )

A lexical comparison can score this pair lower because several words differ. A DeepEval `GEval` metric can consider the
shared meaning and the relationship between both outputs. The score should still be calibrated with representative
examples; DeepEval scores are not directly equivalent to SpaCy, Sentence Transformers or OpenAI scores.

DeepEval is also useful when the answer must be judged against a question and a reference answer:

.. code-block:: python

    score, reason = get_answer_evaluation_with_deepeval(
        llm_answer="The refund will be issued to the original payment method within five business days.",
        reference_answer="Refunds are returned to the original payment method within five business days.",
        question="How and when will the customer receive the refund?",
        provider="azure",
        threshold=0.6,
    )

    print(score)
    print(reason)

In this case, `GEval` can take into account semantic equivalence, factual accuracy, completeness and relevance to the
question. A plain similarity comparison does not necessarily verify all these aspects.

Comparison with the existing methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **SpaCy** is local and fast. It is useful for low-latency comparisons, but results depend on the selected word-vector
  model and may be weaker for paraphrases, domain-specific language or factual correctness.
* **Sentence Transformers** compares embeddings and is usually a good choice for scalable semantic similarity. It does
  not normally provide an explanation and does not independently check whether an answer is factually correct.
* **OpenAI methods in `text_similarity.py` and `evaluate_answer.py`** use a custom prompt and return an LLM-based
  evaluation. They remain available when their existing prompt and response contract are preferred.
* **DeepEval** provides evaluation metrics such as `GEval`, explicit criteria and a reason for the score. It is useful
  when the evaluation needs context, multiple criteria or an LLM-as-a-Judge workflow, but it requires model access and
  can be slower and more expensive than local embedding-based methods.

The scores from these methods must not be compared using the same threshold automatically. A threshold such as `0.6` in
DeepEval may represent an acceptable result that would receive a different score with SpaCy or Sentence Transformers.
Thresholds should be calibrated independently with representative positive, borderline and negative examples.

DeepEval compared with the existing OpenAI methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Both approaches use an OpenAI or Azure OpenAI model as an evaluator, but they expose different levels of abstraction:

* The existing methods call the provider client directly through `openai_request()` and send Toolium-owned prompts.
  The prompt, JSON response format and parsing logic are controlled by Toolium.
* DeepEval creates an evaluation metric such as `GEval`, builds an `LLMTestCase` and delegates the evaluation workflow to
  DeepEval. DeepEval generates the evaluation steps, invokes the configured model and exposes the score and reason using
  its metric API.
* `get_text_similarity_with_openai()` is a focused comparison of two texts. Its prompt asks whether the answer is
  semantically similar to the expected text and returns the similarity value.
* `get_answer_evaluation_with_openai()` includes more explicit criteria such as semantic similarity, factual accuracy,
  completeness and relevance, and can return a structured Pydantic response.
* `get_text_similarity_with_deepeval()` uses `GEval` with actual and expected output parameters. Its criteria are defined
  as a metric and the result includes DeepEval's reason.
* `get_answer_evaluation_with_deepeval()` uses `GEval` with the question, actual output and expected output, making the
  evaluation criteria explicit and reusable independently from the provider request code.

The existing OpenAI methods can be preferable when exact compatibility with the current Toolium prompt, JSON contract,
Pydantic response format, token usage handling or OpenAI client options is required. DeepEval can be preferable when the
evaluation should be expressed as reusable criteria, when the reason generated by the metric is useful, or when several
DeepEval metrics and test cases will be used consistently in a larger evaluation suite.

DeepEval does not automatically produce more accurate results. Both approaches depend on the selected model, prompt or
criteria, temperature and threshold. They may return different scores for the same pair of texts because they use
different instructions and evaluation workflows, even when they use the same OpenAI model. Consequently, thresholds from
`text_similarity.py` or `evaluate_answer.py` should not be copied to DeepEval without calibration.

Examples of different evaluation behavior
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Example 1: paraphrases with different wording**

The existing OpenAI similarity method uses a general-purpose prompt:

.. code-block:: python

    from toolium.utils.ai_utils.text_similarity import get_text_similarity_with_openai
    from toolium.utils.ai_utils.deepeval import get_text_similarity_with_deepeval

    received = "The payment was accepted and the order is being prepared."
    expected = "Your purchase went through successfully and is now in preparation."

    openai_score = get_text_similarity_with_openai(
        received,
        expected,
        model_name="gpt-4o-mini",
        azure=True,
    )
    deepeval_score = get_text_similarity_with_deepeval(
        received,
        expected,
        model_name="gpt-4o-mini",
        provider="azure",
    )

Both methods use an LLM, but they send different instructions. DeepEval evaluates the pair through `GEval` and its
metric criteria, while the existing method uses Toolium's fixed prompt and JSON response. The scores can therefore be
different even when both calls use the same deployment.

**Example 2: correctness against a question**

For an answer that must address a question, `get_answer_evaluation_with_deepeval()` makes the input, expected answer and
actual answer explicit:

.. code-block:: python

    from toolium.utils.ai_utils.evaluate_answer import get_answer_evaluation_with_openai
    from toolium.utils.ai_utils.deepeval import get_answer_evaluation_with_deepeval

    question = "What is the refund period and where is the money returned?"
    expected = "The refund is returned to the original payment method within five business days."
    received = "The refund will arrive within five days."

    openai_score, _ = get_answer_evaluation_with_openai(
        received,
        expected,
        model_name="gpt-4o-mini",
        azure=True,
        question=question,
    )
    deepeval_score, reason = get_answer_evaluation_with_deepeval(
        llm_answer=received,
        reference_answer=expected,
        question=question,
        model_name="gpt-4o-mini",
        provider="azure",
    )

Here the answer mentions the time but omits the original payment method. Both evaluators may penalize the omission, but
there is no guarantee that they assign the same score. The DeepEval `reason` can make the missing information explicit,
while the existing method is preferable when a stable Pydantic response schema or the current Toolium prompt contract is
required.

**Example 3: custom criteria**

DeepEval is useful when the evaluation criteria need to be stated directly:

.. code-block:: python

    score, reason = get_answer_evaluation_with_deepeval(
        llm_answer="The system is fine.",
        reference_answer="The service recovered after a short outage.",
        question="Summarize the incident status.",
        provider="azure",
        criteria=(
            "The answer must mention that there was an outage and that the service recovered. "
            "Penalize vague answers that do not describe both facts."
        ),
    )

The existing `get_answer_evaluation_with_openai()` method has a predefined evaluation prompt and supports additional
structured fields through Pydantic. DeepEval is more convenient when criteria are passed as part of the metric, whereas
the existing method provides more control over the response schema.

Contextual evaluation with one or more metrics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`evaluate_contextual_with_deepeval()` evaluates a response against contextual data using one or more metrics in the
same call. Context can be plain text or JSON objects returned by an API. Each metric produces its own score and reason,
and the combined `passed` value is `True` only when all configured metrics pass.

.. code-block:: python

    from toolium.utils.ai_utils.deepeval import evaluate_contextual_with_deepeval

    result = evaluate_contextual_with_deepeval(
        input_text="What is the status and total of order 12345?",
        actual_output="The order is being prepared and costs 49.99 EUR.",
        expected_output="Order 12345 is preparing and costs 49.99 EUR.",
        context=[
            {
                "order_id": "12345",
                "status": "preparing",
                "total": 49.99,
                "currency": "EUR",
            }
        ],
        metrics=["faithfulness", "contextual_relevancy"],
        provider="azure",
        threshold=0.7,
    )

    print(result["results"])
    print(result["passed"])

A single metric can be selected with a string:

.. code-block:: python

    result = evaluate_contextual_with_deepeval(
        input_text="What is the order status?",
        actual_output="The order is being prepared.",
        context=[{"status": "preparing"}],
        metrics="faithfulness",
        provider="azure",
        threshold=0.7,
    )

Different thresholds can be configured for each metric with a dictionary:

.. code-block:: python

    result = evaluate_contextual_with_deepeval(
        input_text="What is the status and total?",
        actual_output=answer,
        expected_output=expected_answer,
        context=[api_response],
        metrics=["faithfulness", "contextual_precision", "contextual_recall"],
        threshold={
            "faithfulness": 0.7,
            "contextual_precision": 0.8,
            "contextual_recall": 0.8,
        },
        provider="azure",
    )

For step definitions and other dynamic callers, `metric_config` groups each metric with its threshold and optional
metric-specific parameters. When `metric_config` is used, the metric names are obtained from its keys; do not combine it
with `metrics`, `threshold` or `metric_kwargs`.

.. code-block:: python

    result = evaluate_contextual_with_deepeval(
        input_text="Summarize the order update.",
        actual_output="The order is ready for pickup.",
        context=[{"status": "ready", "delivery": "pickup"}],
        metric_config={
            "faithfulness": {"threshold": 0.7},
            "contextual_relevancy": {"threshold": 0.8},
            "summarization": {"threshold": 0.75, "n": 3},
        },
        provider="azure",
    )

Every `metric_config` entry requires a threshold between `0` and `1`. `contextual_precision` and `contextual_recall`
also require `expected_output`.

Use `assert_contextual_with_deepeval()` when the test should fail if one or more metrics do not pass:

.. code-block:: python

    from toolium.utils.ai_utils.deepeval import assert_contextual_with_deepeval

    assert_contextual_with_deepeval(
        input_text=question,
        actual_output=answer,
        expected_output=expected_answer,
        context=context,
        metric_config={
            "faithfulness": {"threshold": 0.7},
            "contextual_relevancy": {"threshold": 0.8},
        },
        provider="azure",
    )

Contextual metrics
~~~~~~~~~~~~~~~~~~

The contextual metrics currently supported by the combined evaluation are:

* **faithfulness**: checks whether the claims in the answer are supported by the supplied context. A high score is better.
* **contextual_relevancy**: checks whether the retrieved context is relevant to the input and answer. A high score is better.
* **contextual_precision**: checks whether the relevant context is ranked or selected precisely for the expected answer. It requires `expected_output`. A high score is better.
* **contextual_recall**: checks whether the context contains the information needed to cover the expected answer. It requires `expected_output`. A high score is better.
* **summarization**: checks whether the output is a complete and factually consistent summary of the supplied context. A high score is better.

All these contextual metrics use the normal rule `score >= threshold`. This differs from safety-oriented metrics such as
`toxicity`, `PII leakage` and `hallucination`, where a lower score is better and which are evaluated with their dedicated
methods. Thresholds should be calibrated independently for each metric and model; scores from different metrics or
providers should not be assumed to be directly equivalent.

Metric options
~~~~~~~~~~~~~~

`metric_config` accepts `threshold` plus the options supported by the corresponding DeepEval metric. The shared options
are:

* `include_reason`: includes the explanation in the result when `True` (default `True`).
* `async_mode`: enables DeepEval's asynchronous evaluation mode (default `True`). Set it to `False` when the calling
  environment requires synchronous execution.
* `strict_mode`: enables stricter pass/fail behavior (default `False`).
* `verbose_mode`: enables additional DeepEval diagnostic output (default `False`).
* `evaluation_template`: custom DeepEval evaluation template, for advanced integrations.

The `model` option is managed by Toolium and should not be placed inside `metric_config`. Use `provider`, `model_name` and
`model_kwargs` at the top level instead.

Supported options by metric
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**`faithfulness`**

In addition to the shared options, it supports:

* `truths_extraction_limit`: limits the number of extracted claims to evaluate.
* `penalize_ambiguous_claims`: penalizes claims that are ambiguous instead of treating them as acceptable.

Example:

.. code-block:: python

    metric_config={
        "faithfulness": {
            "threshold": 0.7,
            "include_reason": True,
            "truths_extraction_limit": 10,
            "penalize_ambiguous_claims": True,
        }
    }

**`contextual_relevancy`**

It supports the shared options. It evaluates whether the retrieved context is relevant to the input and generated answer.

.. code-block:: python

    metric_config={
        "contextual_relevancy": {
            "threshold": 0.8,
            "include_reason": True,
            "strict_mode": False,
        }
    }

**`contextual_precision`**

It supports the shared options and requires `expected_output` in the call to
`evaluate_contextual_with_deepeval()`. It evaluates whether relevant context is selected or ranked precisely.

.. code-block:: python

    metric_config={
        "contextual_precision": {
            "threshold": 0.8,
            "include_reason": True,
        }
    }

**`contextual_recall`**

It supports the shared options and requires `expected_output`. It evaluates whether the context contains the information
needed to cover the expected answer.

.. code-block:: python

    metric_config={
        "contextual_recall": {
            "threshold": 0.8,
            "include_reason": True,
        }
    }

**`summarization`**

In addition to the shared options, it supports:

* `n`: number of assessment questions used to evaluate the summary (default `5`). Higher values can increase coverage,
  latency and token usage.
* `assessment_questions`: explicit questions to use instead of relying only on automatically generated assessments.
* `truths_extraction_limit`: limits the number of extracted truths used in the evaluation.

Example:

.. code-block:: python

    metric_config={
        "summarization": {
            "threshold": 0.75,
            "n": 5,
            "assessment_questions": [
                "Does the summary include the order status?",
                "Does it preserve the total amount?",
            ],
            "truths_extraction_limit": 10,
        }
    }

The `threshold` option is required for every `metric_config` entry and must be between `0` and `1`. Options not listed
for a metric should not be added to that metric's configuration; DeepEval may reject unsupported arguments. All contextual
metrics use the rule `score >= threshold`, so a higher score represents a better contextual evaluation.

API responses as JSON context
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the facts come from an API, JSON objects and arrays can be passed as context. The DeepEval implementation serializes
each dictionary or list to a JSON string before sending it as `retrieval_context`:

.. code-block:: python

    from toolium.utils.ai_utils.deepeval import get_faithfulness_evaluation_with_deepeval

    api_response = {
        "order_id": "12345",
        "status": "preparing",
        "total": 49.99,
        "currency": "EUR",
    }

    score, reason = get_faithfulness_evaluation_with_deepeval(
        actual_output="The order is being prepared and costs 49.99 EUR.",
        context=[api_response],
        input_text="What is the status and total of order 12345?",
        provider="azure",
        threshold=0.6,
    )

For several API responses, pass one JSON object per context item:

.. code-block:: python

    context = [order_response, customer_response, shipping_response]

    assert_faithfulness_with_deepeval(
        actual_output=answer,
        context=context,
        input_text=question,
        provider="azure",
        threshold=0.6,
    )

Text context remains supported as well:

.. code-block:: python

    context = ["The order is in preparation.", "The total is 49.99 EUR."]

JSON is serialized with `ensure_ascii=False` and indentation for readability. For critical fields such as identifiers,
amounts, dates and statuses, combine faithfulness evaluation with deterministic assertions because an LLM metric should
not be the only validation for exact API values.

Configuration
~~~~~~~~~~~~~

Default similarity method can be set in the properties.cfg file with the property *text_similarity_method* in
*[AI]* section::

    [AI]
    text_similarity_method: openai  # Options: 'spacy' (default), 'sentence_transformers', 'openai', 'azure_openai'
    spacy_model: en_core_web_lg  # SpaCy model to use, en_core_web_sm by default
    sentence_transformers_model: all-MiniLM-L6-v2  # Sentence Transformers model to use, all-mpnet-base-v2 by default
    openai_model: gpt-3.5-turbo  # OpenAI model to use, gpt-4o-mini by default
    provider: openai  # AI provider: 'openai' (default) or 'azure'
    azure_deployment: gpt-4o-mini  # Azure deployment used by DeepEval

DeepEval uses the same provider and model configuration as the other LLM utilities:

* `provider`: `openai` (default) or `azure`. An explicit `provider` argument takes precedence.
* `openai_model`: model name used by DeepEval when `model_name` is not specified.
* `openai_api_key` and `openai_temperature`: OpenAI credentials and temperature.
* `azure_api_key`, `azure_endpoint`, `api_version` and `azure_deployment`: Azure OpenAI credentials and deployment settings.
* `azure_temperature`: Azure OpenAI temperature.

DeepEval functions also accept `model_name`. It takes precedence over `openai_model`. Provider-specific DeepEval model
options can be passed through `model_kwargs`:

.. code-block:: python

    from toolium.utils.ai_utils.deepeval import get_text_similarity_with_deepeval

    score = get_text_similarity_with_deepeval(
        text="The received answer",
        expected_text="The expected answer",
        provider="azure",              # optional; uses [AI].provider by default
        model_name="my-deployment",     # optional; uses [AI].openai_model by default
        model_kwargs={"temperature": 0.1},
    )

For Azure OpenAI, `azure_deployment` identifies the deployment and `azure_endpoint` is used as the model base URL.
The `deepeval` module creates the corresponding DeepEval `GPTModel` or `AzureOpenAIModel` and passes the configured
credentials to it. DeepEval must be installed with `pip install toolium[ai]`.

To select models for each method, you can refer to the following links:

* `SpaCy models <https://spacy.io/models>`_
* `Sentence Transformers models <https://github.com/UKPLab/sentence-transformers>`_
* `OpenAI models <https://platform.openai.com/docs/models>`_

Text Criteria Analysis
----------------------

Text criteria analysis evaluates how well an input text matches a set of target characteristics
(e.g., tone, style, clarity, domain vocabulary, specific described content, etc) using an LLM.
Toolium provides utilities to both retrieve a structured analysis and assert quality thresholds.

Usage
~~~~~

You can use functions from the `toolium.utils.ai_utils.text_analysis` module:

* **get_text_criteria_analysis()**: returns a JSON string with an overall score and low-scored criteria.
* **assert_text_criteria()**: validates that the overall score is above a threshold and raises `AssertionError` otherwise.

.. code-block:: python

    from toolium.utils.ai_utils.text_analysis import get_text_criteria_analysis, assert_text_criteria
    import json

    input_text = "Hey team! Quick heads-up: deployment is done, all checks green."
    text_criteria = [
        "professional tone",
        "clear and concise message",
        "it includes the status of the deployment"
    ]

    # Get analysis (JSON string)
    raw_analysis = get_text_criteria_analysis(
        text_input=input_text,
        text_criteria=text_criteria,
        model_name="gpt-4o-mini",  # optional
        azure=False                 # True for Azure OpenAI
    )

    analysis = json.loads(raw_analysis)
    print(analysis["overall_match"])
    print(analysis["features"])  # Only low-scored features (<= 0.2)

.. code-block:: python

    from toolium.utils.ai_utils.text_analysis import assert_text_criteria

    # Assert text quality against a minimum score
    assert_text_criteria(
        text_input="This message should be short, formal and informative.",
        text_criteria=["formal tone", "brevity", "informative content"],
        threshold=0.75,
        model_name="gpt-4o-mini",  # optional
        azure=False                 # set True for Azure OpenAI
    )


Configuration
~~~~~~~~~~~~~

Default text analysis method can be set in the properties.cfg file with the property *text_analysis_method* in
*[AI]* section::

    [AI]
    text_analysis_method: openai  # Options: 'openai', 'azure_openai' (default: azure_openai)

Response Format
~~~~~~~~~~~~~~~

`get_text_criteria_analysis()` expects the LLM to return a JSON object with:

.. code-block:: json

    {
      "overall_match": 0.82,
      "features": [
        {
          "name": "formal tone",
          "score": 0.15
        }
      ]
    }

Where:

- `overall_match`: float in `[0.0, 1.0]`
- `features`: list containing only low-scored criteria (score `<= 0.2`)

Assertion Behavior
~~~~~~~~~~~~~~~~~~

`assert_text_criteria()`:

- parses the JSON response returned by `get_text_criteria_analysis()`
- compares `overall_match` with the provided `threshold`
- raises `AssertionError` if `overall_match < threshold`
- logs low-scored features to help diagnose why validation failed


Text Readability
----------------

Text readability is a measure of how user-friendly and comprehensible a piece of text is.
Toolium currently provides a single method to assess text readability, using the `SpaCy <https://spacy.io/>`_ library.

Usage
~~~~~

You can use the function `assert_text_readability` from `toolium.utils.ai_utils.text_readability` module to assess
the readability of a text. You can set the `readability_method` (currently only `spacy`), the `threshold`
(a value between 0 and 1, where 1 means the text is very readable and 0 means it is not readable at all) and
optionally the `technical_characters`, a list of characters to be considered as non-linguistic content,
if you need to overide the ones set by default.

.. code-block:: python

    from toolium.utils.ai_utils.text_readability import assert_text_readability
    # Basic usage
    input_text = "This is a readable text with proper structure and vocabulary."
    threshold = 0.8  # Readability threshold between 0 and 1
    technical_characters = ['$', '%', '&']  # Optional: list of characters considered non-linguistic content
    readability_method = 'spacy'  # Only 'spacy' is currently supported

    # Validate readability
    assert_text_readability(input_text, threshold=threshold, technical_characters=technical_characters, readability_method=readability_method)

Configuration
~~~~~~~~~~~~~

Default readability method and spacy model can be set in the *[AI]* section of the properties.cfg file::

    [AI]
    text_readability_method: spacy  # Only 'spacy' is currently supported
    spacy_model: en_core_web_md  # SpaCy model to use, en_core_web_md by default

For more information on SpaCy models, you can refer to the following link:

* `SpaCy models <https://spacy.io/models>`_

Answer Evaluation using LLM-as-a-Judge
--------------------------------------

Answer evaluation using LLM-as-a-Judge is a technique to assess the quality and correctness of an LLM-generated answer
by comparing it against a reference answer using another LLM. This approach provides context-aware evaluation considering
semantic similarity, factual accuracy, completeness, and relevance.

Toolium provides methods to evaluate answers using OpenAI and Azure OpenAI models with optional structured output
using Pydantic models. DeepEval provides an additional, independent implementation based on its evaluation metrics.

Usage
~~~~~

You can use the functions from the `toolium.utils.ai_utils.evaluate_answer` module to evaluate LLM answers:

**Basic evaluation without structured response:**

.. code-block:: python

    from toolium.utils.ai_utils.evaluate_answer import get_answer_evaluation_with_azure_openai

    llm_answer = "Paris is the capital of France and has a population of over 2 million people."
    reference_answer = "The capital of France is Paris."
    question = "What is the capital of France?"

    similarity, response = get_answer_evaluation_with_azure_openai(
        llm_answer=llm_answer,
        reference_answer=reference_answer,
        question=question,
        model_name='gpt-4o'
    )

    print(f"Similarity score: {similarity}")
    print(f"Explanation: {response['explanation']}")

**Evaluation with structured Pydantic response:**

.. code-block:: python

    from pydantic import BaseModel, Field
    from toolium.utils.ai_utils.evaluate_answer import get_answer_evaluation_with_azure_openai

    class SimilarityEvaluation(BaseModel):
        """Model for text similarity evaluation response"""
        similarity: float = Field(description='Similarity score between 0.0 and 1.0', ge=0.0, le=1.0)
        explanation: str = Field(description='Brief justification for the similarity score')

    llm_answer = "Paris is the capital of France and has a population of over 2 million people."
    reference_answer = "The capital of France is Paris."
    question = "What is the capital of France?"

    similarity, response = get_answer_evaluation_with_azure_openai(
        llm_answer=llm_answer,
        reference_answer=reference_answer,
        question=question,
        model_name='gpt-4o',
        response_format=SimilarityEvaluation
    )

    print(f"Similarity score: {similarity}")
    print(f"Explanation: {response.explanation}")

**Advanced evaluation with custom evaluation criteria:**

.. code-block:: python

    from pydantic import BaseModel, Field
    from toolium.utils.ai_utils.evaluate_answer import get_answer_evaluation_with_azure_openai

    class AnswerEvaluation(BaseModel):
        """Comprehensive evaluation model"""
        similarity: float = Field(description='Similarity score between 0.0 and 1.0', ge=0.0, le=1.0)
        explanation: str = Field(description='Detailed evaluation feedback')
        accuracy: float = Field(description='Factual correctness score 1-5')
        completeness: float = Field(description='Information completeness score 1-5')
        relevance: float = Field(description='Relevance to question score 1-5')

    similarity, response = get_answer_evaluation_with_azure_openai(
        llm_answer=llm_answer,
        reference_answer=reference_answer,
        question=question,
        model_name='gpt-4o',
        response_format=AnswerEvaluation
    )

    print(f"Similarity: {similarity}")
    print(f"Accuracy: {response.accuracy}/5")
    print(f"Completeness: {response.completeness}/5")
    print(f"Relevance: {response.relevance}/5")

**Assertion with threshold validation:**

.. code-block:: python

    from toolium.utils.ai_utils.evaluate_answer import assert_answer_evaluation

    # Validate that LLM answer meets minimum similarity threshold
    assert_answer_evaluation(
        llm_answer="Paris is both the capital and the most populous city in France.",
        reference_answers="The capital and largest city of France is Paris.",
        question="What is the capital of France and its largest city?",
        threshold=0.7,  # Minimum similarity score (0.0 to 1.0)
        provider='azure',
        model_name='gpt-4o'
    )

Evaluation Methods
~~~~~~~~~~~~~~~~~~

The module provides the following evaluation methods:

* **assert_answer_evaluation()**: Evaluates answer and asserts if similarity meets threshold
* **get_answer_evaluation_with_openai()**: Uses OpenAI's API directly for evaluation
* **get_answer_evaluation_with_azure_openai()**: Uses Azure OpenAI's API for evaluation

DeepEval alternative
~~~~~~~~~~~~~~~~~~~~

The following functions provide the same type of answer and criteria validations using DeepEval, without changing the
existing OpenAI-based functions:

* **get_answer_evaluation_with_deepeval()**: evaluates an answer against a reference answer and returns `(score, reason)`.
* **assert_answer_evaluation_with_deepeval()**: accepts one or more reference answers and succeeds when any score reaches the threshold.
* **get_text_criteria_analysis_with_deepeval()**: evaluates each criterion independently and returns `overall_match` and failed features.
* **assert_text_criteria_with_deepeval()**: asserts that the overall criteria score reaches the threshold.

.. code-block:: python

    from toolium.utils.ai_utils.deepeval import (
        get_answer_evaluation_with_deepeval,
        assert_answer_evaluation_with_deepeval,
        get_text_criteria_analysis_with_deepeval,
        assert_text_criteria_with_deepeval,
    )

    score, reason = get_answer_evaluation_with_deepeval(
        llm_answer="Paris is the capital of France.",
        reference_answer="The capital of France is Paris.",
        question="What is the capital of France?",
        model_name="gpt-4o-mini",  # optional
        threshold=0.7,
    )

    assert_answer_evaluation_with_deepeval(
        llm_answer="Paris is the capital of France.",
        reference_answers=["The capital of France is Paris."],
        question="What is the capital of France?",
        threshold=0.7,
    )

    analysis = get_text_criteria_analysis_with_deepeval(
        text_input="The deployment is complete and all checks passed.",
        text_criteria=["clear message", "deployment status is included"],
        threshold=0.7,
    )

    assert_text_criteria_with_deepeval(
        text_input="The deployment is complete and all checks passed.",
        text_criteria=["clear message", "deployment status is included"],
        threshold=0.7,
    )

`get_text_criteria_analysis_with_deepeval()` returns a dictionary with `overall_match` and a `features` list containing
criteria whose score is below the threshold. These functions require DeepEval and can incur model usage costs.

Evaluation Criteria
~~~~~~~~~~~~~~~~~~~

When evaluating answers, the LLM considers the following criteria:

- **Semantic similarity**: Does the LLM answer convey the same meaning as the reference answer, even if phrased differently?
- **Factual accuracy**: How factually correct is it compared to the reference answer?
- **Completeness**: How thoroughly does it address all aspects of the question, covering all information from the reference answer?
- **Relevance**: How well does it directly answer the specific question asked?

Scoring Guide
~~~~~~~~~~~~~

- **1.0**: Perfect semantic match - answer is equivalent to reference answer
- **0.7-0.9**: Similar meaning - minor differences that don't affect overall correctness
- **0.4-0.6**: Incomplete or partially similar - major differences or missing information
- **0.0-0.3**: Different, irrelevant or contradictory - does not match the reference answer

Configuration
~~~~~~~~~~~~~

Default OpenAI model can be set in the properties.cfg file in the *[AI]* section::

    [AI]
    provider: azure  # AI provider to use, openai by default

.. _accuracy_tags_for_behave_scenarios:

Accuracy tags for Behave scenarios
----------------------------------

@accuracy
~~~~~~~~~

You can use accuracy tags in your Behave scenarios to specify the desired accuracy level and number of executions for
scenarios that involve AI-generated content. The accuracy tag follows the format `@accuracy_<percent>_<executions>`,
where `<percent>` is the desired accuracy percentage (0-100) and `<executions>` is the number of executions to achieve
that accuracy. For example, `@accuracy_80_10` indicates that the scenario must be executed 10 times and it should
achieve at least 80% accuracy.

.. code-block:: bash

    @accuracy_80_10
    Scenario: Validate AI-generated response accuracy
      Given the AI model generates a response
       When the user sends a message
       Then the AI response should be accurate

When a scenario is tagged with an accuracy tag, Toolium will automatically execute the scenario multiple times. If the
scenario does not meet the specified accuracy after the given number of executions, it will be marked as failed.

Other examples of accuracy tags:
- `@accuracy_percent_85_executions_10`: 85% accuracy, 10 executions
- `@accuracy_percent_75`: 75% accuracy, default 10 executions
- `@accuracy_90_5`: 90% accuracy, 5 executions
- `@accuracy_80`: 80% accuracy, default 10 executions
- `@accuracy`: default 90% accuracy, 10 executions

A csv report with the results of each execution will be generated in the `accuracy` folder inside the output folder.

@accuracy_data
~~~~~~~~~~~~~~

You can also use accuracy data tags in your Behave scenarios to specify different sets of accuracy data for each
execution. The accuracy data tag follows the format `@accuracy_data_<suffix>`, where `<suffix>` is a custom suffix to
identify the accuracy data set. For example, `@accuracy_data_greetings` indicates that the scenario should use the
accuracy data set with the suffix "greetings".

.. code-block:: bash

    @accuracy_80
    @accuracy_data_greetings
    Scenario: Validate AI-generated greeting responses
      Given the AI model generates a greeting response
       When the user sends "[CONTEXT:accuracy_execution_data.question]" message
       Then the AI greeting response should be similar to "[CONTEXT:accuracy_execution_data.answer]"

When a scenario is tagged with an accuracy data tag, Toolium will automatically use the specified accuracy data set for
each execution. This allows you to test different scenarios with varying data inputs. Accuracy data should be stored
previously in the context storage under the key `accuracy_data_<suffix>`, where `<suffix>` matches the one used in the
tag. For example, for the tag `@accuracy_data_greetings`, the accuracy data should be stored under the key
`accuracy_data_greetings`. The accuracy data should be a list of dictionaries, where each dictionary contains the data
for a specific execution.

For example, to store accuracy data for greetings, you can do the following in a step definition:

.. code-block:: python

    accuracy_data_greetings = [
        {"question": "Hello", "answer": "Hi, how can I help you?"},
        {"question": "Good morning", "answer": "Good morning! What can I do for you today?"},
        {"question": "Hey there", "answer": "Hey! How can I assist you?"}
    ]
    context.storage["accuracy_data_greetings"] = accuracy_data_greetings

This way, during each execution of the scenario, Toolium will use the corresponding data from the accuracy data set
based on the execution index.

after_accuracy_scenario method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can monkey-patch the `after_accuracy_scenario` method in `toolium.utils.ai_utils.accuracy` module to implement
custom behavior after accuracy scenario execution, like calling Allure `after_scenario` method.

.. code-block:: python

    from toolium.utils.ai_utils import accuracy

    def custom_after_accuracy_scenario(context, scenario):
        context.allure.after_scenario(context, scenario)

    # Monkey-patch the hook
    accuracy.after_accuracy_scenario = custom_after_accuracy_scenario


AI agents for testing
---------------------

Toolium provides utilities to create and execute AI agents in your tests using langgraph library, allowing you to
simulate complex user interactions or validate AI-generated responses.

You can create an AI agent using the `create_react_agent` function from the `toolium.utils.ai_utils.ai_agent` module.
This function allows you to create a ReAct agent, which is a type of AI agent that can reason and act based on the
conversation history and tool interactions. You must specify the system message with AI testing agent instructions
and the tool method, that the agent can use to send requests to the system under test and receive responses.

.. image:: react_agent.png
   :alt: ReAct Agent Flow Diagram

Once you have created an AI agent, you can execute it using the `execute_agent` function from the same module. This
function will run the agent and log all conversation messages and tool calls, providing insights into the agent's
behavior and the interactions it had during execution.
You can also provide previous messages to the agent to give it context for its reasoning and actions.

.. code-block:: python

    from toolium.utils.ai_utils.ai_agent import create_react_agent, execute_agent

    # Create a ReAct agent with a system message and a tool method
    system_message = "You are an assistant that helps users find TV content based on their preferences."
    tool_method = tv_recommendations  # This should be a function that the agent can call as a tool
    provider = 'azure'  # Specify the AI provider to use, e.g., 'azure' or 'openai'
    model_name = 'gpt-4o-mini'  # Specify the model to use for the agent

    agent = create_react_agent(system_message, tool_method=tool_method, provider=provider, model_name=model_name)

    # Execute the agent and log all interactions
    final_state = execute_agent(agent)

Default provider and model can be set in the properties.cfg file in *[AI]* section::

    [AI]
    provider: azure  # AI provider to use, openai by default
    openai_model: gpt-3.5-turbo  # OpenAI model to use, gpt-4o-mini by default



