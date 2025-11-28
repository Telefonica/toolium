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
    threshold = 0.8  # Similarity threshold between 0 and 1
    technical_characters = ['$', '%', '&']  # Optional: list of characters considered non-linguistic content
    readability_method = 'spacy'  # Only 'spacy' is currently supported

    # Validate similarity
    assert_text_readability(input_text, threshold=threshold, technical_characters=technical_characters, readability_method=readability_method)

Configuration
~~~~~~~~~~~~~

Default readability method and spacy model can be set in the *[AI]* section of the properties.cfg file::

    [AI]
    text_readability_method: spacy  # Only 'spacy' is currently supported
    spacy_model: en_core_web_md  # SpaCy model to use, en_core_web_md by default

For more information on SpaCy models, you can refer to the following link:

* `SpaCy models <https://spacy.io/models>`_

Installation
~~~~~~~~~~~~

The requirements are the same explained for `SpaCy` in the
`installation section of Text Similarity <https://toolium.readthedocs.io/en/latest/ai_utils.html#installation>`_


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
