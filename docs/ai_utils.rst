AI Utils
========

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
    model_name = 'en_core_web_md'  # Model name to use for the selected method
    **kwargs = {}  # Additional parameters for the selected method.

    # Validate similarity
    assert_text_similarity(input_text, expected_text, threshold=threshold, similarity_method=similarity_method)

Configuration
~~~~~~~~~~~~~

Default similarity method can be set in the properties.cfg file with the property *text_similarity_method* in
*[AI]* section::

    [AI]
    text_similarity_method: openai  # Options: 'spacy' (default), 'sentence_transformers', 'openai', 'azure_openai'
    spacy_model: en_core_web_lg  # SpaCy model to use, en_core_web_sm by default
    sentence_transformers_model: all-MiniLM-L6-v2  # Sentence Transformers model to use, all-mpnet-base-v2 by default
    openai_model: gpt-3.5-turbo  # OpenAI model to use, gpt-4o-mini by default

To select models for each method, you can refer to the following links:

* `SpaCy models <https://spacy.io/models>`_
* `Sentence Transformers models <https://github.com/UKPLab/sentence-transformers>`_
* `OpenAI models <https://platform.openai.com/docs/models>`_

Installation
~~~~~~~~~~~~

Make sure to install the required libraries for the chosen method. For SpaCy, Sentence Transformers or OpenAI LLM, you
can install them with the following command:

.. code-block:: bash

    pip install toolium[ai]

**Additional Requirements:**

For SpaCy, you also need to download the language model, i.e. for small English model:

.. code-block:: bash

    python -m spacy download en_core_web_sm

For OpenAI LLM, you need to set up your configuration in environment variables, that it may depend on the type of access
you have (direct OpenAI access or Azure OpenAI):

.. code-block:: bash

    # For example, to configure direct OpenAI access:
    OPENAI_API_KEY=<your_api_key>

.. code-block:: bash

    # For example, to configure Azure OpenAI:
    AZURE_OPENAI_API_KEY=<your_api_key>
    AZURE_OPENAI_ENDPOINT=<your_endpoint>
    OPENAI_API_VERSION=<your_api_version>


Accuracy tag for Behave scenarios
---------------------------------

You can use accuracy tags in your Behave scenarios to specify the desired accuracy level and number of retries for
scenarios that involve AI-generated content. The accuracy tag follows the format `@accuracy_<percent>_<retries>`,
where `<percent>` is the desired accuracy percentage (0-100) and `<retries>` is the number of retries to achieve that
accuracy. For example, `@accuracy_80_10` indicates that the scenario should achieve at least 80% accuracy retrying the
scenario execution 10 times.

.. code-block:: bash

    @accuracy_80_10
    Scenario: Validate AI-generated response accuracy
      Given the AI model generates a response
      When the user sends a message
      Then the AI response should be accurate

When a scenario is tagged with an accuracy tag, Toolium will automatically execute the scenario multiple times. If the
scenario does not meet the specified accuracy after the given number of retries, it will be marked as failed.

Other examples of accuracy tags:
- `@accuracy_percent_85_retries_10`: 85% accuracy, 10 retries
- `@accuracy_percent_75`: 75% accuracy, default 10 retries
- `@accuracy_90_5`: 90% accuracy, 5 retries
- `@accuracy_80`: 80% accuracy, default 10 retries
- `@accuracy`: default 90% accuracy, 10 retries
