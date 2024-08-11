import re
from typing import Dict, List, Optional, Union, Tuple
import xml.etree.ElementTree as ET

from utils import print_error, print_warning, print_info, print_success


def extract_generated_prompt(response: str) -> Optional[str]:
    """
    Extracts the generated prompt from the given response.

    Args:
        response (str): The response string containing the generated prompt.

    Returns:
        Optional[str]: The extracted generated prompt, or None if not found.
    """
    pattern = r"<GENERATED_PROMPT>(.*?)</GENERATED_PROMPT>"
    try:
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        print_error("Prompt extraction failed: GENERATED_PROMPT tags not found.")
    except Exception as e:
        print_error(f"Error while extracting generated prompt: {e}")
    return None


def extract_variable_placeholders(response: str) -> Union[str, List[str]]:
    """
    Extracts variable placeholders from a given response.

    Args:
        response (str): The response string to search for variable placeholders.

    Returns:
        Union[str, List[str]]: The extracted variable placeholders as a list of strings, or None if no placeholders are found.

    Raises:
        None

    """
    try:
        match = re.search(
            r"<PLACEHOLDERS>(.*?)</PLACEHOLDERS>", response, re.DOTALL | re.IGNORECASE
        )
        if match:
            # Extracting the text found between the tags
            text = match.group(1).strip()
            # Splitting the text into a list of placeholder names
            return text.split("\n")
        # return "No variable placeholder XML tags found."
        print_error("No variable placeholder XML tags found.")
        return None
    except Exception as e:
        print_error(f"Error while extracting variable placeholders: {e}")
        return None


def preprocess_tags(xml_string: str) -> str:
    """
    Preprocesses the XML string by replacing spaces in tag names with a unique placeholder.

    Args:
        xml_string (str): The XML string to be preprocessed.

    Returns:
        str: The preprocessed XML string with spaces in tag names replaced by "_SPACE_".

    """
    # Replace spaces in tag names with a unique placeholder
    pattern = r"(<\s*)([^>]+)(\s*>)"
    for match in re.finditer(pattern, xml_string):
        xml_string = xml_string.replace(
            match.group(2), match.group(2).replace(" ", "_SPACE_")
        )
    return xml_string


def escape_ignored_tags(llm_output: str, tags_to_parse: Union[List[str], None]) -> str:
    """
    Escapes HTML tags in the given `llm_output` string, except for the tags specified in `tags_to_parse`.

    Args:
        llm_output (str): The input string containing HTML tags.
        tags_to_parse (Union[List[str], None]): A list of tags to be parsed. If None, all tags will be escaped.

    Returns:
        str: The modified string with escaped tags.
    """
    if tags_to_parse is not None:
        # Find all unique tags in the output
        unique_tags = set(re.findall(r"</?(\w+)>", llm_output))
        # Escape tags not in tags_to_parse
        for tag in unique_tags:
            if tag not in tags_to_parse:
                llm_output = llm_output.replace(f"<{tag}>", f"&lt;{tag}&gt;").replace(
                    f"</{tag}>", f"&lt;/{tag}&gt;"
                )
    return llm_output


def unescape_characters(parsed_data: Dict[str, str]) -> Dict[str, str]:
    """
    Replaces escaped characters in the values of a dictionary.

    Args:
        parsed_data (Dict[str, str]): A dictionary containing key-value pairs.

    Returns:
        Dict[str, str]: A dictionary with escaped characters replaced.

    """
    for key, value in parsed_data.items():
        if value is not None:
            parsed_data[key] = value.replace("&lt;", "<").replace("&gt;", ">")
    return parsed_data


def postprocess_tags(parsed_data: Dict[str, str]) -> Dict[str, str]:
    """
    Postprocesses the tags in the parsed data dictionary by replacing placeholders with spaces.

    Args:
        parsed_data (Dict[str, str]): The dictionary containing the parsed data.

    Returns:
        Dict[str, str]: The processed data dictionary with placeholders replaced by spaces.
    """
    # Create a new dictionary for the processed data
    processed_data = {}
    for key, value in parsed_data.items():
        # Replace placeholders in the key
        new_key = key.replace("_SPACE_", " ")
        # Replace placeholders in the value, if it's not None
        new_value = value.replace("_SPACE_", " ") if value is not None else None
        # Update the processed data dictionary
        processed_data[new_key] = new_value
    return processed_data


def parse_xml_content(llm_output: str, tags_to_parse=None) -> Dict[str, str]:
    """
    Parses the XML content from the given LLM output.

    Args:
        llm_output (str): The LLM output to parse.
        tags_to_parse (Optional[List[str]]): A list of tags to parse. If None, all tags will be parsed. Default is None.

    Returns:
        Dict[str, str]: A dictionary containing the parsed data, where the keys are the tag names and the values are the corresponding text.

    Raises:
        ET.ParseError: If there is an error parsing the XML.

    """
    # Preprocess the tags to replace spaces
    llm_output_preprocessed = preprocess_tags(llm_output.strip())
    llm_output_esc = escape_ignored_tags(llm_output_preprocessed, tags_to_parse)
    try:
        root = ET.fromstring(
            "<root>" + llm_output_esc + "</root>"
        )  # Wrapping with root tags
        if tags_to_parse is None:
            parsed_data = {child.tag: child.text for child in root}
        else:
            parsed_data = {
                child.tag: child.text for child in root if child.tag in tags_to_parse
            }
        if tags_to_parse:
            # Unescape characters before returning
            parsed_data = unescape_characters(parsed_data)
        # Post-process tags to restore spaces
        parsed_data = postprocess_tags(parsed_data)
        return parsed_data
    except ET.ParseError as e:
        print_info(
            f"Error parsing XML from LLM output: {e}\nReturning raw llm_output..."
        )
        return "parsing failed:" + llm_output


def extract_test_cases(response: str) -> Optional[Dict[str, Dict[str, str]]]:
    """
    Extracts test cases from the given response.

    Args:
        response (str): The response string containing test cases.

    Returns:
        Optional[Dict[str, Dict[str, str]]]: A dictionary containing the extracted test cases.
            The keys are the test case tags and the values are the parsed XML content of each test case.
            If no test cases are found, returns None.

    Raises:
        None.

    """
    try:
        test_cases = {}
        test_case_tags = re.findall(r"<TEST_CASE_(\d+)>", response, re.IGNORECASE)
        for tag in test_case_tags:
            # Constructing the tag name for the current test case
            test_case_tag = f"test_case_{tag}"

            match = re.search(
                rf"<{test_case_tag}>(.*?)</{test_case_tag}>",
                response,
                re.DOTALL | re.IGNORECASE,
            )

            if match:
                test_case_text = match.group(1).strip()
                parsed_xml = parse_xml_content(test_case_text)
                test_cases[test_case_tag] = parsed_xml
            else:
                test_cases[test_case_tag] = "No content within XML tags found."

        return test_cases
    except Exception as e:
        print_error(f"Error while extracting test cases: {e}")
        return None


def update_variable_names(
    test_cases: Dict[str, str],
    placeholder_names: List[str],
) -> Tuple[Dict[str, str], bool]:
    """
    Update the variable names in the test cases dictionary based on the provided placeholder names.

    Args:
        test_cases (Dict[str, str]): A dictionary containing the test cases.
        placeholder_names (List[str]): A list of placeholder names.
        test_case_retry (bool, optional): A flag indicating whether to retry generating test cases. Defaults to True.

    Returns:
        Tuple[Dict[str, str], bool]: A tuple containing the updated test cases dictionary and a flag indicating whether test case generation needs to be retried.
    """
    # Check if placeholder names match test case input variable names
    # Remove the leading { and trailing } from the placeholder names
    placeholder_names_cleaned = [
        name[1:-1]
        for name in placeholder_names
        if name.startswith("{") and name.endswith("}")
    ]

    sorted_placeholder_names = sorted(placeholder_names_cleaned)
    sorted_test_case_names = sorted(test_cases["test_case_1"].keys())

    mismatch_found = False
    for placeholder, test_case_name in zip(
        sorted_placeholder_names, sorted_test_case_names
    ):
        if placeholder != test_case_name:
            # Check if the mismatch is only due to case sensitivity
            if placeholder.lower() == test_case_name.lower():
                # Correct the case-sensitive mismatch
                for test_case_key in test_cases:
                    inner_dict = test_cases[test_case_key]
                    if test_case_name in inner_dict:
                        inner_dict[placeholder] = inner_dict.pop(test_case_name)
            else:
                # Un-fixable mismatch found, need to regenerate test cases
                print_warning(
                    f"Placeholder name '{placeholder}' does not match test case input variable name '{test_case_name}'. Regenerating test cases..."
                )
                mismatch_found = True
                inner_dict = {}
                break  # Exit the loop for un-fixable mismatch

    # If no mismatch was found, exit the while loop
    if not mismatch_found:
        return test_cases, False
    else:
        # Retry generating test cases
        return inner_dict, True


def load_prompt(prompt_template: str, test_case: Dict[str, str]) -> str:
    """
    Load and process a prompt template by replacing variables with corresponding values from a test case.

    Args:
        prompt_template (str): The template string containing variables to be replaced.
        test_case (Dict[str, str]): A dictionary containing variable-value pairs for replacement.

    Returns:
        str: The processed prompt string with variables replaced by their corresponding values.
    """
    for var_name, val in test_case.items():
        prompt_template = prompt_template.replace(f"{{{var_name}}}", val)
    return prompt_template


def extract_eval_result(evaluation: str) -> Optional[str]:
    """
    Extracts the evaluation result from the given evaluation string.

    Args:
        evaluation (str): The evaluation string.

    Returns:
        Optional[str]: The extracted evaluation result, or None if not found.
    """
    pattern = r"<EVALUATION_RESULT>(.*?)</EVALUATION_RESULT>"
    try:
        match = re.search(pattern, evaluation, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        print_error("Prompt extraction failed: EVALUATION_RESULT tags not found.")
    except Exception as e:
        print_error(f"Error while extracting eval: {e}")
    return None


def handle_eval_result(tc_name: str, eval_result: Optional[str]) -> bool:
    """
    Handle the evaluation result of a test case.

    Args:
        tc_name (str): The name of the test case.
        eval_result (Optional[str]): The evaluation result.

    Returns:
        bool: True if the evaluation result indicates failure, False otherwise.
    """
    if not eval_result:
        print_error("Evaluation result not found.")
        return False  # Default to no failure
    if tc_name == "":
        tc_name = "evaluation"
    print(f"{tc_name} result: ", end="")
    if eval_result == "FAIL":
        print_warning("FAIL")
        return True  # Indicates failure
    elif eval_result == "PASS" or (
        "pass" in eval_result.lower() and "fail" not in eval_result.lower()
    ):
        print_success("PASS")
        return False  # Indicates success
    else:
        print_info("Evaluation result unknown.")
        return False  # Default to no failure


def update_test_results(
    test_case_key: str,
    prompt_template: str,
    test_case_input: Dict[str, str],
    response: str,
    evaluation: str,
) -> Dict[str, Dict[str, Dict[str, Union[str, Dict[str, str]]]]]:
    """
    Update the test results with the given information.

    Args:
        test_case_key (str): The key of the test case.
        prompt_template (str): The template of the prompt.
        test_case_input (Dict[str, str]): The input for the test case.
        response (str): The response generated by the prompt.
        evaluation (str): The evaluation of the response.

    Returns:
        Dict[str, Dict[str, Dict[str, Union[str, Dict[str, str]]]]]: The updated test results.
    """
    test_result = {}
    test_result[test_case_key] = {
        "prompt": prompt_template,
        "input": test_case_input,
        "response": response,
        "evaluation": evaluation,
    }
    return test_result


def store_results_for_file(
    test_case: str, response: str, evaluation: str
) -> Dict[str, Dict[str, str]]:
    """
    Store the results for a file.

    Args:
        test_case (str): The test case identifier.
        response (str): The response for the test case.
        evaluation (str): The evaluation result for the test case.

    Returns:
        Dict[str, Dict[str, str]]: A dictionary containing the stored results.
    """
    results = {}
    results[test_case] = {"response": response, "evaluation": evaluation}
    return results


def parse_results_for_file(
    results: Dict[str, Dict[str, str]],
    test_case: str,
    prompt_template: str,
    response: str,
) -> Dict[str, Union[str, Dict[str, str]]]:
    """
    Parses the results for a file.

    Args:
        results (Dict[str, Dict[str, str]]): A dictionary containing the results for each test case.
        test_case (str): The test case for which to parse the results.
        prompt_template (str): The prompt template used for the test case.
        response (str): The response for the test case.

    Returns:
        Dict[str, Any]: A dictionary containing the parsed results, including the prompt template,
        raw response, parsed response, and parsed evaluation.
    """
    parsed_response = parse_xml_content(results[test_case]["response"])
    parsed_evaluation = parse_xml_content(
        results[test_case]["evaluation"], ["EVALUATION_SCRATCHPAD", "EVALUATION_RESULT"]
    )
    return {
        "prompt_template": prompt_template,
        "raw_response": response,
        "parsed_response": parsed_response,
        "parsed_evaluation": parsed_evaluation,
    }
