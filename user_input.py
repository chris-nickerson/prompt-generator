from utils import print_info


# Function to prompt user for prompt description
def prompt_user():
    print_info("\n*** Claude Prompt Generator ***")
    print_info("\nThis tool can help engineer effective prompts for Claude.")
    print_info("\nWould you like to:")
    print_info("1. Enter a custom prompt description")
    print_info("2. View preset examples")

    user_choice = input("\nEnter your choice (1 or 2): ")

    if user_choice == "1":
        custom_prompt = input("This prompt should guide Claude to: ")
        print_info(f"\nCustom prompt description entered: {custom_prompt}")
        return "The prompt should guide the LLM to: " + custom_prompt
    elif user_choice == "2":
        return display_presets()
    else:
        print_info("\nInvalid choice. Please enter 1 or 2.")
        return prompt_user()  # Recursive call for invalid input


def display_presets():
    prompt_options = get_prompt_options()
    print_info("\nSelect a preset example:")
    for key, value in prompt_options.items():
        print_info(f"{key}. {value}")
    user_input = input("\nEnter the number of your choice: ")

    if user_input in prompt_options:
        print_info(f"\nYou have selected: {prompt_options[user_input]}")
        return "The prompt should guide the LLM to: " + prompt_options[user_input]
    else:
        print_info("\nInvalid selection. Please try again.")
        return display_presets()  # Recursive call for invalid input


def get_prompt_options():
    return {
        "1": "Redact personally identifiable information (PII) from a given text with 'XXX' and return the redacted text.",
        "2": "Solve the given reasoning question.",
        "3": "Extract phone numbers from a given text and list them in a standard format.",
        "4": "Extract and list all names from a given text.",
        "5": "Compose a haiku on a given topic.",
        "6": "Act as a helpful chatbot for home-office IT issues. Answer user questions using LLM general knowledge. Take a user question as input.",
        "7": "Act as a virtual customer service agent for Anthropic with access to an FAQ document. Take a user question as input.",
        "8": "Create a short rap about a given inanimate object.",
        "9": "Organize information from a given student info text file into JSON with keys 'name', 'grade', 'gpa', 'major'.",
    }
