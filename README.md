# Python Prompt Generation Tool for Claude

## Overview
This tool is designed to help you create effective prompts for Claude. It attempts to automate the initial generation, testing, and iterative improvement of prompts, streamlining the prompt engineering process. It's meant to create a good prompt to start with for a given task, allowing you to tweak it as necessary afterward.

## Key Features
- **Prompt Generation from High-Level Prompt Description**: Generates a prompt with best-practices in mind from a high-level prompt description.
- **Automated Test Cases**: Automatically generates test cases.
- **In-depth Self-Evaluation**: Self-assesses responses for alignment with prompt goals.
- **Iterative Refinement**: Enhances prompts based on evaluation feedback.
- **Comprehensive Results**: Detailed feedback and results storage in JSON.

## Installation and Setup
Clone the repository and install dependencies:
```bash
git clone [Your-Repository-Link]
cd [Project-Directory]
pip install -r requirements.txt
```

## Configuration
Set your Anthropic API key in a `.env` file:
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage Instructions
Run the tool with:
```bash
python prompt_generator.py
```
Follow the on-screen prompts to choose or create your desired prompt.