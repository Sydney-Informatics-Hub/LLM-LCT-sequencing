# Test functions for the class LLM in tools.utils_llm

import sys

sys.path.append('../tools')
from utils_llm import LLM

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
    assert len(completion_text) > 0
    assert tokens_used > 0
    assert len(logprobs) > 0


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
    assert len(completion_text) > 0
    assert tokens_used > 0