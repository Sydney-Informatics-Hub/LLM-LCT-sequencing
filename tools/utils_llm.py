# Python utility functions for LLM handling and tokenisation such as OpenAI

import tiktoken

def count_tokens(prompt, encoding_name="gpt-3.5-turbo"):
    """
    Count the number of tokens in a given prompt text string using tiktoken.

    Parameters:
    - prompt (str): The input text string.
    - encoding_name (str): The LLM engine type (e.g., "davinci", "gpt-3.5-turbo", "gpt-4").

    Returns:
    - int: The number of tokens in the prompt text.
    """
    encoding = tiktoken.encoding_for_model(encoding_name)
    num_tokens = len(encoding.encode(prompt))
    return num_tokens
