from typing import Optional
from anthropic import Anthropic
from utils import print_error


class AnthropicAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.anthropic = Anthropic(api_key=self.api_key)

    def send_request_to_claude(
        self, prompt: str, max_tokens_to_sample: int = 4000, temperature: float = 0.05
    ) -> Optional[str]:
        """
        Sends a request to the Anthropic API to generate a response based on the given prompt.

        Args:
            prompt (str): The prompt for generating the response.
            max_tokens_to_sample (int, optional): The maximum number of tokens to sample. Defaults to 4000.
            temperature (float, optional): The temperature parameter for controlling the randomness of the generated response. Defaults to 0.05.

        Returns:
            Optional[str]: The generated response from the Claude API, or None if an error occurred.
        """
        try:
            completion = self.anthropic.messages.create(
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
                self._handle_http_error(e)
            else:
                print_error(f"An unexpected error occurred: {e}")
            return None

    def _handle_http_error(self, error: Exception) -> None:
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
            print_error(f"Anthropic API error: {error}")
        else:
            print_error(f"Unexpected HTTP error: {error})")
