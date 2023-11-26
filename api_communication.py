from anthropic import Anthropic
from utils import print_warning


class AnthropicAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.anthropic = Anthropic(api_key=self.api_key)

    def send_request_to_claude(self, prompt, max_tokens_to_sample=100000, temperature=0.05):
        try:
            completion = self.anthropic.completions.create(
                prompt=prompt,
                model="claude-2.1",  # Model version can be adjusted as needed
                max_tokens_to_sample=max_tokens_to_sample,
                temperature=temperature,
            )
            response = completion.completion
            stop_reason = completion.stop_reason

            return self._process_completion_response(response, stop_reason)

        except Exception as e:
            print_warning(f"An error occurred: {e}")
            return None

    @staticmethod
    def _process_completion_response(response, stop_reason):
        if stop_reason != "stop_sequence":
            print_warning(f"Completion stopped unexpectedly. Reason: '{stop_reason}'")
            return None

        if len(response) < 10 and "no" in response.lower():
            print_warning("Completion failed.")
            return None

        return response
