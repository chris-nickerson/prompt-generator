import re
import xml.etree.ElementTree as ET

from utils import print_error, print_warning, print_info, print_success


# Function to extract generated prompt from XML tags
def extract_generated_prompt(response):
    try:
        # Using regular expression to find content between <generated_prompt> tags
        match = re.search(
            r"<generated_prompt>(.*?)</generated_prompt>", response, re.DOTALL
        )
        if match:
            # Extracting and returning the text found between the tags
            return match.group(1).strip()
        else:
            return "No generated prompt  XML tags found."
    except Exception as e:
        print_error(f"Error while extracting generated prompt: {e}")
        exit(1)


# Function to format the prompt ready for sending to Claude
def clean_prompt(prompt):
    # Insert test case into prompt
    prompt = prompt.replace("H:", "Human:")
    prompt = prompt.replace("A:", "Assistant:")
    # Correct prompt if it does not start with \n\n
    if not prompt.startswith("\n\n"):
        prompt = "\n\n" + prompt
    return prompt


# Function to extract variable placeholders from XML tags
def extract_variable_placeholders(response):
    try:
        # Using regular expression to find content between <generated_prompt> tags
        match = re.search(r"<placeholders>(.*?)</placeholders>", response, re.DOTALL)
        if match:
            # Extracting the text found between the tags
            text = match.group(1).strip()
            # Splitting the text into a list of placeholder names
            return text.split("\n")
        else:
            return "No variable placeholder XML tags found."
    except Exception as e:
        print_error(f"Error while extracting generated prompt: {e}")
        exit(1)


# Function to preprocess tags to replace spaces
def preprocess_tags(xml_string):
    # Replace spaces in tag names with a unique placeholder
    cleaned_xml_string = re.sub(
        r"(<\s*/?\s*)([^<>]+)(\s*>|\s+[^<>]*>)",
        lambda m: f"{m.group(1)}{m.group(2).replace(' ', '_SPACE_')}{m.group(3)}",
        xml_string,
    )
    return cleaned_xml_string


# Function to escape tags that are not to be parsed
def escape_ignored_tags(llm_output, tags_to_parse):
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


# Function to unescape characters in the parsed data
def unescape_characters(parsed_data):
    for key, value in parsed_data.items():
        if value is not None:
            parsed_data[key] = value.replace("&lt;", "<").replace("&gt;", ">")
    return parsed_data


# Function to postprocess tags to restore spaces
def postprocess_tags(parsed_data):
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


# Function to parse XML content
def parse_xml_content(llm_output, tags_to_parse=None):
    llm_output = llm_output.strip().replace("\n\n", "\n")
    # Preprocess the tags to replace spaces
    llm_output_preprocessed = preprocess_tags(llm_output)
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
        # Unescape characters before returning
        parsed_data = unescape_characters(parsed_data)
        # Postprocess tags to restore spaces
        parsed_data = postprocess_tags(parsed_data)
        return parsed_data
    except ET.ParseError as e:
        # print_info(f"Error parsing XML from LLM output: {e}")
        print_info("Error parsing XML from LLM output. Returning raw llm_output...")
        return "parsing failed:" + llm_output


# Function to extract test cases from XML tags
def extract_test_cases(response):
    response = response.replace("\n\n", "\n")
    try:
        test_cases = {}

        # Using regex to find all test case tags in the format <test_case_X>
        test_case_tags = re.findall(r"<test_case_(\d+)>", response)

        for tag in test_case_tags:
            # Constructing the tag name for the current test case
            test_case_tag = f"test_case_{tag}"

            # Using regular expression to find content between <test_case_X> tags
            match = re.search(
                rf"<{test_case_tag}>(.*?)</{test_case_tag}>", response, re.DOTALL
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
        exit(1)


# Function to update variable names in test cases to match placeholder names
def update_variable_names(test_cases, placeholder_names, test_case_retry=True):
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
                # Unfixable mismatch found, need to regenerate test cases
                print_warning(
                    f"Placeholder name '{placeholder}' does not match test case input variable name '{test_case_name}'. Regenerating test cases..."
                )
                mismatch_found = True
                inner_dict = {}
                break  # Exit the loop for unfixable mismatch

    # If no mismatch was found, exit the while loop
    if not mismatch_found:
        test_case_retry = False
        return test_cases, test_case_retry
    else:
        return inner_dict, test_case_retry


# Function to load input variable(s) into the prompt
def load_prompt(prompt_template, test_case):
    loaded_prompt = prompt_template
    for var_name, val in test_case.items():
        loaded_prompt = loaded_prompt.replace(f"{{{var_name}}}", val)
    return loaded_prompt.replace("\n \n", "\n\n")


# Function to extract evaluation result from XML tags
def extract_eval_result(evaluation):
    eval_start_idx = evaluation.find("<evaluation_result>")
    eval_end_idx = evaluation.find("</evaluation_result>")
    eval_result = evaluation[eval_start_idx + 19 : eval_end_idx].replace("\n", "")
    return eval_result.strip()


# Function to determine test case result
def handle_eval_result(tc_name, eval_result):
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
        print_info("Evaluation result not found.")
        return False  # Default to no failure


# Function to update the test results with each test case's data
def update_test_results(
    test_case_key, prompt_template, test_case_input, response, evaluation
):
    test_result = {}
    test_result[test_case_key] = {
        "prompt": prompt_template,
        "input": test_case_input,
        "response": response,
        "evaluation": evaluation,
    }
    return test_result


# Function to store results for saving to a file
def store_results_for_file(test_case, response, evaluation):
    results = {}
    results[test_case] = {"response": response, "evaluation": evaluation}
    return results


# Function to parse results for saving to a file
def parse_results_for_file(results, test_case, prompt_template, response):
    parsed_response = parse_xml_content(results[test_case]["response"])
    parsed_evaluation = parse_xml_content(
        results[test_case]["evaluation"], ["evaluation_scratchpad", "evaluation_result"]
    )
    return {
        "prompt_template": prompt_template,
        "raw_response": response,
        "parsed_response": parsed_response,
        "parsed_evaluation": parsed_evaluation,
    }
