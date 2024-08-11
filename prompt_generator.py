import re
import asyncio
from utils import (
    print_success,
    print_info,
    print_warning,
    print_final_results,
    save_results_to_json,
)
from config import load_configuration
from api_communication import AnthropicAPI
from prompt_processing import PromptProcessor
from user_input import prompt_user, get_test_cases_count


async def main() -> None:
    """
    Main function that generates prompts, processes test cases, and prints results.

    Returns:
        None
    """
    ...
    config = load_configuration()
    api_key = config.get("anthropic_api_key")

    api_client = AnthropicAPI(api_key)
    prompt_processor = PromptProcessor(api_client)
    goal = prompt_user()
    num_test_cases = get_test_cases_count()

    combined_results, test_results = [], {}
    test_cases, first_iteration = None, True

    while True:
        prompt_template = await prompt_processor.generate_prompt_handler(
            goal, test_results
        )
        if prompt_template is None:
            return None  # Prompt generation failed
        if num_test_cases == 0:
            print_info("\n*** No test cases to evaluate. ***")
            break
        placeholders = re.findall(r"{\w+}", prompt_template)

        input_vars_detected = bool(placeholders)
        if first_iteration and input_vars_detected:
            test_cases = await prompt_processor.setup_test_cases(
                num_test_cases, prompt_template, placeholders
            )
            if not test_cases:
                return None  # Test case generation failed

        if input_vars_detected:
            # Skip processing if no test cases are defined
            if not test_cases:
                print_warning("No test cases available.")
                break

            (
                test_results,
                combined_results,
                failed_tests,
            ) = await prompt_processor.process_test_cases(
                test_cases, prompt_template, combined_results, test_results
            )
            if not test_results and not combined_results and not failed_tests:
                return None  # Prompt Execution or Evaluation failed

            if not failed_tests:
                print_success("\n*** All test cases passed! ***")
                break
        else:
            (
                test_results,
                combined_results,
                failed_evaluation,
            ) = await prompt_processor.process_no_input_var_case(
                prompt_template, combined_results, test_results
            )
            if (
                test_results is None
                and combined_results is None
                and failed_evaluation is None
            ):
                return  # Prompt Execution or Evaluation failed
            if not failed_evaluation:
                print_success(
                    "\n*** Evaluation passed! No input variables detected. ***"
                )
                break

        first_iteration = False

    save_results_to_json(combined_results)
    print_final_results(prompt_template)


if __name__ == "__main__":
    asyncio.run(main())
