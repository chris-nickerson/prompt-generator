from utils import print_info


def prompt_user():
    print_info("\n*** Claude Prompt Generator ***")
    print_info("\nThis tool can help engineer effective prompts for Claude.")
    print_info("\nWould you like to:")
    print_info("1. Enter a custom prompt description")
    print_info("2. View preset examples")

    user_choice = input("\nEnter your choice (1 or 2): ")

    if user_choice == "1":
        print_info("\nHere are a few examples to inspire you:")
        display_example_prompts()
        print_info(f"\nInclude any input variables Claude should consider\n")
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


def display_example_prompts():
    example_prompts = [
        "Identify and list key points from an input meeting transcript.",
        "Rewrite an email to be more formal. Take the email as input.",
        "Extract dates and event names from an input text about historical events and store them in XML tags.",
    ]
    for example in example_prompts:
        print_info(f"- {example}")


def get_prompt_options():
    return {
        "1": "Redact personally identifiable information from an input text with 'XXX'.",
        "2": "Solve the input reasoning question.",
        "3": "Extract phone numbers from an input text and list them in a standard format.",
        "4": "Extract and list all last names from a given input text.",
        "5": "Act as a helpful chatbot for home-office IT issues. Answer user questions using LLM general knowledge. Take a user question as input.",
        "6": "Act as a virtual customer service agent for Anthropic with access to an FAQ document. Take a user question as input.",
        "7": "Extract information from a student info text file into JSON with keys 'name', 'grade', 'gpa', 'major'.",
    }


def get_test_cases_count():
    while True:
        try:
            count = int(input("\nEnter the number of test cases to generate (0-10): "))
            if 0 <= count <= 10:
                return count
            else:
                print_info("Please enter a number between 0 and 10.")
        except ValueError:
            print_info("Invalid input. Please enter a number.")
