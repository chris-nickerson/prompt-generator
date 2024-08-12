from typing import Any, Dict, Optional

import asyncio
from anthropic import AsyncAnthropic
from writerai import AsyncWriter
from utils import print_error, print_warning


def handle_http_error(error: Exception) -> None:
    """
    Handles HTTP errors based on the status code.

    Args:
        error: The HTTP error object.

    Returns:
        None

    Raises:
        None
    """
    status_code = error.status_code
    # Custom handling for each status code
    if status_code in (400, 401, 403, 404, 429, 500, 529):
        print_error(f"API error: {error}")
    else:
        print_error(f"Unexpected HTTP error: {error})")


class AnthropicAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def send_request_to_model(
        self,
        prompt: str,
        max_tokens_to_sample: int = 4000,
        temperature: float = 0,
        max_retries: int = 10,
    ) -> Optional[str]:
        """
        Sends a request to the Anthropic API to generate a response based on the given prompt.

        Args:
            prompt (str): The prompt for generating the response.
            max_tokens_to_sample (int, optional): The maximum number of tokens to sample. Defaults to 4000.
            temperature (float, optional): The temperature parameter for controlling the randomness of the generated response. Defaults to 0.

        Returns:
            Optional[str]: The generated response from the Claude API, or None if an error occurred.
        """
        rate_limit_sleep_time = 0.5
        for _ in range(max_retries):
            try:
                async with AsyncAnthropic() as client:
                    completion = await client.messages.create(
                        model="claude-3-sonnet-20240229",
                        max_tokens=max_tokens_to_sample,
                        temperature=temperature,
                        messages=[
                            {
                                "role": "user",
                                "content": prompt,
                            }
                        ],
                    )
                    return completion.content[0].text
            except Exception as e:
                if hasattr(e, "status_code"):
                    if e.status_code == 429:  # Anthropic API rate limit exceeded
                        print_warning(
                            f"Rate limit exceeded. Waiting for {rate_limit_sleep_time} seconds..."
                        )
                        await asyncio.sleep(rate_limit_sleep_time)
                        rate_limit_sleep_time *= 1.5
                    else:
                        handle_http_error(e)
                else:
                    print_error(f"An unexpected error occurred: {e}")
                    return None
        print_error("Max retries exceeded. Failed to generate a response.")
        return None


class WriterAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def send_request_to_model(
        self,
        prompt: str,
        max_tokens_to_sample: int = 4000,
        temperature: float = 0,
        config: Dict[str, Any] = {},
        max_retries: int = 10,
    ) -> Optional[str]:
        """
        Sends a request to the Writer API to generate a response based on the given prompt.

        Args:
            prompt (str): The prompt for generating the response.
            max_tokens_to_sample (int, optional): The maximum number of tokens to sample. Defaults to 4000.
            temperature (float, optional): The temperature parameter for controlling the randomness of the generated response. Defaults to 0.

        Returns:
            Optional[str]: The generated response from the Writer API, or None if an error occurred.
        """
        if not config:
            config = {"temperature": temperature, "max_tokens": max_tokens_to_sample}

        rate_limit_sleep_time = 0.5
        for _ in range(max_retries):
            async with AsyncWriter() as client:
                try:
                    completion = await client.completions.create(
                        model="palmyra-x-32k",
                        prompt=prompt,
                        stream=False,
                    )
                    return completion.choices[0].text
                except Exception as e:
                    if hasattr(e, "status_code"):
                        if e.status_code == 429:  # Writer API rate limit exceeded
                            print_warning(
                                f"Rate limit exceeded. Waiting for {rate_limit_sleep_time} seconds..."
                            )
                            await asyncio.sleep(rate_limit_sleep_time)
                            rate_limit_sleep_time *= 1.5
                        else:
                            handle_http_error(e)
                    else:
                        print_error(f"An unexpected error occurred: {e}")
                        return None
        print_error("Max retries exceeded. Failed to generate a response.")
        return None
