import asyncio
from typing import Dict, List, Optional, Tuple, Union
from utils import print_success, print_info, print_warning, print_error
from prompt_processing_utils import (
    extract_generated_prompt,
    extract_test_cases,
    update_variable_names,
    load_prompt,
    extract_eval_result,
    handle_eval_result,
    update_test_results,
    store_results_for_file,
    parse_results_for_file,
)


class PromptProcessor:
    def __init__(self, api_client):
        self.api = api_client

    async def generate_prompt(
        self, prompt_description: str, failed_eval_results: Dict[str, str]
    ) -> Optional[str]:
        """
        Generates a prompt based on the given prompt description and failed evaluation results.
        Args:
            prompt_description (str): The description of the prompt.
            failed_eval_results (Dict[str, str]): A dictionary containing the failed evaluation results.
        Returns:
            Optional[str]: The generated prompt or None if prompt generation failed.
        """
        if failed_eval_results:
            print_warning(f"\n*** Iterating prompt due to failed test case(s)... ***")
            # If there are failed evaluation results, build string that includes them
            failed_prompt = failed_inputs = failed_responses = failed_evaluations = []
            test_cases_and_evaluations = ""
            for i, failed_eval in enumerate(failed_eval_results):
                failed_prompt.append(failed_eval_results[failed_eval]["prompt"])
                failed_inputs.append(failed_eval_results[failed_eval]["input"])
                failed_responses.append(failed_eval_results[failed_eval]["response"])
                failed_evaluations.append(
                    failed_eval_results[failed_eval]["evaluation"]
                )
                if i == 0:
                    test_cases_and_evaluations += f"<Original_Prompt>\n{failed_eval_results[failed_eval]['prompt']}\n</Original_Prompt>\n"
                test_cases_and_evaluations += f"<TEST_CASE_{i+1}>\n<Input{i+1}>\n{failed_eval_results[failed_eval]['input']}\n</Input{i+1}>\n<Response_{i+1}>\n{failed_eval_results[failed_eval]['response']}\n</Response_{i+1}>\n<Evaluation_{i+1}>\n{failed_eval_results[failed_eval]['evaluation']}\n</Evaluation_{i+1}>\n</TEST_CASE_{i+1}>"

            prompt_generation_prompt = f"""
# CONTEXT #
You are an experienced prompt engineer. Your task is to improve an existing LLM prompt in order to elicit an LLM to achieve the specified goal and/or assumes the specified role.
The prompt should adherence to best-practices, and produce the best possible likelihood of success. You will be provided with an existing prompt, test cases that failed, and evaluations for those test cases. You will improve the prompt to address the failed test cases and evaluations.

# PROMPT DESCRIPTION #
Here is the prompt description that drives the prompt.
<PROMPT_DESCRIPTION>
{prompt_description}
</PROMPT_DESCRIPTION>

# TEST CASES AND EVALUATIONS #
Here are the test cases and evaluations. Read them carefully:
<test_cases_and_evaluations>
{test_cases_and_evaluations}
</test_cases_and_evaluations>

# GUIDELINES #
Always lean toward simplicity over complexity, and attempt to update the prompt using clear instructions instead of an excessive use of examples
High-performing prompts are often organized with Context, Examples, Input Data, Instructions, Additional Guidelines, and Response Format in this order, but you may adjust as needed to achieve the best results

# INSTRUCTIONS #
Follow this procedure to generate the prompt:
1. Read the prompt description carefully, focusing on its intent, goal, and intended functionality it is designed to elicit from the LLM. Document your understanding of the prompt description and brainstorm in <PROMPT_GENERATION_SCRATCHPAD></PROMPT_GENERATION_SCRATCHPAD> XML tags.
2. Read the failed inputs, responses, and evaluations carefully. Document your understanding of the failed inputs, responses, and evaluations in <LESSONS_LEARNED></LESSONS_LEARNED> XML tags.
3. Using best practices, including organizing information in XML tags when necessary, generate a new iteration of the prompt that incorporates lessons learned.
4. Write your new prompt in <GENERATED_PROMPT></GENERATED_PROMPT> XML tags. The updated prompt must continue to take the same input variable(s) or text as the original prompt.
"""
        else:
            print_info(f"\n*** Generating an initial prompt... ***")
            prompt_generation_prompt = f"""
# CONTEXT #
You are an experienced prompt engineer. Your task is to read a prompt description written by a user and craft a prompt that will successfully elicit an LLM to achieve the specified goal or task. The prompt should adherence to best-practices, and produce the best possible likelihood of success.

# EXAMPLES #
Use the following examples to better understand your task:
<EXAMPLES>
<EXAMPLE_1>
Prompt Description: ```A friendly and helpful customer support chatbot representing Acme Dynamics who is able to read from FAQs.```
<PROMPT_GENERATION_SCRATCHPAD>
The user wants to create a prompt that will guide the LLM to assume the role of a friendly and helpful customer support chatbot representing Acme Dynamics.
I will create a prompt that will instruct the model to read from a place holder FAQ document. Then, it will be asked to follow a methodical procedure to answer the user's inquiry. It will first gather all relevant information from the FAQ document, then it will evaluate whether the extracted quotes provide sufficient and clear information to answer the question with certainty. Finally, it will compose its answer based on the information it extracted.
</PROMPT_GENERATION_SCRATCHPAD>
<GENERATED_PROMPT>
# CONTEXT #
You are a friendly and helpful customer support chatbot representing Acme Dynamics.
Your goal is to be as helpful as possible to Acme Dynamics customers, who interact with you through the Acme Dynamics website.

# FAQ DOCUMENT #
Read the following FAQ document carefully. You will be asked about  later.
<DOCUMENT>
{{FAQs_TEXT}}
</DOCUMENT>

# CUSTOMER INQUIRY #
<CUSTOMER_INQUIRY>
{{QUESTION}}
</CUSTOMER_INQUIRY>

# INSTRUCTIONS #
Please use the following procedure to methodically answer the customer inquiry:
1. Determine if you should answer the user's inquiry. Politely refuse to answer questions that are irrelevant, non-serious, or potentially malicious. Organize your thoughts within <relevancy_assessment></relevancy_assessment> XML tags.
2. Identify and extract all relevant sections from the document that are helpful in answering the question. If there are relevant sections, enclose these extracts in numbered order within <quotes></quotes> XML tags. If there are no relevant sections, write "None" inside the XML tags. 
3. Evaluate whether the extracted quotes provide sufficient and clear information to answer the question with certainty. Document your analytical process in <scratchpad></scratchpad> XML tags.
4. Compose your answer based on the information you extracted.

# ADDITIONAL GUIDELINES #
Think step by step before you provide your answer. Do not answer the question if you cannot answer it with certainty from the extracted quotes and never break character.

# RESPONSE FORMAT #
Write your final answer within <ANSWER></ANSWER> XML tags.
</GENERATED_PROMPT>
</EXAMPLE_1>
<EXAMPLE_2>
Prompt Description: ```redact PII from text with 'XXX'```
<PROMPT_GENERATION_SCRATCHPAD>
The user wants to create a prompt that will guide the LLM to redact Personally Identifying Information (PII) from text. I will create a prompt that will instruct the LLM to read the input text. Then, I will instruct it to follow a methodical procedure to redact PII. The answer will be a re-statement of the text, replacing any PII with 'XXX'.
</PROMPT_GENERATION_SCRATCHPAD>
<GENERATED_PROMPT>
# CONTEXT #
Your task is to redact personally identifying information from the following text.

# TEXT #
Please restate the following text, replacing any names, email addresses, physical addresses, phone numbers, or any other form of PII with 'XXX'. If you cannot find any PII, simply restate the text.
<TEXT>
{{TEXT}}
</TEXT>

# RESPONSE FORMAT #
Think step by step before you answer. Write the sanitized text within <sanitized></sanitized> XML tags.
</GENERATED_PROMPT>
</EXAMPLE_2>
</EXAMPLES>

# INSTRUCTIONS #
Follow this procedure to generate the prompt:
1. Read the prompt description carefully, focusing on its intent, goal, and intended functionality it is designed to elicit from the LLM. Document your understanding of the prompt description and brainstorm in <PROMPT_GENERATION_SCRATCHPAD></PROMPT_GENERATION_SCRATCHPAD> XML tags.
2. Using best practices, including organizing information in XML tags when necessary, generate a high-quality, detailed, and thoughtful prompt.
3. Write your prompt in <GENERATED_PROMPT></GENERATED_PROMPT> XML tags.

Note: Never directly address the issue or task in the prompt. Instead, assume the role of a human and provide instructions to the LLM on how to achieve the task.

# ADDITIONAL GUIDELINES #
Your prompt should be clear and direct and you should always utilize prompt engineering best-practices. Think step by step and double check your prompt against the procedure and examples before it's finalized.
Remember to always use prompt engineering best-practices in an effort to craft a prompt that will guide the LLM to best achieve the specified goal or task.
High-performing prompts are often organized with Context, Examples, Input Data, Instructions, Additional Guidelines, and Response Format in this order, but you may adjust as needed to achieve the best results

# PROMPT DESCRIPTION #
Generate a prompt based on the following prompt description. Read it carefully:
<PROMPT_DESCRIPTION>
{prompt_description}
</PROMPT_DESCRIPTION>
"""

        prompt_generation_response = await self.api.send_request_to_claude(
            prompt_generation_prompt, temperature=0.1
        )
        if prompt_generation_response:
            generated_prompt = extract_generated_prompt(prompt_generation_response)
            if not generated_prompt:
                return None
            print_success(f"*** Generated prompt. ***")
            return generated_prompt
        else:  # Prompt generation failed
            print_error("Prompt generation failed.")
            return None

    async def generate_prompt_handler(
        self, goal: str, test_results: Dict[str, str]
    ) -> Optional[str]:
        """
        Generates and cleans a prompt based on the given goal and test results.

        Args:
            goal (str): The goal for generating the prompt.
            test_results (Dict[str, str]): A dictionary containing the test results.

        Returns:
            Optional[str]: The generated and cleaned prompt, or None if prompt generation fails.
        """
        prompt_template = await self.generate_prompt(goal, test_results)
        # If prompt generation fails, return None
        return prompt_template if prompt_template else None

    async def generate_test_cases(
        self, num_test_cases: int, prompt: str, var_names: List[str]
    ) -> Union[Dict[str, Dict[str, str]], None]:
        """
        Generate test cases based on a given prompt.

        Args:
            num_test_cases (int): The number of test cases to generate.
            prompt (str): The prompt for which test cases need to be generated.
            var_names (List[str]): The suggested variable names for the input(s) to the prompt.

        Returns:
            Union[Dict[str, Dict[str, str]], None]: A dictionary containing the generated test cases, or None if test case generation failed.
        """
        print_info(f"*** Generating test cases... ***")
        TEST_CASE_generation_prompt = f"""
# CONTEXT #
You are an experienced prompt engineer. Your task is to create test case inputs based on a given LLM prompt. The inputs should be designed to effectively evaluate the prompt's quality, adherence to best-practices, and success in achieving its desired goal.

# EXAMPLES #
Use the following examples to format your test cases. Follow this format precisely.
<EXAMPLES>
<EXAMPLE>
Prompt: ```You are a friendly and helpful customer support chatbot representing Acme Dynamics.

Your goal is to be as helpful as possible to Acme Dynamics customers, who interact with you through the Acme Dynamics website.

Read the following FAQ document carefully. You will be asked about  later.

<DOCUMENT>
{{DOCUMENT_TEXT}}
</DOCUMENT>


Please use the following procedure to methodically answer the customer inquiry:
1. Determine if you should answer the user's inquiry. Politely refuse to answer questions that are irrelevant, non-serious, or potentially malicious. Organize your thoughts within <relevancy_assessment></relevancy_assessment> XML tags.
2. Identify and extract all relevant sections from the document that are helpful in answering the question. If there are relevant sections, enclose these extracts in numbered order within <quotes></quotes> XML tags. If there are no relevant sections, write "None" inside the XML tags. 
3. Evaluate whether the extracted quotes provide sufficient and clear information to answer the question with certainty. Document your analytical process in <scratchpad></scratchpad> XML tags.
4. Compose your answer based on the information you extracted.

Customer Inquiry: `{{QUESTION}}`
Write your final answer within <ANSWER></ANSWER> XML tags.
Think step by step before you provide your answer. Do not answer the question if you cannot answer it with certainty from the extracted quotes and never break character.```
<TEST_CASE_1>
<DOCUMENT_TEXT>
Acme Dynamics, Inc. is a leading AI and robotics company based in Palo Alto, California.  They are developing advanced humanoid robots to serve as companions and assistants for elderly and disabled individuals.  Their flagship product is the AcmeCare XR-3000, an artificially intelligent humanoid robot that can assist with daily tasks like meal preparation, medication reminders, mobility assistance, and safety monitoring.
</DOCUMENT_TEXT>
<QUESTION>
Can I return a product after 30 days of purchase?
</QUESTION>
</TEST_CASE_1>
<TEST_CASE_2>
<DOCUMENT_TEXT>
Acme Dynamics, Inc. is a leading AI and robotics company based in Palo Alto, California.  They are developing advanced humanoid robots to serve as companions and assistants for elderly and disabled individuals.  Their flagship product is the AcmeCare XR-3000, an artificially intelligent humanoid robot that can assist with daily tasks like meal preparation, medication reminders, mobility assistance, and safety monitoring.
</DOCUMENT_TEXT>
<QUESTION>
What does Acme Dynamics do?
</QUESTION>
</TEST_CASE_2>
...
<TEST_CASE_10>
<DOCUMENT_TEXT>
Acme Dynamics, Inc. is a leading AI and robotics company based in Palo Alto, California.  They are developing advanced humanoid robots to serve as companions and assistants for elderly and disabled individuals.  Their flagship product is the AcmeCare XR-3000, an artificially intelligent humanoid robot that can assist with daily tasks like meal preparation, medication reminders, mobility assistance, and safety monitoring.
</DOCUMENT_TEXT>
<QUESTION>
Where is the company based?
</QUESTION>
</TEST_CASE_10>
</EXAMPLE>
<EXAMPLE>
Prompt: ```I will provide you with a text inside <TEXT> XML tags. Read through the text carefully and identify all full names that include both first and last names. 

Extract just the first and last names into a list format, with each full name on a separate line inside <NAMES> XML tags. Only include the first and last names - do not include any other information from the text.

Here is the text:

<TEXT>
{{TEXT}} 
</TEXT>

Please provide the list of extracted names here:
<NAMES>

</NAMES>

Think step-by-step and double check your work. Do not include anything other than the first and last names extracted from the provided text.```
<TEST_CASE_1>
<TEXT>
Steve Jobs was a key member of Apple, especially in its early days, and Tim Cook is the current CEO. 
</TEXT>
</TEST_CASE_1>
<TEST_CASE_2>
<TEXT>
Mr. Jones and his student, Tim Smith, are working on a new project together.
</TEXT>
</TEST_CASE_2>
...
<TEST_CASE_10>
<TEXT>
I want to know the names of all the people who work at Acme Dynamics.
</TEXT>
</TEST_CASE_10>
</EXAMPLE>
</EXAMPLES>

# PROMPT #
Here is the prompt for which you need to generate test cases. Read it carefully:
<PROMPT>
{prompt}
</PROMPT>

# VARIABLE NAMES #
It is essential that you use the following variable name(s) in your test cases. You should use these variable names for both XML tags and the variable names themselves:
<VARIABLE_NAMES>
{var_names}
</VARIABLE_NAMES>

# INSTRUCTIONS #
Follow this procedure to generate test cases:
1. Read the PROMPT carefully, focusing on its intent, goal, and task it is designed to elicit from the LLM. Document your understanding of the PROMPT in <PROMPT_ANALYSIS></PROMPT_ANALYSIS> XML tags.
2. Generate {num_test_cases} test cases that can be used to assess how well the prompt achieves its goal. Ensure they are diverse and cover different aspects of the prompt. The test cases should attempt to reveal areas where the prompt can be improved. Write your numbered test cases in <TEST_CASE_#></TEST_CASE_#> XML tags. Inside these tags, use additional tags that specify the name of the variable your input is represented by. 

# ADDITIONAL GUIDELINES #
Remember to match the format of the example exactly. Ensure the XML tags you use match the variable name(s) in the prompt exactly. For example, if the prompt contains <DOCUMENT>{{TEXT}}</DOCUMENT>, your test input must be written within <TEXT></TEXT> XML tags. 
Double check your test cases against the procedure and examples before you answer.
"""

        test_cases_response = await self.api.send_request_to_claude(
            TEST_CASE_generation_prompt, temperature=0.2
        )
        if test_cases_response:
            test_cases = extract_test_cases(test_cases_response)
            if not test_cases:
                return None
            # print_success(f"*** Generated {len(test_cases)} test cases. ***")
            return test_cases
        else:
            print_error("Test case generation failed.")
            return None

    async def setup_test_cases(
        self, num_tc: int, prompt_template: str, placeholder_names: List[str]
    ) -> Union[Dict[str, str], None]:
        """
        Generate test cases based on the given parameters.

        Args:
            num_tc (int): The number of test cases to generate.
            prompt_template (str): The template for the prompt.
            placeholder_names (List[str]): The list of placeholder names.

        Returns:
            Union[Dict[str, str], None]: The generated test cases as a dictionary, or None if unable to generate.

        """
        while True:
            test_cases = await self.generate_test_cases(
                num_tc, prompt_template, placeholder_names
            )
            if test_cases is None:
                return None
            test_cases, test_case_retry = update_variable_names(
                test_cases, placeholder_names
            )
            if not test_case_retry:
                break
        print_success(f"*** Set up {len(test_cases)} test cases. ***")
        return test_cases

    async def evaluate_response(
        self, prompt_to_eval: str, response_to_eval: str
    ) -> Optional[str]:
        """
        Evaluates the adherence of a response to the associated prompt.

        Args:
            prompt_to_eval (str): The prompt to evaluate.
            response_to_eval (str): The response to evaluate.

        Returns:
            Optional[str]: The evaluation of the response, or None if evaluation fails.
        """
        evaluation_prompt = f"""
# CONTEXT #
Your task is to evaluate the adherence of a response to the associated prompt. Failure of the response to adhere perfectly to the instructions in the prompt can indicate flawed prompt engineering.

# PROMPT #       
Here is the prompt you need to evaluate. Read it carefully:
<PROMPT_TO_EVAL>
{prompt_to_eval}
</PROMPT_TO_EVAL>

# RESPONSE #
Here is the response you need to evaluate. Read it carefully:
<RESPONSE_TO_EVAL>
{response_to_eval}
</RESPONSE_TO_EVAL>

# INSTRUCTIONS #
Follow this procedure to perform your evaluation:
1. Read the prompt carefully, focusing on its intent, format, and the specific task it is designed to elicit from the LLM.
2. Carefully assess the response's adherence to the prompt. Clearly document your step by step analytical process, including any deviations, hallucinations, logic/reasoning mistakes or any other undesired behavior, however minor, from the prompt's specified instructions in <EVALUATION_SCRATCHPAD></EVALUATION_SCRATCHPAD> XML tags.
3. Score the prompt's performance in generating the expected response. Mark it as 'PASS' if the response aligns perfectly with the instructions and the LLM behaves optimally. Mark it as 'FAIL' otherwise. Write your determination in <EVALUATION_RESULT></EVALUATION_RESULT> XML tags.

Remember, the prompt you are evaluating was asked of another LLM, and the response was created by that same other LLM. Your job is to evaluate the performance. Think step by step before you answer.
"""

        evaluation_response = await self.api.send_request_to_claude(
            evaluation_prompt, temperature=0
        )
        if evaluation_response:
            return evaluation_response
        else:
            print_error(
                "Self-Evaluation failed."
            )  # This is an error, not a failed test case
            return None

    async def execute_prompt(self, prompt: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Executes a prompt by sending a request to Claude and evaluates the response.

        Args:
            prompt (str): The prompt to be executed.

        Returns:
            Tuple[Optional[str], Optional[str]]: A tuple containing the response and evaluation.
                - The response (str): The response received from Claude.
                - The evaluation (str): The evaluation of the response.

                If the prompt execution fails or the evaluation is not available, None is returned for both values.
        """
        response = await self.api.send_request_to_claude(prompt, temperature=0)
        if response is None:
            print_error("Prompt execution failed.")
            return None, None
        evaluation = await self.evaluate_response(prompt, response)
        if evaluation is None:
            return None, None
        return response, evaluation

    async def handle_test_case(
        self, test_case: str, test_case_data: Dict[str, str], prompt_template: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Handles a single test case by executing the prompt and processing the response.

        Args:
            test_case (str): The name of the test case.
            test_case_data (Dict[str, str]): The data for the test case.
            prompt_template (str): The template for the prompt.

        Returns:
            Tuple[bool, Optional[str], Optional[str]]: A tuple containing:
                - A boolean indicating whether the test case should be skipped.
                - The response received from Claude.
                - The evaluation of the response.
        """
        print(f"\n{test_case} input(s): ")
        for key, val in test_case_data.items():
            print_info(f"{key}: {val}")
        skip_test_case = False
        for val in test_case_data.values():
            if val is None or val == "None":
                print_warning(f"Skipping test case because it contains invalid input.")
                skip_test_case = True
                break

        if skip_test_case:
            return True, None, None

        loaded_prompt = load_prompt(prompt_template, test_case_data)
        response, evaluation = await self.execute_prompt(loaded_prompt)
        if response is None and evaluation is None:
            return False, None, None
        return False, response, evaluation

    async def process_test_cases(
        self,
        test_cases: Dict[str, str],
        prompt_template: str,
        combined_results: List[Dict[str, Union[str, Dict[str, str]]]],
        test_results: Dict[str, Union[str, Dict[str, str]]],
    ) -> Tuple[
        Dict[str, Union[str, Dict[str, str]]],
        List[Dict[str, Union[str, Dict[str, str]]]],
        bool,
    ]:
        """
        Processes the test cases by executing the prompt and evaluating the responses.

        Args:
            test_cases (Dict[str, str]): A dictionary containing the test cases.
            prompt_template (str): The template for the prompt.
            combined_results (List[Dict[str, Union[str, Dict[str, str]]]]): A list of combined results.
            test_results (Dict[str, Union[str, Dict[str, str]]]): A dictionary containing the test results.

        Returns:
            test_results (Dict[str, Union[str, Dict[str, str]]]): A dictionary containing the test results.
            combined_results (List[Dict[str, Union[str, Dict[str, str]]]]): A list of combined results.
            failed_test_cases (bool): A boolean indicating whether any test cases failed.
        """
        results, failed_test_cases = {}, False
        print_info(f"\n*** Evaluating test cases concurrently... ***")
        test_case_handling_tasks = [
            asyncio.create_task(
                self.handle_test_case(test_case, test_cases[test_case], prompt_template)
            )
            for test_case in test_cases
        ]
        test_case_results = await asyncio.gather(*test_case_handling_tasks)
        for test_case, (skip_test_case, response, evaluation) in zip(
            test_cases.keys(), test_case_results
        ):
            if not response or not evaluation:
                skip_test_case = True
                # return None, None, None
            if response:
                print(f"{test_case} response: ")
                print_info(f"{response}")
            if skip_test_case:
                continue

            eval_result = extract_eval_result(evaluation)
            test_case_failed = handle_eval_result(test_case, eval_result)
            failed_test_cases = (
                failed_test_cases or test_case_failed
            )  # Update only if a failure is detected

            test_result = update_test_results(
                test_case,
                prompt_template,
                test_cases[test_case],
                response,
                evaluation,
            )
            test_results.update(test_result)

            result_for_file = store_results_for_file(test_case, response, evaluation)
            results.update(result_for_file)

            parsed_results = parse_results_for_file(
                results, test_case, prompt_template, response
            )
            combined_results.append(parsed_results)

        return test_results, combined_results, failed_test_cases

    async def process_no_input_var_case(
        self, prompt_template: str, combined_results: List, test_results: Dict[str, str]
    ) -> Union[Dict[str, str], List, bool]:
        """
        Process the case when there is no input variable.

        Args:
            prompt_template (str): The template for the prompt.
            combined_results (List): The combined results.
            test_results (Dict[str, str]): The test results.

        Returns:
            Union[Dict[str, str], List, bool]: The processed test results, combined results, and evaluation status.
        """
        results = {}
        response, evaluation = await self.execute_prompt(prompt_template)
        if response is None and evaluation is None:
            return None, None, None
        eval_result = extract_eval_result(evaluation)
        eval_failed = handle_eval_result("", eval_result)
        test_results = update_test_results(
            0, prompt_template, "None", response, evaluation
        )
        result_for_file = store_results_for_file(0, response, evaluation)
        results.update(result_for_file)
        parsed_results = parse_results_for_file(results, 0, prompt_template, response)
        combined_results.append(parsed_results)
        return test_results, combined_results, eval_failed
