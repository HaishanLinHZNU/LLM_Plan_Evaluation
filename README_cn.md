# Plan Evaluation System

基于 OpenAI Assistants API 的综合性发展规划评估与指标评分框架优化系统。

## 项目概述

本项目旨在自动化评估县级综合发展规划（County Comprehensive Development Plan）对一系列预设指标的符合程度。系统通过调用 OpenAI 的 Assistants API（支持文件检索和向量存储），对规划文本进行语义分析，并依据评分框架（0-2分）给出得分及依据。

核心创新点在于引入了一套**自优化的评分框架生成机制**，能够根据历史评估的偏差（混淆矩阵、均方误差等）自动调整指标的评分标准，从而持续提升评估的准确率。

## 主要功能

1. **自动化规划评估 (`Call_assistant_api_change_max_num_result.py` / `Call_assistant_finial_part_1.py`)**
   - 遍历多个郡（County）的综合发展规划 PDF（已上传为 Vector Store）。
   - 针对预设的指标列表进行语义检索和打分。
   - 支持断点续传，可从中断处恢复评估任务。

2. **评估结果解析与可视化 (`Resolve_the_result_of_Plan_Evaluation.py`)**
   - 将评估原始 JSON 数据解析为结构化的 Excel 表格。
   - 计算准确率、平均误差 (ME)、均方误差 (MSE)、混淆矩阵等关键性能指标。
   - 自动生成带样式（颜色标注错误与偏差）的 Excel 报告。

3. **评分框架自优化 (`Optimizing_scoring_framework*.py`)**
   - **优化器 Agent**：根据当前评分框架的表现（准确率、误差趋势）和混淆矩阵分析，生成更精准的评分标准（Interpretation & Scoring Framework）。
   - **评估器 Agent**：自动运行新生成的框架进行测试，计算新框架的准确率。
   - **自动迭代**：系统会自动保留表现更好的评分框架，并持续优化直至达到阈值或收敛。

4. **提示词优化实验 (`Optimizing_instruction.py`)**
   - 用于探索不同系统指令（Meta-Prompt）对评估效果的影响，通过元学习生成更优的任务描述。

## 文件结构说明

| 文件名称                                                   | 描述                                                         |
| :--------------------------------------------------------- | :----------------------------------------------------------- |
| `Call_assistant_api_change_max_num_result.py`              | **主评估流程**：基础版本，包含完整的 API 调用、重试逻辑和结果存储。 |
| `Call_assistant_finial_part_1.py`                          | **优化后评估流程**：集成了动态加载最优评分框架的功能（`Best_Scoring_Framework`）。 |
| `Optimizing_scoring_framework_with_generating_tendency.py` | **核心优化器**：结合混淆矩阵分析生成优化建议，自动迭代寻找最优评分标准。 |
| `Optimizing_instruction.py`                                | 用于优化系统顶层指令（Instruction）的实验脚本。              |
| `Resolve_the_result_of_Plan_Evaluation.py`                 | 结果解析工具，负责 JSON 到 Excel 的转换及统计学指标计算。    |
| `Writing_result.py`                                        | 负责将评估过程中的原始数据写入 JSON 文件。                   |
| `Get_vector_store_id.py`                                   | 工具函数，根据郡名查找对应的 OpenAI Vector Store ID。        |
| `prompt.md`                                                | 记录了评估过程中使用的 Prompt 模板演变历史。                 |

## 数据流与工作流程

1. **准备阶段**
   - 规划文档 PDF 上传至 OpenAI 并创建 Vector Store。
   - 准备指标配置文件：`__indicators_with_Scoring_Framework__.json`。

2. **评估阶段 (`Call_assistant_*.py`)**
   - 读取 `County-Indicator` 映射表。
   - 切换 Assistant 的 Vector Store 至对应郡。
   - 组装 Prompt：`Indicator + Interpretation + Scoring Framework`。
   - 获取 LLM 评分结果及引用依据。

3. **分析阶段 (`Resolve_*.py`)**
   - 计算准确率与混淆矩阵。
   - 输出 `_bias_info.json` 和 `_resolved.xlsx`。

4. **优化阶段 (`Optimizing_*.py`)**
   - 读取低准确率指标的偏差数据。
   - 调用优化 Agent 生成新的评分框架。
   - 自动运行新框架并对比结果，保留更优框架。

## 环境配置

### 依赖库
```bash
pip install openai pandas numpy openpyxl tqdm
```



### API 配置

请在代码文件顶部填入您的 OpenAI API Key 和 Base URL（如有代理）：
```python
api_key = "sk-xxxxxxxx"
api_base = "https://api.openai.com/v1"  
```

### 路径配置
需要根据您的实际文件存储位置修改以下全局变量路径：
- `indicator_data_path`：指标与郡的对应关系 JSON。
- `vector_store_data_path`：郡名与 Vector Store ID 映射 JSON。
- `result_directory_path`：结果输出目录。

## 使用方法

### 1. 执行基础评估
直接运行主流程脚本，开始对所有郡和指标进行评估：
```bash
python Call_assistant_finial_part_1.py
```

### 2. 仅解析已有结果
如果你已经有 `result_start_at_xxx.json` 文件，可以在 `Resolve_the_result_of_Plan_Evaluation.py` 底部调用解析函数：
```python
Change_Plan_Evaluation_from_json_to_xlsx("path/to/result.json", "timestamp")
```

### 3. 启动评分框架自动优化
```bash
python Optimizing_scoring_framework_with_generating_tendency.py
```
脚本将自动识别准确率低于阈值（如 40%）的指标，并开始迭代优化。

### 4. 断点续传
如果在评估过程中网络中断，可以记录下中断时的时间戳，并通过参数恢复：
```python
Plan_evaluation(timestamp_for_resuming="24-11-05 12-55-05")
```

## 输出示例

评估完成后，会在 `Result_of_Plan_Evaluation/` 目录下生成以下文件：
- `Part_1_result_start_at_24-11-05 12-55-05.json`：原始评估数据。
- `Part_1_result_start_at_24-11-05 12-55-05_resolved.xlsx`：包含 Evaluation、Confusion Matrix、Indicators 三个 Sheet 的可视化报告。

## 注意事项

1. **速率限制**：代码中内置了 `random_lag()` 函数以规避 OpenAI API 的速率限制，若仍遇到 429 错误，请适当增大延迟参数。
2. **Vector Store 费用**：OpenAI 的 Vector Store 存储按天计费，评估完成后请及时清理不再使用的 Vector Store。
3. **模型选择**：默认使用 `gpt-4o-mini` 以平衡成本与效果，如需更高精度可修改为 `gpt-4o`。