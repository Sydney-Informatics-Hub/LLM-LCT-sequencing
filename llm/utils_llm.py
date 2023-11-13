# Python utility functions for LLM handling and tokenisation such as OpenAI

"""
For OpenAI pricing, see https://openai.com/pricing
For OpenAI API documentation, see https://beta.openai.com/docs/api-reference/completions/create

"""

import os
import tiktoken
import openai
import panel as pn
from openai.error import AuthenticationError, APIConnectionError
import logging


class LLM:
    """
    A class to handle the LLM API.
    """
    def __init__(self, filename_openai_key=None, model_name = 'gpt-3.5-turbo'):
        """
        Initialize the LLM object with the API key and model name

        Note: The API key is stored in a text file. Do not share this file with others or on Github.
        """
        # Manual API key input if no file is given
        if filename_openai_key is None:
            # Check if API key is already set
            openai.api_key = os.environ.get("OPENAI_API_KEY")
            # check if API key is valid
            try:
                ailist = openai.Model.list()
                logging.debug('LLM initialized.')
            except openai.error.AuthenticationError:
                logging.debug("No valid OpenAI API key found. Please enter your OpenAI API key.")
        else:
            # Check if file exists
            if not os.path.isfile(filename_openai_key):
                raise FileNotFoundError("OpenAI key file does not exist: {}".format(filename_openai_key))
            with open(filename_openai_key, 'r') as f:
                openai.api_key = f.read()
            logging.debug('LLM initialized with API key from file: {}'.format(filename_openai_key))
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


    def request_completion(self, prompt, temperature = 0, max_tokens = 1000, get_logprobs = True):
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
            logging.warning("Warning: gpt-3.5-turbo is not available for completions API. Using gpt-3.5-turbo-instruct instead.")
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


    def request_chatcompletion(self, prompt, messages = None, temperature=0, max_tokens = 1000):
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
                                )
        # Get the completion text
        message_response = completion_response['choices'][0]['message']
        completion_text = message_response['content']
        # Get the number of tokens used
        tokens_used = completion_response['usage']['total_tokens']
        # Get id of the completion
        completion_id = completion_response['id']
        return completion_text, tokens_used, completion_id, message_response

def openai_apikey_input():
    """
    Create a password input widget to enter the OpenAI API key.
    """
    pn.extension()
    password_input = pn.widgets.PasswordInput(name='Enter your OpenAI API Key (then press enter):',
                                              placeholder='<OpenAI API Key>')

    def _cb_overwrite_api(key: str):
        if len(key) == 0:
            return "Please enter your OpenAI API Key."
        else:
            if len(key) == 51:
                try:
                    openai.api_key = key
                    _ = openai.Model.list()
                    os.environ['OPENAI_API_KEY'] = key
                    return "Valid API Key. Please continue."
                except AuthenticationError as ae:
                    return str(ae)
                except APIConnectionError as ace:
                    logging.debug(ace)
                    return "Something is wrong with your network connection. Please try again."
                except Exception as e:
                    logging.debug(str(e))
                    return "Something went wrong when validating API Key. Please try again."
            return "Incorrect API key provided. Must be 51 characters."

    iobject = pn.bind(_cb_overwrite_api,
                      password_input.param.value,
                      watch=False)  # watch=False callback triggered with "Enter"
    return pn.Row(password_input, pn.pane.Markdown(iobject))


def openai_models():
    # return openai available models
    return openai.Model.list()

def find_clause_position(text, clause):
    """
    Find position of str in a text

    Parameters:
    -----------
    - text (str): The text to search in.
    - clause (str): The clause to search for.

    Returns:
    --------
    - start_position (int): The start position of the clause in the text.
    - end_position (int): The end position of the clause in the text.
    - bracketed_text (str): The text with brackets around the clause.
    """
    # enforce utf8 encoding
    text = text.encode('utf8', errors='ignore').decode('utf8')
    clause = clause.encode('utf8', errors='ignore').decode('utf8')

    # Find the start position of the clause in the text
    start_position = text.find(clause)
    
    # If the clause is not found, return None values
    if start_position == -1:
        return None, None, text

    # Calculate the end position
    end_position = start_position + len(clause) - 1

    # Insert brackets around the clause
    bracketed_text = text[:start_position] + "[" + clause + "]" + text[end_position + 1:]

    return start_position, end_position, bracketed_text


def test_llm_completion():
    """
    test the LLM class with a completion
    """
    prompt = """What sequencing class is the following example? If you don't know answer with 'None'.
    example: Testing and LLM is fun or not!\n
    Answer: """
    llm = LLM()
    logging.debug(f'prompt: {prompt}')
    completion_text, tokens_used, chat_id, logprobs = llm.request_completion(prompt)
    logging.debug(f'completion_text: {completion_text}')
    logging.debug(f'tokens_used: {tokens_used}')
    logging.debug(f'token logprobs: {logprobs}')


def test_llm_chatcompletion():
    """
    test the LLM class with a chat completion
    """
    prompt = """What sequencing class is the following example?
    example: Testing and LLM is fun or not!\n
    Answer: """
    llm = LLM()
    logging.debug(f'prompt: {prompt}')
    completion_text, tokens_used, chat_id, message = llm.request_chatcompletion(prompt)
    logging.debug(f'completion_text: {completion_text}')
    logging.debug(f'tokens_used: {tokens_used}')