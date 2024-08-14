# Define a dict that drives model selection
# Keys are LLM providers, values are dicts with keys for each task

model_selector = {
    "Anthropic": {
        "prompt-generation": {"model": "claude-3-sonnet-20240229", "temperature": 0.1},
        "test-case-generation": {
            "model": "claude-3-sonnet-20240229",
            "temperature": 0.2,
        },
        "test-case-execution": {
            "model": "claude-3-sonnet-20240229",
            "temperature": 0.0,
        },
        "test-case-evaluation": {
            "model": "claude-3-sonnet-20240229",
            "temperature": 0.0,
        },
    },
    "Writer": {
        "prompt-generation": {"model": "palmyra-x-32k", "temperature": 0.1},
        "test-case-generation": {"model": "palmyra-x-32k", "temperature": 0.2},
        "test-case-execution": {"model": "palmyra-x-32k", "temperature": 0.0},
        "test-case-evaluation": {"model": "palmyra-x-32k", "temperature": 0.0},
    },
}
