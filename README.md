# Plan Evaluation System

An automated comprehensive development plan evaluation and scoring framework optimization system based on the OpenAI Assistants API.

## Project Overview

This project automates the evaluation of County Comprehensive Development Plans against a set of predefined indicators. By leveraging the OpenAI Assistants API (supporting file search and vector stores), the system performs semantic analysis on planning documents and assigns scores (0–2) along with justifications based on a scoring framework.

The core innovation lies in a **self-optimizing scoring framework generation mechanism**. It automatically adjusts scoring criteria based on historical evaluation biases (e.g., confusion matrix, mean squared error), thereby continuously improving evaluation accuracy.

## Key Features

1. **Automated Plan Evaluation** (`Call_assistant_api_change_max_num_result.py` / `Call_assistant_finial_part_1.py`)
   - Iterates over multiple counties whose comprehensive development plans (PDFs) have been uploaded as Vector Stores.
   - Performs semantic retrieval and scoring against a predefined list of indicators.
   - Supports resumption from breakpoints, allowing recovery from interrupted evaluation tasks.

2. **Result Parsing and Visualization** (`Resolve_the_result_of_Plan_Evaluation.py`)
   - Parses raw evaluation JSON data into a structured Excel workbook.
   - Calculates key performance metrics such as accuracy, Mean Error (ME), Mean Squared Error (MSE), and confusion matrices.
   - Automatically generates styled Excel reports with color-coded errors and deviations.

3. **Scoring Framework Self-Optimization** (`Optimizing_scoring_framework*.py`)
   - **Optimizer Agent**: Generates more precise scoring criteria (Interpretation & Scoring Framework) based on current framework performance (accuracy, error trends) and confusion matrix analysis.
   - **Evaluator Agent**: Automatically tests newly generated frameworks and calculates their accuracy.
   - **Automatic Iteration**: The system retains better-performing scoring frameworks and continues optimization until a threshold is reached or convergence occurs.

4. **Prompt Optimization Experiments** (`Optimizing_instruction.py`)
   - Explores the impact of different system instructions (Meta-Prompts) on evaluation outcomes through meta-learning to generate improved task descriptions.

## File Structure

| File Name                                                  | Description                                                  |
| :--------------------------------------------------------- | :----------------------------------------------------------- |
| `Call_assistant_api_change_max_num_result.py`              | **Main evaluation pipeline**: Base version with full API calls, retry logic, and result storage. |
| `Call_assistant_finial_part_1.py`                          | **Optimized evaluation pipeline**: Dynamically loads the best-performing scoring framework (`Best_Scoring_Framework`). |
| `Optimizing_scoring_framework_with_generating_tendency.py` | **Core optimizer**: Generates optimization suggestions using confusion matrix analysis and iteratively seeks the best scoring criteria. |
| `Optimizing_instruction.py`                                | Experimental script for optimizing top-level system instructions. |
| `Resolve_the_result_of_Plan_Evaluation.py`                 | Result parsing utility: handles JSON-to-Excel conversion and statistical metric calculations. |
| `Writing_result.py`                                        | Writes raw evaluation process data into JSON files.          |
| `Get_vector_store_id.py`                                   | Utility function to look up OpenAI Vector Store IDs by county name. |
| `prompt.md`                                                | Records the evolution of prompt templates used during evaluation. |

## Data Flow and Workflow

1. **Preparation Phase**
   - Upload planning documents (PDFs) to OpenAI and create Vector Stores.
   - Prepare indicator configuration files (e.g., `__indicators_with_Scoring_Framework__.json`).

2. **Evaluation Phase** (`Call_assistant_*.py`)
   - Read the `County-Indicator` mapping table.
   - Switch the Assistant's Vector Store to the corresponding county.
   - Assemble the prompt: `Indicator + Interpretation + Scoring Framework`.
   - Retrieve the LLM score and supporting citations.

3. **Analysis Phase** (`Resolve_*.py`)
   - Calculate accuracy and confusion matrices.
   - Output `_bias_info.json` and `_resolved.xlsx`.

4. **Optimization Phase** (`Optimizing_*.py`)
   - Read bias data for low-accuracy indicators.
   - Invoke the Optimizer Agent to generate a new scoring framework.
   - Automatically run the new framework, compare results, and retain the superior one.

## Environment Setup

### Dependencies
```bash
pip install openai pandas numpy openpyxl tqdm
```

### API Configuration

Enter your OpenAI API Key and Base URL (or proxy) at the top of the code files:
```python
api_key = "sk-xxxxxxxx"
api_base = "https://api.openai.com/v1"
```

### Path Configuration
Modify the following global variable paths according to your actual file storage locations:
- `indicator_data_path`: JSON mapping of indicators to counties.
- `vector_store_data_path`: JSON mapping of county names to Vector Store IDs.
- `result_directory_path`: Output directory for results.

## Usage

### 1. Run Basic Evaluation
Execute the main pipeline script to begin evaluating all counties and indicators:
```bash
python Call_assistant_finial_part_1.py
```

### 2. Parse Existing Results Only
If you already have a `result_start_at_xxx.json` file, call the parsing function at the bottom of `Resolve_the_result_of_Plan_Evaluation.py`:
```python
Change_Plan_Evaluation_from_json_to_xlsx("path/to/result.json", "timestamp")
```

### 3. Launch Automatic Scoring Framework Optimization
```bash
python Optimizing_scoring_framework_with_generating_tendency.py
```
The script will automatically identify indicators with accuracy below a threshold (e.g., 40%) and begin iterative optimization.

### 4. Resume from Breakpoint
If the evaluation is interrupted due to network issues, record the timestamp of the interruption and resume using the parameter:
```python
Plan_evaluation(timestamp_for_resuming="24-11-05 12-55-05")
```

## Output Example

After evaluation, the following files will be generated in the `Result_of_Plan_Evaluation/` directory:
- `Part_1_result_start_at_24-11-05 12-55-05.json`: Raw evaluation data.
- `Part_1_result_start_at_24-11-05 12-55-05_resolved.xlsx`: Visualized report containing `Evaluation`, `Confusion Matrix`, and `Indicators` sheets.

## Notes

1. **Rate Limits**: The code includes `random_lag()` functions to avoid OpenAI API rate limits. If you still encounter 429 errors, consider increasing the delay parameters.
2. **Vector Store Costs**: OpenAI charges for Vector Store storage on a daily basis. Remember to clean up unused Vector Stores after evaluation is complete.
3. **Model Selection**: The default model is `gpt-4o-mini` to balance cost and performance. For higher precision, you may change it to `gpt-4o`.

