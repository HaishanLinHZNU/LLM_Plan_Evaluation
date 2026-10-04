### basic prompt:

```
indicator: '{indicator}'. Evaluate the provided comprehensive development plan against the given indicator.

Response Format: 
### Score: <here to put the score (only number range in 0, 1, and 2)>

### Reason:
1. ...
2. ...
3. ...
..."
```

### optimized prompt

```python
indicator: '{indicator}'. 

Here is the interpretation of the indicator: 
{interpretation}

Scoring framework:
{scoring_framework}

Evaluate the provided 'The {county_name} County Comprehensive Development Plan' against the given indicator. 

Response Format: 
### Score: <here to put the score (only number range in 0, 1, and 2)>

### Reason:
1. ...
2. ...
3. ...
..."
```

### instruction for evaluator agent

```
Task: Evaluate the provided County Comprehensive Development Plan against the given indicator. 

Scoring Criteria: 
0 - Does Not Match (0 points) 
The plan does not address or mention the indicator at all. No effort is made to incorporate or consider the indicator. Shows no understanding of the indicator's relevance. 

1 - Partially Matches (1 point) 
The plan briefly mentions the indicator but lacks depth or specificity. The mention might be tangential or incomplete, not fully aligned with the objectives. The explanation is minimal and may not seem practical or well-supported. Feasibility and integration with the overall plan are weak or unclear. 

2 - Fully Matches (2 points) 
The plan thoroughly addresses the indicator with detailed, specific content. Provides a clear explanation of how the indicator will be implemented. The approach is realistic, well-supported by evidence, and feasible. Demonstrates strategic alignment with the plan's goals, showing how the indicator plays a critical role in its success. 

Instructions for Scoring: 
Be critical and cautious when awarding 2 points. Only give a score of 2 if all conditions are clearly met (thorough explanation, high feasibility, strategic integration). If the plan addresses the indicator but lacks depth, clarity, or feasibility, lean towards a score of 1. If the indicator is not addressed or its relevance is not demonstrated, assign a score of 0. 

Expected Response: 
Provide a single score (0, 1, or 2) based on the criteria above, and the reason or factual base of it. "
```

### 

