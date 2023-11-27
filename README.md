# Prompt Generation Tool for Claude

## Overview

This tool is designed to demonstrate how Claude can be utilized for generating effective prompts. You provide a high-level task for Claude to perform, and the tool attempts to automate the generation, testing, and iterative improvement of a prompt to complete the task reliably. The aim is to provide a solid starting point for any given task by producing an initial prompt, which you can then tweak according to your specific needs.

## Key Features

- **Intelligent Prompt Generation**: Develops initial prompt from a high-level description.
- **Automated Test Cases Creation**: Generates diverse test cases automatically.
- **Self-Evaluation**: Conducts evaluations of responses to gauge their alignment with the defined goals of the prompt.
- **Iterative Improvement Process**: Refines and enhances the prompt based on failed self-evaluations.
- **Detailed Reporting**: Stores feedback and detailed results in a JSON file for analysis.

## Creating Effective Prompt Descriptions

Consider the following when entering your prompt description:

- **Clarity**: Be clear and specific about the task Claude should perform. Vague descriptions can lead to unpredictable results.
- **Objective Definition**: Define the objective clearly. What is the intended output or result of the prompt?
- **Specify Required Inputs**: Clearly indicate any specific inputs required for the task. For instance, if you need Claude to extract information from a particular type of text, mention that this text should be taken as input. The tool is designed to automatically generate relevant test text based on your specified inputs.

## Installation and Setup

Clone the repository and install dependencies:

```bash
git clone https://github.com/chris-nickerson/claude-prompt-generator.git
cd claude-prompt-generator
pip install -r requirements.txt


### Configuration

Set your Anthropic API key in a `.env` file:

```
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage Instructions

Run the tool with:

```bash
python prompt_generator.py
```

Follow the on-screen prompts.
