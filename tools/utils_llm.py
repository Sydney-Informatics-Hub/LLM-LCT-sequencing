# Python utility functions for LLM handling and tokenisation such as OpenAI

import os
import tiktoken
import openai

class LLM:
    """
    A class to handle the LLM API.
    """
    def __init__(self, filename_openai_key='../../openai_key.txt', model_name = 'gpt-3.5-turbo-instruct'):
        """
        Initialize the LLM object with the API key and model name

        Note: The API key is stored in a text file. Do not share this file with others or on Github.
        """
        # Check if file exists
        if not os.path.isfile(filename_openai_key):
            raise FileNotFoundError("OpenAI key file does not exist: {}".format(filename_openai_key))
        with open(filename_openai_key, 'r') as f:
            openai.api_key = f.read()
        self.model_name = model_name


    def count_tokens(self, prompt):
        """
        Count the number of tokens in a given prompt text string using tiktoken.

        Parameters:
        - prompt (str): The input text string.
        - encoding_name (str): The LLM engine type (e.g., "davinci", "gpt-3.5-turbo", "gpt-4").

        Returns:
        - int: The number of tokens in the prompt text.
        """
        try:
            encoding = tiktoken.encoding_for_model(self.model_name)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        num_tokens = len(encoding.encode(prompt))
        return num_tokens


    def request_completion(self, 
        prompt, temperature = 0, 
        max_tokens = 3000,
        logprobs = 1):
        """
        Request a completion from the LLM API.

        Parameters:
        ----------
        - prompt (str): The input text string.

        Returns:
        ----------
        - str: The completion text.
        - int: The number of tokens used.
        """
        completion_response = openai.Completion.create(
                                prompt=prompt,
                                temperature=temperature,
                                max_tokens=max_tokens,
                                logprobs=logprobs,
                                #top_p=top_p,
                                #frequency_penalty=0,
                                #presence_penalty=0,
                                model=model_name
                                )
        # Get the completion text
        completion_text = completion_response['choices'][0]['text']
        # Get the number of tokens used
        tokens_used = completion_response['usage']['total_tokens']
        # Get id of the completion
        completion_id = completion_response['id']
        # Get log probabilities (list for each token)
        logprobs = completion_response['choices'][0]['logprobs']['token_logprobs']
        return completion_text, tokens_used, logprobs, completion_id 


def test_llm():
    """
    test the LLM class
    """
    prompt = """What sequencing class is the following example? If you don't know answer with 'None'.
    example: Testing and LLM is fun or not!\n
    Answer: """
    llm = LLM()
    print(f'prompt: {prompt}')
    completion_text, tokens_used = llm.request_completion(prompt)
    print(f'completion_text: {completion_text}')
    print(f'tokens_used: {tokens_used}')