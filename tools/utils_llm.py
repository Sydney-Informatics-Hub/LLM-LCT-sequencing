# Python utility functions for LLM handling and tokenisation such as OpenAI

"""
For OpenAI pricing, see https://openai.com/pricing
For OpenAI API documentation, see https://beta.openai.com/docs/api-reference/completions/create

"""

import os
import tiktoken
import openai

class LLM:
    """
    A class to handle the LLM API.
    """
    def __init__(self, filename_openai_key='../../openai_key.txt', model_name = 'gpt-3.5-turbo'):
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


    def request_completion(self, prompt, temperature = 0, max_tokens = 4000, get_logprobs = True):
        """
        Request a completion from the LLM API.

        Parameters:
        ----------
        - prompt (str): The input text string.
        - temperature (float): The sampling temperature.
        - max_tokens (int): The maximum number of tokens to generate.

        Returns:
        ----------
        - str: The completion text.
        - int: The number of tokens used.
        - str: The completion id.
        - list: The log probabilities for each token.
        """
        if get_logprobs:
            logprobs = 1
        else:
            logprobs = None
        model_name = self.model_name
        if model_name == 'gpt-3.5-turbo':
            print("Warning: gpt-3.5-turbo is not available for completions API. Using gpt-3.5-turbo-instruct instead.")
            model_name = 'gpt-3.5-turbo-instruct'
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
        return completion_text, tokens_used, completion_id, logprobs 


    def request_chatcompletion(self, prompt, messages = None, temperature=0, max_tokens = 4000):
        """
        Use OpenAI's Chat completions API

        Parameters:
        ----------
        - prompt (str): The input text string.
        - messages (list): A list of messages in the chat. Each message is a dictionary with keys 'role' and 'content'.
        - temperature (float): The temperature of the completion. Higher values mean the model will take more risks.
        - max_tokens (int): The maximum number of tokens to generate.

        Returns:
        ----------
        - str: The completion text.
        - int: The number of tokens used.
        - str: The completion id.
        - dict: The response message.
        """
        if messages is None:
            messages = []
         # check if prompt follows chat completion format
        if isinstance(prompt, dict):
            if not (prompt['role'] == 'user' or prompt['role'] == 'system'):
                raise ValueError("Prompt does not follow chat completion format. See https://beta.openai.com/docs/api-reference/completions/create#chat-format")
        else:
            prompt = {"role": "user", "content": prompt}
        messages.append(prompt)
        completion_response = openai.ChatCompletion.create(
                                messages = messages,
                                temperature=temperature,
                                max_tokens=max_tokens,
                                model=self.model_name,
                                stop=['\n']
                                )
        # Get the completion text
        message_response = completion_response['choices'][0]['message']
        completion_text = message_response['content']
        # Get the number of tokens used
        tokens_used = completion_response['usage']['total_tokens']
        # Get id of the completion
        completion_id = completion_response['id']
        return completion_text, tokens_used, completion_id, message_response


# test the LLM class (see also tests/test_utils_llm.py)

def test_llm_completion():
    """
    test the LLM class with a completion
    """
    prompt = """What sequencing class is the following example? If you don't know answer with 'None'.
    example: Testing and LLM is fun or not!\n
    Answer: """
    llm = LLM()
    print(f'prompt: {prompt}')
    completion_text, tokens_used, chat_id, logprobs = llm.request_completion(prompt)
    print(f'completion_text: {completion_text}')
    print(f'tokens_used: {tokens_used}')
    print(f'token logprobs: {logprobs}')


def test_llm_chatcompletion():
    """
    test the LLM class with a chat completion
    """
    prompt = """What sequencing class is the following example?
    example: Testing and LLM is fun or not!\n
    Answer: """
    llm = LLM()
    print(f'prompt: {prompt}')
    completion_text, tokens_used, chat_id, message = llm.request_chatcompletion(prompt)
    print(f'completion_text: {completion_text}')
    print(f'tokens_used: {tokens_used}')