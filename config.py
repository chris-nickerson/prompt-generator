from dotenv import load_dotenv
import os


def load_configuration():
    load_dotenv()
    return {
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY")
        # Add other configurations as needed
    }
