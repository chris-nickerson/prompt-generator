import os
from typing import Dict
from dotenv import load_dotenv
from utils import print_error


def load_anthropic_configuration() -> Dict[str, str]:
    """
    Load the configuration for the Anthropic API from environment variables.
    Returns:
        A dictionary containing the configuration values.
    Raises:
        ValueError: If the Anthropic API key is not found in the environment variables.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        error_msg = "No Anthropic API key found. Set it in a .env file."
        print_error(error_msg)
        raise ValueError(error_msg)
    return {"api_key": api_key}


def load_writer_configuration() -> Dict[str, str]:
    """
    Load the configuration for the Writer API from environment variables.
    Returns:
        A dictionary containing the configuration values.
    Raises:
        ValueError: If the Writer API key is not found in the environment variables.
    """
    api_key = os.getenv("WRITER_API_KEY")
    if not api_key:
        error_msg = "No Writer API key found. Set it in a .env file."
        print_error(error_msg)
        raise ValueError(error_msg)
    return {"api_key": api_key}


def load_configuration(provider: str) -> Dict[str, str]:
    """
    Load the configuration from environment variables.
    Args:
        provider (str): The name of the LLM provider.
    Returns:
        A dictionary containing the configuration values.
    Raises:
        ValueError: If the Anthropic API key is not found in the environment variables.
    """
    load_dotenv()
    if provider == "Anthropic":
        return load_anthropic_configuration()
    elif provider == "Writer":
        return load_writer_configuration()
    else:
        error_msg = (
            f"Invalid provider: {provider}. Please select 'Anthropic' or 'Writer'."
        )
        print_error(error_msg)
        raise ValueError(error_msg)
