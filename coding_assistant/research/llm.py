# One place for plain model calls (question generation, judge, figure vision):
# waits and retries when Google answers 429 (rate limit) or 5xx (overloaded),
# and when a request hangs (no answer within `timeout` seconds).

import time

import openai

_RETRY_CODES = (429, 500, 502, 503, 504)


def chat(client: openai.OpenAI, retries: int = 5, timeout: float = 60, **kwargs):
    """client.chat.completions.create(**kwargs) with timeout, waiting and retrying."""
    fast = client.with_options(timeout=timeout, max_retries=0)  # we do the retrying ourselves
    for attempt in range(retries + 1):
        try:
            return fast.chat.completions.create(**kwargs)
        except (openai.APITimeoutError, openai.APIConnectionError) as error:
            if attempt >= retries:
                raise
            wait = 10 * (attempt + 1)
            print(f"No answer ({type(error).__name__}), waiting {wait} s ...")
            time.sleep(wait)
        except openai.APIStatusError as error:
            if error.status_code == 429 and "PerDay" in str(error.body):
                raise  # daily quota: waiting does not help
            if error.status_code in _RETRY_CODES and attempt < retries:
                wait = 20 * (attempt + 1)
                print(f"Model answered {error.status_code}, waiting {wait} s ...")
                time.sleep(wait)
                continue
            raise
