# Imports
from dotenv import load_dotenv
import os
import json
import re
from custom_printer import print_info, print_success, print_warning, print_error
import xml.etree.ElementTree as ET
from anthropic import Anthropic

# Initialize Anthropics API
anthropic = Anthropic()


# Function to load configuration
def load_configuration():
    load_dotenv()
    return os.getenv("ANTHROPIC_API_KEY")


# Function to prompt user for prompt description
def prompt_user():
    newline = "\n"
    print_info(
        f"{newline * 20}*** This tool can help you craft effective prompts for Claude! ***"
    )
    print_info(
        f"\nEnter some high-level info about what you want Claude to do.\nNote: It may be helpful if you start off by thinking 'This prompt should guide Claude to...' before typing your prompt description.\nClaude will then attempt to create and self-evaluate a prompt against generated test cases."
    )
    print_info("\nPress '0' to enter your own prompt description, or choose a preset:")
    # List of pre-defined prompt options
    prompt_options = {
        "0": "Enter your own custom prompt description.",
        "1": "Redact personally identifiable information (PII) from a given text with 'XXX' and return the redacted text.",
        "2": "Solve a specific reasoning question.",
        "3": "Extract phone numbers from a text and put them into a standard format.",
        "4": "Identify and list all first and last names from a given text.",
        "5": "Compose a haiku on a specified topic.",
        "6": "Act as a helpful chatbot for home-office IT issues. Answer user questions using LLM general knowledge.",
        "7": "Act as a virtual customer service agent for Anthropic with access to an FAQ document and answering a user question.",
        "8": "Create a short rap about a specified inanimate object.",
        "9": "Organize information from a student info text file into JSON with keys 'name', 'grade', 'gpa', 'major'.",
    }

    # Display the options
    for key, value in prompt_options.items():
        print_info(f"{key}. {value}")

    # User input for selecting or entering a template
    user_input = input("\nPlease enter the number of your choice: ")

    # Process the user input
    if user_input in prompt_options:
        if user_input == "0":
            custom_prompt = input("Enter your custom prompt description: ")
            print_info(f"\nCustom prompt description entered: {custom_prompt}")
            goal = custom_prompt
            # Here, you can add functionality to handle the custom prompt
        else:
            print_info(f"\nYou have selected: {prompt_options[user_input]}")
            goal = prompt_options[user_input]
            # Here, you can add functionality to execute the selected pre-defined option
    else:
        print_info(
            "\nInvalid selection. Please enter a number from the list above or type '7' for a custom prompt."
        )
    goal = "The prompt should guide the LLM to: " + goal
    return goal


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


# Function to generate prompts
def generate_prompt(prompt_description, failed_eval_results):
    if failed_eval_results:
        print_info(f"\n*** Updating prompt... ***")
        # If there are failed evaluation results, build string that includes them
        failed_prompt = []
        failed_inputs = []
        failed_responses = []
        failed_evaluations = []
        test_cases_and_evaluations = ""
        for i, failed_eval in enumerate(failed_eval_results):
            failed_prompt.append(failed_eval_results[failed_eval]["prompt"])
            failed_inputs.append(failed_eval_results[failed_eval]["input"])
            failed_responses.append(failed_eval_results[failed_eval]["response"])
            failed_evaluations.append(failed_eval_results[failed_eval]["evaluation"])
            if i == 0:
                test_cases_and_evaluations += f"<Original_Prompt>\n{failed_eval_results[failed_eval]['prompt']}\n</Original_Prompt>\n"
            test_cases_and_evaluations += f"<Test_Case_{i+1}>\n<Input{i+1}>\n{failed_eval_results[failed_eval]['input']}\n</Input{i+1}>\n<Response_{i+1}>\n{failed_eval_results[failed_eval]['response']}\n</Response_{i+1}>\n<Evaluation_{i+1}>\n{failed_eval_results[failed_eval]['evaluation']}\n</Evaluation_{i+1}>\n</Test_Case_{i+1}>"

        prompt_generation_prompt = f"""\n\nHuman: You are an experienced prompt engineer. Your task is to improve an existing LLM prompt in order to elicit an LLM to achieve the specified goal and/or assumes the specified role. The prompt should adherence to best-practices, and produce the best possible likelihood of success. You will be provided with an existing prompt, test cases that failed, and evaluations for those test cases. You will improve the prompt to address the failed test cases and evaluations.

        Follow this procedure to generate the prompt:
        1. Read the prompt description carefully, focusing on its intent, goal, and intended functionality it is designed to elicit from the LLM. Document your understanding of the prompt description and brainstorm in <prompt_generation_scratchpad></prompt_generation_scratchpad> XML tags.
        2. Read the failed inputs, responses, and evaluations carefully. Document your understanding of the failed inputs, responses, and evaluations in <lessons_learned></lessons_learned> XML tags.
        3. Using best practices, including organizing information in XML tags when necessary, generate a new iteration of the prompt that incorporates lessons learned.
        4. Write your new prompt in <generated_prompt></generated_prompt> XML tags. The updated prompt must continue to take the same input variable(s) or text as the original prompt. Your prompt must start with '\n\nH:' and end with '\n\nA:' to ensure proper formatting.
        
        Generate a prompt based on the following prompt description. Read it carefully:
        Prompt Description: ```{prompt_description}```
        
        Here are the test cases and evaluations. Read them carefully:
        <test_cases_and_evaluations>
        {test_cases_and_evaluations}
        </test_cases_and_evaluations>
        
        Remember to put your new prompt within <generated_prompt></generated_prompt> XML tags. Think step by step and double check your prompt against the procedure and failed input(s) before it's finalized.

        Assistant: """
    else:
        print_info(f"\n*** Generating an initial prompt... ***")
        prompt_generation_prompt = f"""\n\nHuman: You are an experienced prompt engineer. Your task is to read a prompt description written by a user and craft a prompt that will successfully elicit an LLM to achieve the specified goal or task. The prompt should adherence to best-practices, and produce the best possible likelihood of success.

        Follow this procedure to generate the prompt:
        1. Read the prompt description carefully, focusing on its intent, goal, and intended functionality it is designed to elicit from the LLM. Document your understanding of the prompt description and brainstorm in <prompt_generation_scratchpad></prompt_generation_scratchpad> XML tags.
        2. Using best practices, including organizing information in XML tags when necessary, generate a high-quality, detailed, and thoughtful prompt.
        3. Write your prompt in <generated_prompt></generated_prompt> XML tags. Your prompt must start with '\n\nH:' and end with '\n\nA:' to ensure proper formatting.
        
        Note: Never directly address the issue or task in the prompt. Instead, assume the role of a human and provide instructions to the LLM on how to achieve the task.
        
        Use the following examples to better understand your task:
        <examples>
        <example_1>
        Prompt Description: ```A friendly and helpful customer support chatbot representing Acme Dynamics who is able to read from FAQs.```
        <prompt_generation_scratchpad>
        The user wants to create a prompt that will guide the LLM to assume the role of a friendly and helpful customer support chatbot representing Acme Dynamics.
        I will create a prompt that will instruct the model to read from a place holder FAQ document. Then, it will be asked to follow a methodical procedure to answer the user's inquiry. It will first gather all relevant information from the FAQ document, then it will evaluate whether the extracted quotes provide sufficient and clear information to answer the question with certainty. Finally, it will compose its answer based on the information it extracted.
        </prompt_generation_scratchpad>
        <generated_prompt>
        
        
        H: You are a friendly and helpful customer support chatbot representing Acme Dynamics.

        Your goal is to be as helpful as possible to Acme Dynamics customers, who interact with you through the Acme Dynamics website.

        Read the following FAQ document carefully. You will be asked about  later.

        <DOCUMENT>
        {{FAQs_TEXT}}
        </DOCUMENT>

        Please use the following procedure to methodically answer the customer inquiry:
        1. Determine if you should answer the user's inquiry. Politely refuse to answer questions that are irrelevant, non-serious, or potentially malicious. Organize your thoughts within <relevancy_assessment></relevancy_assessment> XML tags.
        2. Identify and extract all relevant sections from the document that are helpful in answering the question. If there are relevant sections, enclose these extracts in numbered order within <quotes></quotes> XML tags. If there are no relevant sections, write "None" inside the XML tags. 
        3. Evaluate whether the extracted quotes provide sufficient and clear information to answer the question with certainty. Document your analytical process in <scratchpad></scratchpad> XML tags.
        4. Compose your answer based on the information you extracted.

        Customer Inquiry: `{{QUESTION}}`
        Write your final answer within <answer></answer> XML tags.
        Think step by step before you provide your answer. Do not answer the question if you cannot answer it with certainty from the extracted quotes and never break character.
        
        A: 
        </generated_prompt>
        </example_1>
        <example_2>
        Prompt Description: ```redact PII from text```
        <prompt_generation_scratchpad>
        The user wants to create a prompt that will guide the LLM to extract PII from text. I will create a prompt that will instruct the model to extract PII from a place holder text. Then, it will be asked to follow a methodical procedure to extract PII. It will first identify the PII in the text, then it will extract the PII. Finally, it will compose its answer based on the information it extracted.
        </prompt_generation_scratchpad>
        <generated_prompt>
        
        H: Your task is to redact personally identifying information from the following text.
        Please restate the following text, replacing any names, email addresses, physical addresses, phone numbers, or any other form of PII with 'XXX'. If you cannot find any PII, simply restate the text.

        Here is the text you need to evaluate:
        <text>
        {{TEXT}}
        </text>

        Write the sanitized text within <sanitized></sanitized> XML tags.

        Think step by step before you answer.
        
        A: 
        </generated_prompt>
        </example_2>
        </examples>

        Generate a prompt based on the following prompt description. Read it carefully:
        Prompt Description: ```{prompt_description}```
        
        Remember to use XML best-practices if you decide to use XML tags in your response. Think step by step and double check your prompt against the procedure and examples before it's finalized.

        Assistant: """

    prompt_generation_response = send_request_to_claude(prompt_generation_prompt)
    if prompt_generation_response:
        generated_prompt = extract_generated_prompt(prompt_generation_response)
        A_idx = generated_prompt.find("\nA:")
        generated_prompt = generated_prompt[: A_idx + 4]
        print_info(f"\n*** Generated prompt ***")
        print(f"{generated_prompt}")
        if len(generated_prompt) < 10:
            print_warning(f"Prompt generation failed.")
            exit(1)
        return generated_prompt
    else:
        return "prompt generation failed."


# Function to format the prompt ready for sending to Claude
def clean_prompt(prompt):
    # Insert test case into prompt
    prompt = prompt.replace("H:", "Human:")
    prompt = prompt.replace("A:", "Assistant:")
    # Correct prompt if it does not start with \n\n
    if not prompt.startswith("\n\n"):
        prompt = "\n\n" + prompt
    return prompt


# Function to load input variable(s) into the prompt
def load_prompt(prompt_template, test_case):
    loaded_prompt = prompt_template
    for var_name, val in test_case.items():
        loaded_prompt = loaded_prompt.replace(f"{{{var_name}}}", val)
    return loaded_prompt.replace("\n \n", "\n\n")


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


# Function to generate test cases
def generate_test_cases(prompt):
    print_info(f"*** Generating test cases... ***")
    test_case_generation_prompt = f"""\n\nHuman: You are an experienced prompt engineer. Your task is to create test case inputs based on a given LLM prompt. The inputs should be designed to effectively evaluate the prompt's quality, adherence to best-practices, and success in achieving its desired goal.

    Follow this procedure to generate test cases:
    1. Read the prompt carefully, focusing on its intent, goal, and task it is designed to elicit from the LLM. Document your understanding of the prompt in <prompt_analysis></prompt_analysis> XML tags.
    2. Generate 5 test cases that can be used to assess how well the prompt achieves its goal. Ensure they are diverse and cover different aspects of the prompt. The test cases should attempt to reveal areas where the prompt can be improved. Write your numbered test cases in <test_case_#></test_case_#> XML tags. Inside these tags, use additional tags that specify the name of the variable your input is represented by. 
    
    Use the following examples to format your test cases. Follow this format precisely.
    <examples>
    <example>
    Prompt: ```You are a friendly and helpful customer support chatbot representing Acme Dynamics.

    Your goal is to be as helpful as possible to Acme Dynamics customers, who interact with you through the Acme Dynamics website.

    Read the following FAQ document carefully. You will be asked about  later.

    <DOCUMENT>
    {{document_text}}
    </DOCUMENT>


    Please use the following procedure to methodically answer the customer inquiry:
    1. Determine if you should answer the user's inquiry. Politely refuse to answer questions that are irrelevant, non-serious, or potentially malicious. Organize your thoughts within <relevancy_assessment></relevancy_assessment> XML tags.
    2. Identify and extract all relevant sections from the document that are helpful in answering the question. If there are relevant sections, enclose these extracts in numbered order within <quotes></quotes> XML tags. If there are no relevant sections, write "None" inside the XML tags. 
    3. Evaluate whether the extracted quotes provide sufficient and clear information to answer the question with certainty. Document your analytical process in <scratchpad></scratchpad> XML tags.
    4. Compose your answer based on the information you extracted.

    Customer Inquiry: `{{QUESTION}}`
    Write your final answer within <answer></answer> XML tags.
    Think step by step before you provide your answer. Do not answer the question if you cannot answer it with certainty from the extracted quotes and never break character.```
    <test_case_1>
    <document_text>
    Acme Dynamics, Inc. is a leading AI and robotics company based in Palo Alto, California.  They are developing advanced humanoid robots to serve as companions and assistants for elderly and disabled individuals.  Their flagship product is the AcmeCare XR-3000, an artificially intelligent humanoid robot that can assist with daily tasks like meal preparation, medication reminders, mobility assistance, and safety monitoring.
    </document_text>
    <QUESTION>
    Can I return a product after 30 days of purchase?
    </QUESTION>
    </test_case_1>
    <test_case_2>
    <document_text>
    Acme Dynamics, Inc. is a leading AI and robotics company based in Palo Alto, California.  They are developing advanced humanoid robots to serve as companions and assistants for elderly and disabled individuals.  Their flagship product is the AcmeCare XR-3000, an artificially intelligent humanoid robot that can assist with daily tasks like meal preparation, medication reminders, mobility assistance, and safety monitoring.
    </document_text>
    <QUESTION>
    What does Acme Dynamics do?
    </QUESTION>
    </test_case_2>
    ...
    <test_case_10>
    <document_text>
    Acme Dynamics, Inc. is a leading AI and robotics company based in Palo Alto, California.  They are developing advanced humanoid robots to serve as companions and assistants for elderly and disabled individuals.  Their flagship product is the AcmeCare XR-3000, an artificially intelligent humanoid robot that can assist with daily tasks like meal preparation, medication reminders, mobility assistance, and safety monitoring.
    </document_text>
    <QUESTION>
    Where is the company based?
    </QUESTION>
    </test_case_10>
    </example>
    <example>
    Prompt: ```I will provide you with a text inside <text> XML tags. Read through the text carefully and identify all full names that include both first and last names. 

    Extract just the first and last names into a list format, with each full name on a separate line inside <names> XML tags. Only include the first and last names - do not include any other information from the text.

    Here is the text:

    <text>
    {{TEXT}} 
    </text>

    Please provide the list of extracted names here:

    <names>

    </names>

    Think step-by-step and double check your work. Do not include anything other than the first and last names extracted from the provided text.```
    <test_case_1>
    <TEXT>
    Steve Jobs was a key member of Apple, especially in its early days, and Tim Cook is the current CEO. 
    </TEXT>
    </test_case_1>
    <test_case_2>
    <TEXT>
    Mr. Jones and his student, Tim Smith, are working on a new project together.
    </TEXT>
    </test_case_2>
    ...
    <test_case_10>
    <TEXT>
    I want to know the names of all the people who work at Acme Dynamics.
    </TEXT>
    </test_case_10>
    </example>
    </examples>

    Here is the prompt for which you need to generate test cases. Read it carefully:
    <prompt_to_generate_test_cases_for>
    {prompt}
    </prompt_to_generate_test_cases_for>
    
    Remember to match the format of the example exactly. Ensure the XML tags you use match the variable name(s) in the prompt exactly. For example, if the prompt contains <text>{{TEXT}}</text>, your test input must be written within <TEXT></TEXT> XML tags. 
    
    Double check your test cases against the procedure and examples before you answer.

    Assistant: """

    test_cases_response = send_request_to_claude(test_case_generation_prompt)
    if test_cases_response:
        test_cases = extract_test_cases(test_cases_response)
        print_info(f"*** Generated {len(test_cases)} test cases. ***")
        return test_cases
    else:
        return "test case generation failed."


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


# Function to identify variable placeholders in the prompt Claude generated
def identify_placeholders(prompt):
    placeholder_identification_prompt = f"""\n\nHuman: Please follow these steps to extract any variable placeholders in the text:

    1. Carefully read the text within the <text> tags.
    2. Look for variable placeholders, which are usually surrounded by curly braces. 
    3. Extract the text between the curly braces. 
    4. Make a list containing each unique variable placeholder name you found.
    5. Put the list of placeholder names within <placeholders> XML tags.
    
    If there are no variable placeholders, write "None" inside the XML tags.

    Use the following examples to strengthen your understanding of the task:
    <examples>
    <example>
    <text>
    Hello, my name is {{NAME}}. I am {{AGE}} years old.
    </text>

    <placeholders>
    {{NAME}}
    {{AGE}}
    </placeholders>
    </example>
    <example>
    <text>
    Please read the following document carefully. You will be asked about it later.
    <doc>
    {{FAQ_document}}
    </doc>
    </text>
    
    <placeholders>
    {{FAQ_document}}
    </placeholders>
    </example>
    </examples>

    Here is the text you need to process. Read it carefully:
    <text>
    {prompt}
    </text>
    
    Think step by step before you answer.

    Assistant: """

    placeholder_identification_response = send_request_to_claude(
        placeholder_identification_prompt
    )
    if placeholder_identification_response:
        return extract_variable_placeholders(placeholder_identification_response)
    else:
        return "variable placeholder identification failed."


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


# Function to send request to Claude API
def send_request_to_claude(prompt):
    completion = anthropic.completions.create(
        prompt=prompt,
        # model="claude-v1",
        # model="claude-v1.3",
        # model="claude-2",
        model="claude-2.1",
        max_tokens_to_sample=100000,
        temperature=0.05,
    )
    response = completion.completion
    stop_reason = completion.stop_reason
    stop_sequence = completion.stop
    if stop_reason != "stop_sequence":
        print_warning(
            f"Completion stopped unexpectedly. Reason: '{stop_reason}' - Stop Sequence: '{stop_sequence}'"
        )
    # print_info(completion)
    return response


# Function to evaluate Claude's response
def evaluate_response(prompt_to_eval, response_to_eval):
    evaluation_prompt = f"""\n\nHuman: Your task is to evaluate the adherence of a response to the associated prompt. Failure of the response to adhere perfectly to the instructions in the prompt can indicate flawed prompt engineering.
    
    Here is the prompt you need to evaluate. Read it carefully:
    <prompt_to_eval>
    {prompt_to_eval}
    </prompt_to_eval>
    
    Here is the response you need to evaluate. Read it carefully:
    <response_to_eval>
    {response_to_eval}
    </response_to_eval>

    Follow this procedure to perform your evaluation:
    1. Read the prompt carefully, focusing on its intent, format, and the specific task it is designed to elicit from the LLM.
    2. Carefully assess the response's adherence to the prompt. Clearly document your step by step analytical process, including any deviations, hallucinations, or any other undesired behavior, however minor, from the prompt's specified instructions in <evaluation_scratchpad></evaluation_scratchpad> XML tags.
    3. Score the prompt's performance in generating the expected response. Mark it as 'PASS' if the response aligns perfectly with the instructions and the LLM behaves optimally. Mark it as 'FAIL' otherwise. Write your determination in <evaluation_result></evaluation_result> XML tags.

    Remember, the prompt you are evaluating was asked of another LLM, and the response was created by that same other LLM. Your job is to evaluate the performance. Think step by step before you answer.
    
    Assistant: 
    """

    evaluation_response = send_request_to_claude(evaluation_prompt)
    if evaluation_response:
        return evaluation_response
    else:
        return "Evaluation failed."


# Function to extract evaluation result from XML tags
def extract_eval_result(evaluation):
    eval_start_idx = evaluation.find("<evaluation_result>")
    eval_end_idx = evaluation.find("</evaluation_result>")
    eval_result = evaluation[eval_start_idx + 19 : eval_end_idx].replace("\n", "")
    return eval_result.strip()


# Function to save results to a JSON file
def save_results_to_json(results, filename="results.json"):
    with open(filename, "w") as file:
        json.dump(results, file, indent=4)


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


# Function to preprocess tags to replace spaces
def preprocess_tags(xml_string):
    # Replace spaces in tag names with a unique placeholder
    cleaned_xml_string = re.sub(
        r"(<\s*/?\s*)([^<>]+)(\s*>|\s+[^<>]*>)",
        lambda m: f"{m.group(1)}{m.group(2).replace(' ', '_SPACE_')}{m.group(3)}",
        xml_string,
    )
    return cleaned_xml_string


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
        return llm_output


# Main execution flow
def main():
    anthropic_api_key = load_configuration()
    if not anthropic_api_key:
        print_error("No API key found.")
        return

    goal = prompt_user()
    input_vars_detected = False
    combined_results = []
    test_results = {}
    first_iteration = True
    failed_test_cases = False
    while True:  # Loop until all test cases pass
        failed_test_cases = False
        # Generate initial prompt
        prompt_template = generate_prompt(goal, test_results)
        cleaned_prompt_template = clean_prompt(
            prompt_template
        )  # Only used to print the final prompt
        # Identify variable placeholders
        placeholder_names = identify_placeholders(prompt_template)

        if placeholder_names[0] != "None":
            input_vars_detected = True

        # Generate test cases for the prompt
        if first_iteration and input_vars_detected:
            test_case_retry = True
            while (
                test_case_retry
            ):  # Loop until placeholder names match test case input variable names
                # Use the same test cases across prompt iterations
                test_cases = generate_test_cases(prompt_template)
                # Check if test case input variable names match placeholder names
                test_cases, test_case_retry = update_variable_names(
                    test_cases, placeholder_names
                )

        if input_vars_detected:
            results = {}
            # Include XML parsing in results
            parsed_results = {}
            test_results = {}
            skip_test_case = False
            for test_case in test_cases:
                print_info(f"\n\n*** Evaluating input ***")
                print(f"{test_cases[test_case]}")
                for val in test_cases[test_case].values():
                    if val is None or val == "None":
                        skip_test_case = True
                        break
                if skip_test_case:
                    print_warning(
                        f"Skipping test case {test_case} because it contains invalid input."
                    )
                    skip_test_case = False
                    continue
                # Load prompt with input from the test case
                loaded_prompt = load_prompt(prompt_template, test_cases[test_case])

                # Get prompt ready for Claude
                loaded_prompt = clean_prompt(loaded_prompt)

                # Send request and get response
                response = send_request_to_claude(loaded_prompt)
                print_info(f"\n*** Response received ***")
                print(f"{response}")

                # Evaluate response
                evaluation = evaluate_response(loaded_prompt, response)

                print_info(f"\n*** Self-evaluation result ***")
                # Extract the result
                eval_result = extract_eval_result(evaluation)
                if eval_result == "FAIL":
                    print_warning(f"{eval_result}")
                    failed_test_cases = True
                elif eval_result == "PASS":
                    print_success(f"{eval_result}")
                else:
                    print_info("Evaluation result not found.")
                    # For now, treat as a pass #TODO: Handle this case

                # Store test results for iterative improvement
                test_results[test_case] = {
                    "prompt": prompt_template,
                    "input": test_cases[test_case],
                    "response": response,
                    "evaluation": evaluation,
                }

                # For results file save
                results[test_case] = {"response": response, "evaluation": evaluation}
                raw_response = response
                parsed_response = parse_xml_content(results[test_case]["response"])
                parsed_evaluation = parse_xml_content(
                    results[test_case]["evaluation"],
                    ["evaluation_scratchpad", "evaluation_result"],
                )
                parsed_results[test_case] = {
                    "prompt_template": prompt_template,
                    "prompt_loaded": loaded_prompt,
                    "raw_response": raw_response,
                    "parsed_response": parsed_response,
                    "parsed_evaluation": parsed_evaluation,
                }
                combined_results.append(parsed_results[test_case])

            # Save final results
            save_results_to_json(combined_results)
            if failed_test_cases:
                print_warning(f"*** Some test cases failed. ***")
                first_iteration = False
            else:
                print_success(f"\n*** All test cases passed! ***")
                break
        else:  # No input variables detected
            cleaned_prompt_template = clean_prompt(prompt_template)
            # Send request and get response
            response = send_request_to_claude(cleaned_prompt_template)
            # Evaluate response
            evaluation = evaluate_response(cleaned_prompt_template, response)

            print_info(f"\n*** Self-evaluation result ***")
            # Extract the result
            eval_result = extract_eval_result(evaluation)
            if eval_result == "FAIL":
                print_warning(f"\n*** Evaluation failed. ***")
                failed_test_cases = True
            elif eval_result == "PASS":
                print_success(f"\n*** Evaluation passed! ***")
                break
            else:
                print_info("Evaluation result not found.")
                break
                # For now, treat as a pass #TODO: Handle this case

            # Store test results for iterative improvement
            test_results[0] = {
                "prompt": cleaned_prompt_template,
                "input": "None",
                "response": response,
                "evaluation": evaluation,
            }

    print_success(f"\nGENERATED PROMPT:")
    print(f"{cleaned_prompt_template}")
    print_success(f"\n\n*** Prompt generation and evaluation complete. ***")
    print_success(f"*** Info saved to results.json ***")


if __name__ == "__main__":
    main()
