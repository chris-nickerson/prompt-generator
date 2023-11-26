# Imports
from utils import (
    print_success,
    print_warning,
    print_error,
    print_final_results,
    save_results_to_json,
)
from config import load_configuration
from api_communication import AnthropicAPI
from prompt_processing import PromptProcessor
from user_input import prompt_user


# Main execution flow
def main():
    config = load_configuration()
    # Check if the API key is available
    if not config.get("anthropic_api_key"):
        print_error("No API key found.")
        return
    anthropic_api_key = config["anthropic_api_key"]

    api = AnthropicAPI(anthropic_api_key)
    prompt_processor = PromptProcessor(api)

    goal = prompt_user()
    combined_results, test_results = [], {}
    input_vars_detected, first_iteration = False, True
    test_cases = None

    while True:
        (
            prompt_template,
            cleaned_prompt_template,
        ) = prompt_processor.generate_and_clean_prompt(goal, test_results)
        placeholder_names = prompt_processor.identify_placeholders(prompt_template)
        input_vars_detected = placeholder_names[0] != "None"

        # Generate test cases only on the first iteration and if input variables are detected
        if first_iteration and input_vars_detected:
            test_cases = prompt_processor.setup_test_cases(
                prompt_template, placeholder_names
            )

        if input_vars_detected:
            if test_cases is not None:  # Proceed if test_cases are available
                (
                    test_results,
                    combined_results,
                    failed_test_cases,
                ) = prompt_processor.process_test_cases(
                    test_cases, prompt_template, combined_results, test_results
                )
            else:
                print_warning("No test cases available.")
                break

            if not failed_test_cases:
                print_success(f"\n*** All test cases passed! ***")
                break
        else:
            (
                test_results,
                combined_results,
                failed_evaluation,
            ) = prompt_processor.process_no_input_var_case(
                prompt_template, combined_results, test_results
            )

            if not failed_evaluation:
                print_success(
                    f"\n*** Evaluation passed! No input variables were detected in this prompt. ***"
                )
                break

        first_iteration = False  # Set to False after the first iteration

    save_results_to_json(combined_results)
    print_final_results(cleaned_prompt_template)


if __name__ == "__main__":
    main()
