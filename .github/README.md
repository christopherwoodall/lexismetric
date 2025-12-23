# LexisMetric

A modular CLI tool designed to measure, quantify, and visualize the reading level of Large Language Model (LLM) prompts and their corresponding outputs. LexisMetric provides a structured framework for benchmarked linguistic complexity across multiple models.

## Installation
1. Clone the repository:
```bash
git clone https://github.com/yourusername/lexismetric.git
cd lexismetric
```

2. Set up a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install in editable mode:
```bash
pip install -e .
```

## Configuration
1. **Environment Variable:** Set your OpenRouter API key:
```bash
export OPENROUTER_API_KEY='your_api_key_here'
```

2. Project Files:
* `config/models.yaml`: Define the models to evaluate.
* `config/prompts.yaml`: Define the list of prompts to test.

## Commands
### Execute Evaluation
Run the asynchronous benchmark across all configured models and prompts:
```bash
lm run
```
Raw results are saved as timestamped JSON files in the `./logs` directory.

### Generate Report
Generate an interactive HTML report based on the most recent log file:
```bash
lm report
```

The report is saved to `./docs/index.html` and includes scatter plots and linguistic correlation data.

--- 
### Development 
* Code Assistant: Gemini