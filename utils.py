import json
from colorama import Fore, Style


# Example of using color-coded print statements:
def print_info(message: str, end="\n"):
    print(f"{Fore.BLUE}{message}{Style.RESET_ALL}", end=end)


def print_success(message: str, end="\n"):
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}", end=end)


def print_warning(message: str, end="\n"):
    print(f"{Fore.YELLOW}{message}{Style.RESET_ALL}", end=end)


def print_error(message: str, end="\n"):
    print(f"{Fore.RED}{message}{Style.RESET_ALL}", end=end)


# Function to print the final generated prompt and completion message
def print_final_results(prompt_template: str):
    print_info(f"\nGENERATED PROMPT:")
    print(f"{prompt_template}")
    print_success(f"\n\n*** Prompt generation and evaluation complete. ***")
    print_info(f"*** See more in results.json file ***\n")


# Function to save results to a JSON file
def save_results_to_json(results, filename="results.json"):
    with open(filename, "w") as file:
        json.dump(results, file, indent=4)
