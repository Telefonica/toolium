AI Utils
========

Text Similarity
---------------

Text similarity is a measure of how alike two pieces of text are in terms of meaning, structure, or content. 
Toolium provides several methods to compare and validate text similarity using different AI techniques:

1. **SpaCy**: Uses the SpaCy library to compute text similarity with pre-trained NLP models. Fast, lightweight and good for general-purpose text analysis.
2. **Sentence Transformers**: Leverages Sentence Transformers for semantic textual similarity using deep learning embeddings. Best balance of accuracy and performance for semantic similarity.
3. **OpenAI**: Utilizes OpenAI's language models for advanced semantic text comparison. Provides the most sophisticated analysis but requires API access and it may incur costs.

Usage
~~~~~

You can use the function `assert_text_similarity` from `toolium.utils.ai_utils` module to compare two texts using any of these
methods. You can specify the method to use with the `similarity_method` parameter and set a threshold for similarity with the
`threshold` parameter (a value between 0 and 1, where 1 means identical and 0 means completely different).

.. code-block:: python

    from toolium.utils.ai_utils import assert_text_similarity

    # Basic usage
    input_text = "The quick brown fox jumps over the lazy dog"
    expected_text = "A fast brown fox leaps over a sleepy dog"  # Admits both a single expected text or a list of expected texts
    threshold = 0.8  # Similarity threshold between 0 and 1
    similarity_method = 'spacy'  # Options: 'spacy', 'sentence_transformers', 'openai', 'azure_openai'

    # Validate similarity
    assert_text_similarity(input_text, expected_text, threshold=threshold, similarity_method=similarity_method)

Configuration
~~~~~~~~~~~~~

Default similarity method can be set in the properties.cfg file with the property
`text_similarity_method <https://toolium.readthedocs.io/en/latest/ai_utils.html#configuration>`_ in *[AI]* section::

    [AI]
    text_similarity_method: openai  # Options: 'spacy' (default), 'sentence_transformers', 'openai', 'azure_openai'
    spacy_model: en_core_web_lg  # SpaCy model to use, en_core_web_sm by default
    sentence_transformers_model: all-MiniLM-L6-v2  # Sentence Transformers model to use, all-mpnet-base-v2 by default
    openai_model: gpt-3.5-turbo  # OpenAI model to use, gpt-4o-mini by default

To select models for each method, you can refer to the following links:

* SpaCy: `https://spacy.io/models`
* Sentence Transformers: `https://github.com/UKPLab/sentence-transformers`
* OpenAI: `https://platform.openai.com/docs/models`

Installation
~~~~~~~~~~~~

Make sure to install the required libraries for the chosen method. For SpaCy, Sentence Transformers or OpenAI LLM, you
can install them with the following command:

.. code-block:: bash

    pip install toolium[ai]

**Additional Requirements:**

For SpaCy, you also need to download the language model, i.e. for small English model::

.. code-block:: bash

    python -m spacy download en_core_web_sm

For OpenAI LLM, you need to set up your configuration in environment variables, that it may depend on the type of access you have (direct OpenAI access or Azure OpenAI).

.. code-block:: bash

    # For example, to configure direct OpenAI access:
    OPENAI_API_KEY=<your_api_key>

.. code-block:: bash

    # For example, to configure Azure OpenAI:
    AZURE_OPENAI_API_KEY=<your_api_key>
    AZURE_OPENAI_ENDPOINT=<your_endpoint>
    OPENAI_API_VERSION=<your_api_version>
