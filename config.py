import os
from typing import Dict
from dotenv import load_dotenv
from utils import print_error


def load_configuration() -> Dict[str, str]:
    """
    Load the configuration from environment variables.

    Returns:
        A dictionary containing the configuration values.
    Raises:
        ValueError: If the Anthropic API key is not found in the environment variables.
    """
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        error_msg = "No Anthropic API key found. Set it in a .env file."
        print_error(error_msg)
        raise ValueError(error_msg)
    return {"anthropic_api_key": api_key}
