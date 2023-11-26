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


def main():
    config = load_configuration()
    api_key = config.get("anthropic_api_key")

    # Early exit if no API key found
    if not api_key:
        print_error("No API key found.")
        return

    api = AnthropicAPI(api_key)
    prompt_processor = PromptProcessor(api)
    goal = prompt_user()

    combined_results, test_results = [], {}
    test_cases, first_iteration = None, True

    while True:
        prompt_template, cleaned_prompt = prompt_processor.generate_and_clean_prompt(
            goal, test_results
        )
        placeholders = prompt_processor.identify_placeholders(prompt_template)

        input_vars_detected = placeholders[0] != "None"
        if first_iteration and input_vars_detected:
            test_cases = prompt_processor.setup_test_cases(
                prompt_template, placeholders
            )

        if input_vars_detected:
            # Skip processing if no test cases are defined
            if not test_cases:
                print_warning("No test cases available.")
                break

            (
                test_results,
                combined_results,
                failed_tests,
            ) = prompt_processor.process_test_cases(
                test_cases, prompt_template, combined_results, test_results
            )

            if not failed_tests:
                print_success("\n*** All test cases passed! ***")
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
                    "\n*** Evaluation passed! No input variables detected. ***"
                )
                break

        first_iteration = False

    save_results_to_json(combined_results)
    print_final_results(cleaned_prompt)


if __name__ == "__main__":
    main()
