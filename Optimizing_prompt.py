from openai import OpenAI
from time import sleep
import random
from datetime import datetime
import logging
import json
import re
from Call_assistant_api_change_max_num_result import Plan_evaluation


api_key = ""
api_base = "https://api.openai.com/v1"

# file path
indicator_data_path = "Indicators/test.json"
vector_store_data_path = "./NE_Plans/Plans picked according to completeness (county)/Files_info.json"

result_directory_path_for_plan_evaluation = "./Result_of_Plan_Evaluation/"
result_directory_path_for_optimizing = "./Result_of_Optimizing_Prompt/"
generated_instruction_directory_path = "./Result_of_Optimizing_Prompt/generated_instructions/"

history_prompt_file_path = "./Result_of_Optimizing_Prompt/history_instructions.json"
history_generated_instruction_path = "./Result_of_Optimizing_Prompt/history_generated_instructions.json"
history_meta_prompt_path = "./Result_of_Optimizing_Prompt/history_meta_prompt.json"

optimizer_assistant_id_list = []
scorer_assistant_id_list = []


client = OpenAI(api_key=api_key, base_url=api_base)


thread_prompt_default_v3 = "Task: Evaluate the provided County Comprehensive Development Plan against the given indicator. \n\nScoring Criteria: \n0 - Does Not Match (0 points) \nThe plan does not address or mention the indicator at all. No effort is made to incorporate or consider the indicator. Shows no understanding of the indicator's relevance. \n\n1 - Partially Matches (1 point) \nThe plan briefly mentions the indicator but lacks depth or specificity. The mention might be tangential or incomplete, not fully aligned with the objectives. The explanation is minimal and may not seem practical or well-supported. Feasibility and integration with the overall plan are weak or unclear. \n\n2 - Fully Matches (2 points) \nThe plan thoroughly addresses the indicator with detailed, specific content. Provides a clear explanation of how the indicator will be implemented. The approach is realistic, well-supported by evidence, and feasible. Demonstrates strategic alignment with the plan's goals, showing how the indicator plays a critical role in its success. \n\nInstructions for Scoring: \nBe critical and cautious when awarding 2 points. Only give a score of 2 if all conditions are clearly met (thorough explanation, high feasibility, strategic integration). If the plan addresses the indicator but lacks depth, clarity, or feasibility, lean towards a score of 1. If the indicator is not addressed or its relevance is not demonstrated, assign a score of 0. \n\nExpected Response: \nProvide a single score (0, 1, or 2) based on the criteria above, and the reason or factual base of it. "
structural_response_instruction = "\n\nResponse Format: \n###Score: <here to put the score>\n\n###Reason:\n1. ...\n2. ...\n3. ...\n..."

'''<Basic function>'''
def random_lag(lag_min=1, lag_max=5):
    # Generate a random delay between 1 and 11 seconds
    sleep(random.randint(lag_min, lag_max))


def open_file(result_file_path):
    """
    Opens and loads JSON data from the specified file path.

    Args:
        result_file_path (str): The path to the JSON file.

    Returns:
        dict: The loaded JSON data.
    """
    with open(result_file_path, 'r') as file:
        data = json.load(file)
    return data



def save_result_to_json(file_path, data):
    try:
        # Write the updated data back to the file
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
        print(f"Result saved to \n{file_path}")
    except Exception as e:
        print(f"<Save result to json>"
              f" error rase when writing data to json with '{e}'")



def pick_random_elements_from_dictionary(input_dict, num_elements):
    # Check if the number of elements to pick is greater than the dictionary size
    if num_elements > len(input_dict):
        raise ValueError("Number of elements to pick exceeds the size of the dictionary.")

    # Convert the keys view to a list
    keys_list = list(input_dict.keys())

    # Randomly select keys from the list of keys
    selected_keys = random.sample(keys_list, num_elements)

    # Create a new dictionary with the selected keys and their corresponding values
    selected_elements = {key: input_dict[key] for key in selected_keys}

    return selected_elements



def pick_random_elements_from_list(input_list, num_elements):
    # Check if the number of elements to pick is not greater than the list length
    if num_elements > len(input_list):
        raise ValueError("Number of elements to pick cannot be greater than the list size")

    # Randomly pick the specified number of elements from the list
    selected_elements = random.sample(input_list, num_elements)

    return selected_elements



def pick_top_n_elements_by_comprehensive_score(input_dict, num_elements=3, sub_element_key='Mean_comprehensive_score_for_prompt'):
    # Check if the number of elements to pick is greater than the dictionary size
    if num_elements > len(input_dict):
        raise ValueError("Number of elements to pick exceeds the size of the dictionary.")

    # Use a list to hold tuples of (key, value) for sorting
    items = [(key, value) for key, value in input_dict.items()]

    # Sort the items based on the specified sub-element, but only take the top N
    top_n_items = sorted(items, key=lambda item: item[1].get(sub_element_key), reverse=True)[:num_elements]

    # Create a dictionary from the top N items
    top_n_elements = {key: value for key, value in top_n_items}

    return top_n_elements


def convert_to_number(input_value):
    # 如果输入已经是整数或浮点数，直接返回
    if isinstance(input_value, (int, float)):
        return input_value

    # 尝试将字符串转换为浮点数或整数
    if isinstance(input_value, str):
        try:
            # 尝试转换为浮点数
            number = float(input_value)
            # 如果转换后的浮点数没有小数部分，再转换为整数
            if number.is_integer():
                return int(number)
            else:
                return number
        except ValueError:
            # 如果转换失败，打印错误信息并返回原输入
            print("输入的字符串无法转换为数字: ", input_value)
            return input_value
'''</Basic function>'''


'''<Accessing the OpenAI API>'''
def create_thread():
    while True:
        try:
            print("<create_thread> Creating new thread")
            random_lag()
            thread = client.beta.threads.create()
            print("<create_thread> [Complete]")
            return thread
        except Exception as e:
            print(f"<create_thread> Fail to create new thread with error: '{e}'")
            print("<create_thread> Retrying...")
            continue



def using_thread(prompt, thread_id):
    while True:
        try:
            random_lag()
            print(f"<thread_update> adding message to thread...")
            message = client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=prompt
            )
            print(f"<thread_update> thread update completed [Complete]")
            return message
        except Exception as e:
            print(f"<thread_update> Fail to add message with exception [{e}].")
            print(f"<thread_update> Retrying...")
            continue



def run_assistant(thread_id, assistant_id):
    while True:
        try:
            random_lag()
            print(f"<run_assistant> creating run")
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
                temperature=0.0,
                tools=[{'type': 'file_search', 'file_search': {'max_num_results': 20}}],
            )
            print(f"<run_assistant> [Complete]")
            return run
        except Exception as e:
            print(f"<run_assistant> fail to create run with [{e}]. [Fail]")
            continue



def retrieve_run(thread_id, run_id):
    random_lag()
    run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
    return run



def process_for_call_assistant_api(miss, prompt, assistant_id, thread):
    while True:
        try:
            using_thread(prompt=prompt, thread_id=thread.id)
            run = run_assistant(thread_id=thread.id, assistant_id=assistant_id)
            i = 0
            # Wait for completion of the run
            print(f"<Run> begin to Run...")
            while True:
                i += 1
                run = retrieve_run(thread_id=thread.id, run_id=run.id)
                if run.status == "completed":
                    print(f"<Run> Run completed [Complete]")
                    break

                random_lag(lag_min=1, lag_max=i)
                if i % 5 == 0 and i != 0:
                    print("<Run> Retrying Run_assistant...")
                    run = run_assistant(thread.id, assistant_id)
                else:
                    print(f"<Run> Wait for completion of the run. The {i} times trying...")
                if i >= 25:
                    print(f"<Run> Fail to get response.")
                    miss = True
                    break
            break
        except Exception as e:
            print(f"Error: {e}")
            continue
    return miss, thread



def get_messages(thread_id):
    '''
    Getting message from Response
    '''
    thread_messages = client.beta.threads.messages.list(thread_id=thread_id)
    message = thread_messages.data[0].content[0].text.value
    return message
'''</Accessing the OpenAI API>'''


'''<Evaluator process>'''
def get_final_suggestion(message):
    print(f"<Get_final_suggestion> Start processing  Suggestions ")
    message_ = message.replace("\"", "\'")
    try:
        if "### Suggestion:" in message_:
            message_ = message_.replace("### Suggestion:", "### Suggestions:")
        print(f"<Get_final_suggestion> trying to get final suggestion from message...")
        suggestion_part = message_.split("### Suggestions:")[1].strip()
        # Split the suggestions into lines
        # suggestion_lines = [line for line in suggestion_part.split('\n') if line.strip()]
        print(f"<Get_final_suggestion> Complete")
        return suggestion_part
    except Exception as e:
        print(f"<Get_final_suggestion> Failed with error: '{e}'")
    return None



def get_score_and_suggestion(message):
    print(f"<get_score_and_suggestion> Start processing Score and Suggestions ")
    message_ = message.replace("\"", "\'")

    try:
        if "### Score:" in message and "### Suggestion:" in message_:
            message_ = message_.replace("### Suggestion:", "### Suggestions:")
        print(f"<get_score_and_suggestion> trying to get score and suggestions from message...")
        score_part = message_.split("### Score:")[1].split("\n\n### Suggestions:")[0].strip()
        suggestion_part = message_.split("### Suggestions:")[1].strip()
        score = convert_to_number(score_part)
        # Split the reason into lines
        # suggestion_lines = [line for line in suggestion_part.split('\n') if line.strip()]
        print(f"<get_score_and_suggestion> Complete")
        return score, suggestion_part
    except Exception as e:
        print(f"<get_score_and_suggestion> Failed with error: '{e}'")
    return None, None



def count_final_score_for_func_prompt(result_list):
    # 算均分
    Total_score = 0
    count = 0
    for result in result_list:
        try:
            Total_score += result["Score"]
            count += 1
        except Exception as e:
            print(f"<count_final_score_for_func_prompt> fail with error: '{e}'")
            continue
    mean_score = Total_score / count

    return mean_score



def get_final_suggestion_for_improving_instruction(result_list):
    # 生成总结建议的提示词
    prompt = 'Here is a list of suggestion for improving a prompt. I want you to read throught all of these suggestions,and summary them. Merge the same part, and the redundant part, high light the suggestion that giving useful, practicable directory for further improvement, and the suggestion that addressing the key deficiency and insufficient part of the orginal prompt.\n\nsuggestions: \n'
    count = 1
    for result in result_list:
        a_part_of_suggestions = '\n'.join(map(str, result["Suggestions"]))
        prompt = prompt + f"the {count} list of suggestions:"+a_part_of_suggestions + "\n\n"
        count += 1
    prompt = prompt + "Now, summarizing the suggestions listed above, and generate a new suggestion for me.\nThe response should be in the following format: '### Suggestion: ...'"

    print(f'<get_final_suggestion> Finishing prompt creation')
    # 发起请求
    miss = False
    assistant_id = ''
    thread = create_thread()

    # 调用接口
    miss, thread = process_for_call_assistant_api(miss, prompt, assistant_id, thread)

    while True:
        try:
            if miss:
                print(f"<Result> Eliminated the fail_record to data successfully")
                suggestions = ''
                break
            print(f"<Processing> Processing response data...")
            message = get_messages(thread.id)
            print(message)
            suggestions = get_final_suggestion(message)
            print(f"Final_Suggestion: {suggestions}")
            return suggestions
        except Exception as e:
            print(f"<Result> Error: {e}")
            continue
    return None
'''</Evaluator process>'''


'''<Generating meta prompt>'''
def generate_instruction_description_for_prompt_tracking(history_prompt_data, func_prompt):
    '''
    Arg: history_prompt_data (dictionary),
         func_prompt (str)

    composing history instruction description text

    return: instruction_description (str)
    '''

    # get info from data
    instruction = history_prompt_data[func_prompt]['Func_Prompt']

    # compose previous instruction text
    mean_comprehensive_score_part = f"- Comprehensive Score: {history_prompt_data[func_prompt]['Mean_comprehensive_score_for_prompt']}\n"
    accuracy_part = f"- Accuracy: {history_prompt_data[func_prompt]['Accuracy']}\n"


    instruction_description = (
            '<HISTORY_INS>\n' + instruction + '\n</HISTORY_INS>\n\nParameters:\n' +
            mean_comprehensive_score_part + accuracy_part + '\n'
    )
    return instruction_description



def generate_previous_instruction_for_meta_prompt(history_prompt_data, previous_func_prompt):
    '''
    Arg: history_prompt_data (dictionary)
         previous_func_prompt (str)

    composing previous instruction description text

    return: previous_instruction_text (str)
    '''

    instruction = history_prompt_data[previous_func_prompt]['Func_Prompt']
    parameter_description = history_prompt_data[previous_func_prompt]['Parameter_description']

    # compose previous instruction text
    introduction = 'Below are the instruction <INS> updated at the last. Below the <INS> are its comprehensive score, ranges from 0 to 100, performance parameter, and suggestions for further improvement.\n\n'
    mean_comprehensive_score_part = f"- Comprehensive Score: {history_prompt_data[previous_func_prompt]['Mean_comprehensive_score_for_prompt']}\n"
    suggestion_part = f"\n\nSuggestion for further improvement of the previous instruction: \n{history_prompt_data[previous_func_prompt]['Suggestion_for_improving_instruction']}"

    previous_instruction_text = (
            introduction + '<PREVIOUS_INS>\n' + instruction + '\n</PREVIOUS_INS>\n\nParameters:\n' +
            mean_comprehensive_score_part + parameter_description + suggestion_part + '\n\n'
    )
    return previous_instruction_text



def generate_instructions_tracking_for_meta_prompt(history_prompt_data, previous_func_prompt, tracking_number=3):
    '''
    pick track_number of history instruction, to compose an instruction tracking

    return: instruction tracking (str)
    '''

    introduction = 'Below are some previous Instructions with their scores. The score ranges from 0 to 100. \n\n'
    instruction_score_part = ''
    instructions_num = tracking_number

    if len(history_prompt_data) == 1:
        return None
    else:
        tracking_dict = pick_top_n_elements_by_comprehensive_score(history_prompt_data, len(history_prompt_data))

    if len(history_prompt_data) <= tracking_number:
        instructions_num = len(history_prompt_data) - 1

    count = 0
    for prompt in tracking_dict:
        if count == instructions_num:
            break
        if prompt == previous_func_prompt:
            continue
        text = generate_instruction_description_for_prompt_tracking(history_prompt_data, prompt)
        instruction_score_part += text
        count += 1
    instruction_tracking = introduction + instruction_score_part

    return instruction_tracking



def generate_task_examples_for_meta_prompt(history_prompt_data, previous_func_prompt, example_number=3):
    '''
    pick track_number of history instruction, to compose an instruction tracking

    return: instruction tracking (str)
    '''

    task_dict = history_prompt_data[previous_func_prompt]['Result']

    introduction = 'Below are some example for the task <INS> actually solved. \n\n'
    task_part = ''

    county_picked = pick_random_elements_from_dictionary(task_dict, 1)
    county_name = list(county_picked.keys())[0]
    indicator_list = list(county_picked.values())[0]
    indicator_picked = pick_random_elements_from_list(indicator_list, example_number)

    if indicator_picked[0]['Factual_base']:
        print(indicator_picked[0]['Factual_base'][0]['Factual_base'])
        for i in indicator_picked:
            factual_base = ''
            #for j in range(1):
                #print(i['Factual_base'][j]['Factual_base'])
                #factual_base += i['Factual_base'] + "\n\n"
            task_part += f"relevance text from Plan:\n{i['Factual_base']}indicator: '{i['Indicator']}'. Evaluate the provided 'The {county_name} County Comprehensive Development Plan' against the given indicator.\n\n"
    else:
        for i in indicator_picked:
            task_part += f"indicator: '{i['Indicator']}'. Evaluate the provided 'The {county_name} County Comprehensive Development Plan' against the given indicator.\n\n"

    task_example = introduction + task_part

    return task_example



def generating_meta_prompt(previous_func_prompt):
    '''
    receive the previous instruction as input argument

    if history_prompt is empty, start from plan evaluation and then call evaluator and finally reach here, generate
    a meta prompt.

    1. read history_prompt.json

    2. get the previous instruction by using the func_prompt as key.

    3. fill each part and generate the meta prompt that be used to optimizing instruction

    return a meta prompt (str)
    '''
    '''
    structure of meta_prompt:

    task describe
      - text: "Your task is to generate the instruction <INS>."
    prompt tracking
      - Instruction
      - Score (by evaluator)
      - Accuracy
    previous instruction
      - Instruction
      - Score (by evaluator)
      - Accuracy
      - Mean Error
      - Mean Squared Error
      - Standard Deviation of Errors
      - Confusion Matrix
    suggestions for further improvement
    task examples
    '''

    # 结果存放位置
    history_meta_prompt_path = f"{result_directory_path_for_optimizing}history_meta_prompt.json"
    history_meta_prompt_data = open_file(history_meta_prompt_path)

    # 读入 history_instructions.json
    history_instructions_path = f"{result_directory_path_for_optimizing}history_instructions.json"
    history_prompt_data = open_file(history_instructions_path)


    # meta_prompt 模板
    task_describe = "Your task is to generate the instruction <INS>. "
    previous_instruction_text = generate_previous_instruction_for_meta_prompt(history_prompt_data, previous_func_prompt)  # require
    prompt_tracking_text = generate_instructions_tracking_for_meta_prompt(history_prompt_data, previous_func_prompt) # optional
    task_examples_text = generate_task_examples_for_meta_prompt(history_prompt_data, previous_func_prompt)

    meta_prompt = task_describe

    ending_text = ('Generate an instruction that is different from the instructions <INS> above, and has a highter score '
                   'than all the instruction <INS> above. The instruction should begin with <INS> and end with </INS>. '
                   'The instruction should be concise, effective, ')

    if previous_instruction_text:
        meta_prompt += previous_instruction_text
    if prompt_tracking_text:
        meta_prompt += prompt_tracking_text
    if task_examples_text:
        meta_prompt += task_examples_text
        ending_text += 'generally applicable to all task example above, '

    ending_text += 'and clearly show the distinction between different scoring criteria.'
    meta_prompt += ending_text

    # 将 meta_prompt 存到 history_meta_prompt.json
    if previous_func_prompt not in history_meta_prompt_data:
        history_meta_prompt_data[previous_func_prompt] = {}
    history_meta_prompt_data[previous_func_prompt]["Meta_Prompt"] = meta_prompt
    save_result_to_json(history_meta_prompt_path, history_meta_prompt_data)
    #print(f"meta_prompt: \n{meta_prompt}\n\n")
    return meta_prompt
'''</Generating meta prompt>'''


'''<Optimizing>'''
def extract_text_between_ins(text):
    pattern_1 = r"<INS>(.*?)</INS>"
    pattern_2 = r"<Ins>(.*?)</Ins>"
    pattern_3 = r"<ins>(.*?)</ins>"
    match_1 = re.search(pattern_1, text, re.DOTALL)
    match_2 = re.search(pattern_2, text, re.DOTALL)
    match_3 = re.search(pattern_3, text, re.DOTALL)
    if match_1:
        return match_1.group(1).strip()
    elif match_2:
        return match_2.group(1).strip()
    elif match_3:
        return match_3.group(1).strip()
    return None



def updating_assistant_temperature(assistant_id, temperature):
    '''
    to change the temperature used by assistant, according to assistant id and assign temperature

    arg: assistant_id (str),
         temperature (float)

    return: OpenAI API assistant object.
    '''
    while True:
        try:
            random_lag()
            assistant = client.beta.assistants.update(
                assistant_id=assistant_id,
                temperature=0.0
            )
            print('<Assistant update> Assistant update instruction completed')
            return assistant
        except Exception as e:
            logging.error(f"<Assistant update> Error updating assistant with temperature: '{temperature}' {e}")
            print(f"<Assistant update> Error updating assistant with temperature: '{temperature}' {e}")
            continue



def save_generated_instruction(data, generated_instruction, previous_instruction, timestamp):
    '''
    arg:
        data (dictionary)
        generated_instruction (text)
        timestamp (timestamp)

    return: data (directionary)
    '''
    if generated_instruction not in data:
        data[generated_instruction] = {}
    data[generated_instruction]["Generated_Prompt"] = generated_instruction
    data[generated_instruction]["Evaluation_Status"] = False
    data[generated_instruction]["Timestamp_Generating"] = timestamp
    data[generated_instruction]["Previous_Prompt"] = previous_instruction
    return data
'''</Optimizing>'''


def call_optimizer(meta_prompt, previous_instruction):

    timestamp_for_prompt_optimizing = datetime.now().strftime("%y-%m-%d %H-%M-%S")

    # 结果存放的位置
    history_generated_instruction_path = result_directory_path_for_optimizing + 'history_generated_instructions.json'
    generated_instruction_path = generated_instruction_directory_path + f"generated_instruction_{timestamp_for_prompt_optimizing}.json"

    result_data = {}
    history_generated_instruction_data = open_file(history_generated_instruction_path)

    # 开始调用优化器
    print(f">=============================== Beginning call optimizer ================================<")
    thread = create_thread()

    for t in range(5):
        random_lag()
        miss = False
        assistant_id = random.sample(optimizer_assistant_id_list, 1)[0]

        miss, thread = process_for_call_assistant_api(miss=miss, prompt=meta_prompt, assistant_id=assistant_id,
                                                      thread=thread)

        while True:
            try:
                if miss:
                    print(f"<Result> Eliminated the fail_record to data successfully")
                    break
                print(f"<Processing> Processing response data...")
                message = get_messages(thread.id)
                print(message)
                # 从响应中提取优化后的 instruction
                generated_instruction = extract_text_between_ins(message)
                if generated_instruction:
                    print(f"<Extract instruction> Successfully extract generate instruction:\n{generated_instruction}")
                    history_generated_instruction_data = save_generated_instruction(history_generated_instruction_data, generated_instruction, previous_instruction, timestamp_for_prompt_optimizing)
                    result_data = save_generated_instruction(result_data, generated_instruction, previous_instruction, timestamp_for_prompt_optimizing)
                    print(f"<Result> save the result to data successfully")
                else:
                    print(f"<Extract instruction> fail to extract generate instruction")
                break
            except Exception as e:
                print(f"<Result> Error: {e}")
                continue

    # 将结果存到对应的文件
    save_result_to_json(history_generated_instruction_path, history_generated_instruction_data)
    save_result_to_json(generated_instruction_path, result_data)
    print(f"<Result> save the result to data successfully")

    print(f">=============================== Finished call evaluator ================================<")


    return timestamp_for_prompt_optimizing



def call_evaluator(func_prompt, timestamp):
    """
    输入参数：
    功能 prompt 以及 评估的各个结果（直接传入 timestamp 吧）

    0. Read data from resolved.json

    1. Fill the previous result of plan evaluation to get scoring prompt

    2. call evaluators (randomly)

    3. get multiple scores and suggestions for improving func-prompt

    4. 评分求均值

    5. 改进意见访问 api，做归纳总结，进一步精简

    5. 将对应结果存到 json

    return:
    score, suggestion
    """

    # 读文件
    resolved_json_path = result_directory_path_for_plan_evaluation + f'result_start_at_{timestamp}_bias_info.json'
    result_file_path = result_directory_path_for_plan_evaluation + f'result_start_at_{timestamp}_resolved.json'
    bias_data = open_file(resolved_json_path)
    history_prompt_data = open_file(history_prompt_file_path)
    result_data = open_file(result_file_path)

    # 将数据存到变量中，用于填入到 scoring_prompt 当中
    Accuracy = bias_data.get("Accuracy",'')
    ME = bias_data.get("Mean Error (ME)",'')
    MSE = bias_data.get("Mean Squared Error (MSE)",'')
    Standard_Deviation = bias_data.get("Standard Deviation of Errors",'')
    Higher_error = bias_data.get("Higher_error",'')
    Lower_error = bias_data.get("Lower_error",'')
    Excessive_difference = bias_data.get("Excessive_difference",'')
    Confusion_Matrix = bias_data.get("Confusion Matrix",'')

    parameter_description = f"- Accuracy: {Accuracy}\n- Mean Error: {ME}\n- Mean Squared Error (MSE): {MSE}\n- Standard Deviation of Errors: {Standard_Deviation}\n- Higher Error Count: {Higher_error}\n- Lower Error Count: {Lower_error}\n- Excessive Difference Count: {Excessive_difference}\n- Confusion Matrix: {Confusion_Matrix}"

    scoring_prompt_1 = f"Please evaluate the following function prompt:\n\n'{func_prompt}'\n\nBased on the plan evaluation results, assign a score from 0 to 100, considering the following parameters:\n\n{parameter_description}\n\nComes up with some suggestion for further improvement of this prompt.\nFocus on areas where the mean error and MSE indicate significant room for improvement.\nUtilize insights from the confusion matrix to refine classification logic and reduce misclassifications.\n\nThe Response should be the following format:\n###Score: <here to put the score>\n\n###Ruggestion:\n1. ...\n2. ...\n3. ...",
    scoring_prompt_2 = f"Evaluate the effectiveness of the following function-prompt based on the specified metrics. Provide a score from 0 to 100, along with detailed suggestions for improvement.\n\nFunction_Prompt:\n'{func_prompt}'\n\nEvaluation Metrics:\n\n{parameter_description}\n\nEvaluate the function_prompt, provide score and suggestions for improvement. Considering: 1. Provide specific recommendations based on the evaluation metrics. 2. Identify potential changes or enhancements to the function-prompt. 3. Suggest areas to explore for improving accuracy and reducing errors.\n\nThe Response should be the following format:\n###Score: <here to put the score>\n\n###Ruggestion:\n1. ...\n2. ...\n3. ..."
    scoring_prompt_3 = f"Please conduct a thorough evaluation of the following function prompt:\n\n'{func_prompt}'\n\nUtilizing the provided evaluation metrics, assign a score ranging from 0 to 100. Take into account the following parameters:\n\n{parameter_description}\n\nIn addition, please offer actionable suggestions for enhancing the function prompt. Pay particular attention to areas where the mean error and MSE suggest potential for improvement, and leverage insights from the confusion matrix to optimize classification accuracy.\n\nRespond in the following format:\n### Score: <score here>\n\n### Suggestions:\n1. ...\n2. ...\n3. ..."
    scoring_prompt_4 = f"Evaluate the following function prompt:\n\n'{func_prompt}'\n\nAssign a score from 0 to 100 based on these metrics:\n\n{parameter_description}\n\nProvide clear suggestions for improvement, focusing on areas with high mean error and MSE, and use insights from the confusion matrix to enhance performance.\n\nResponse format:\n### Score: <score>\n\n### Suggestions:\n1. ...\n2. ...\n3. ..."
    scoring_prompt_5 = f"Hey there! Let’s dive into the evaluation of this function prompt:\n\n'{func_prompt}'\n\nCould you give it a score from 0 to 100 based on the following details?\n\n{parameter_description}\n\nAlso, share some tips on how to make it better! Focus on the areas where we can reduce errors and improve classification based on the confusion matrix insights.\n\nFormat your response like this:\n### Score: <your score>\n\n### Suggestions:\n1. ...\n2. ...\n3. ..."
    scoring_prompt_6 = f"Let’s enhance our understanding of the following function prompt:\n\n'{func_prompt}'\n\nPlease evaluate it and assign a score from 0 to 100 using these criteria:\n\n{parameter_description}\n\nYour suggestions for improvement are crucial! Identify areas where we can achieve better results, especially where the mean error and MSE indicate a need for refinement. Let’s work together to optimize our approach based on the confusion matrix.\n\nPlease respond with:\n### Score: <score>\n\n### Suggestions:\n1. ...\n2. ...\n3. ..."

    scoring_prompt_list = [str(scoring_prompt_1), str(scoring_prompt_2), str(scoring_prompt_3), str(scoring_prompt_4), str(scoring_prompt_5), str(scoring_prompt_6)]

    # 存储结果的位置
    result_file_path = result_directory_path_for_plan_evaluation + f'result_start_at_{timestamp}_bias_info_with_prompt_evaluation.json'
    result_list = []

    # 开始调用评估器
    print(f">=============================== Beginning call evaluator ================================<")
    thread = create_thread()

    timestamp_for_prompt_evaluation = datetime.now().strftime("%y-%m-%d %H-%M-%S")

    for t in range(5):
        random_lag()
        miss = False
        prompt = random.sample(scoring_prompt_list, 1)[0]
        assistant_id = random.sample(scorer_assistant_id_list, 1)[0]

        miss, thread = process_for_call_assistant_api(miss=miss, prompt=prompt, assistant_id=assistant_id, thread=thread)
        while True:
            try:
                if miss:
                    print(f"<Result> Eliminated the fail_record to data successfully")
                    break
                print(f"<Processing> Processing response data...")
                message = get_messages(thread.id)
                print(message)
                score, suggestions = get_score_and_suggestion(message)
                result_list.append({"Score": score,"Suggestions": suggestions})
                print(f"Score: {score}")
                print(f"Suggestion: {suggestions}")
                print(f"<Result> save the result to data successfully")
                break
            except Exception as e:
                print(f"<Result> Error: {e}")
                continue

    mean_score = count_final_score_for_func_prompt(result_list)

    final_suggestion = get_final_suggestion_for_improving_instruction(result_list)

    print(f"Mean_score: '{mean_score}'")
    print(f"Final_suggestion: {final_suggestion}")

    bias_data["Func_Prompt"] = func_prompt
    bias_data["Mean_comprehensive_score_for_prompt"] = mean_score
    bias_data["Suggestion_for_improving_instruction"] = final_suggestion
    bias_data["Func_Prompt_eval_time"] = timestamp_for_prompt_evaluation
    bias_data["Comprehensive_scores_for_instruction"] = result_list

    # 将结果存到对应的文件
    save_result_to_json(result_file_path, bias_data)

    # 将 func-prompt 添加到 history_prompt
    bias_data["Result"] = result_data
    bias_data["Parameter_description"] = parameter_description
    history_prompt_data[func_prompt] = bias_data
    # 将结果存到对应的文件
    save_result_to_json(history_prompt_file_path, history_prompt_data)

    print(f"<Result> save the result to data successfully")

    print(f">=============================== Finished call evaluator ================================<")
    return mean_score, final_suggestion



def optimizing_step_1(previous_func_prompt):
    # Setup logging
    logging.basicConfig(
        filename='Optimizing_prompt.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='a'  # Append to the log file
    )
    meta_prompt = generating_meta_prompt(previous_func_prompt)
    timestamp_for_prompt_optimizing = call_optimizer(meta_prompt, previous_func_prompt)
    print(f"timestamp_for_prompt_optimizing: '{timestamp_for_prompt_optimizing}'")



def optimizing_step_2(timestamp_for_prompt_optimizing):

    generated_instruction_path = generated_instruction_directory_path + f"generated_instruction_{timestamp_for_prompt_optimizing}.json"
    generated_instructions_data = open_file(generated_instruction_path)
    history_generated_instruction_path = result_directory_path_for_optimizing + "history_generated_instructions.json"
    history_generated_instruction_data = open_file(history_generated_instruction_path)

    print(f"read instructions complete")
    for instruction, detail in generated_instructions_data.items():
        if generated_instructions_data[instruction]["Evaluation_Status"]:
            print(f"The following instruction has evaluated:\n{instruction}")
        else:
            print(f"<Optimizing> using the following instruction to evaluate plan:\n{instruction}")

            timestamp_for_plan_evaluation = Plan_evaluation(instruction)
            call_evaluator(instruction, timestamp_for_plan_evaluation)

            # update json file
            generated_instructions_data[instruction]["Evaluation_Status"] = True
            history_generated_instruction_data[instruction]["Evaluation_Status"] = True
            save_result_to_json(generated_instruction_path, generated_instructions_data)
            save_result_to_json(history_generated_instruction_path, history_generated_instruction_data)



def Optimizing_auto():
    # Setup logging
    logging.basicConfig(
        filename='Optimizing_prompt.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='a'  # Append to the log file
    )
    previous_func_prompt = thread_prompt_default_v3
    meta_prompt = generating_meta_prompt(previous_func_prompt)
    timestamp_for_prompt_optimizing = call_optimizer(meta_prompt)
    generated_instruction_path = generated_instruction_directory_path + f"generated_instruction_{timestamp_for_prompt_optimizing}.json"

    generated_instructions_data = open_file(generated_instruction_path)
    print(f"read instructions complete")
    for instruction, detail in generated_instructions_data.items():
        print(f"<Optimizing> using the following instruction to evaluate plan:\n{instruction}")
        timestamp_for_plan_evaluation = Plan_evaluation(instruction)
        call_evaluator(instruction, timestamp_for_plan_evaluation)
        generated_instructions_data[instruction]["Evaluation_Status"] = True
        save_result_to_json(generated_instruction_path, generated_instructions_data)




#optimizing_step_2('')

#ins = "Task: Analyze the County Comprehensive Development Plan with respect to the specified indicator using a precise and comprehensive scoring system.\n\nScoring Criteria:\n- **0 Points (Not Acknowledged):** The plan fails to refer to or incorporate the indicator, indicating no awareness or relevance.\n- **1 Point (Minimal Mention):** The plan refers to the indicator briefly, lacking in-depth analysis or clear linkages to objectives. Implementation strategy and evidence are sparse or insufficient.\n- **2 Points (Comprehensively Addressed):** The plan offers detailed treatment of the indicator, with explicit, evidence-based strategies, showcasing practical feasibility and strong strategic integration with the plan\u2019s core goals.\n\nEvaluation Instructions:\n- Utilize a detailed rubric with specific, quantifiable descriptors for each score level, ensuring clear differentiation between superficial and thorough treatment.\n- Provide a well-substantiated score, supported by specific examples and quantifiable evidence from the plan.\n- Engage in evaluative calibration sessions regularly, using real-time tools to minimize scoring inconsistencies and enhance overall accuracy.\n\nIncorporate feedback and continuous learning through structured workshops and technology-enabled systems to improve uniform application of the scoring framework."
#call_evaluator(func_prompt=ins, timestamp='')

ins = "Task: Critically assess the provided County Comprehensive Development Plan focusing on a specified indicator by following a structured evaluation framework.\n\nScoring Criteria: \n- **0 - Not Acknowledged (0 points):** The plan lacks any reference to the indicator. Demonstrates no recognition of its importance or relevance.\n- **1 - Acknowledged but Lacking Depth (1 point):** The plan mentions the indicator but in a limited context. Explanation lacks detailed alignment with objectives, missing actionable steps or evidence-backed support. \n- **2 - Fully Integrated and Elaborate (2 points):** The plan provides a comprehensive treatment of the indicator, offering detailed strategies, evidence-based alignment with goals, and realistic implementation steps. It clearly demonstrates how the indicator is vital to the plan\u2019s success.\n\nInstructions for Evaluation:\n- Use a structured rubric to assess plan components against scoring criteria, detailing examples and thresholds for each score. \n- Assign points by verifying if the plan meets the necessary conditions - for a score of 2, ensure thoroughness, feasibility, and strategic relevance. \n- Document findings and justification clearly for the chosen score (0, 1, or 2).\n\nEnhanced Guidance and Monitoring:\n- Participate in evaluator calibration sessions and leverage technology-assisted tools for consistent application of scoring criteria.\n- Regularly engage in workshops to refine understanding and application of evaluation metrics, reducing variance and increasing accuracy.\n\nReach out for further clarifications through established feedback channels if scoring challenges arise."

#timestamp_for_prompt_optimizing = optimizing_step_1(previous_func_prompt=ins)
#print(f"timestamp_for_prompt_optimizing: '{timestamp_for_prompt_optimizing}'")
#optimizing_step_2(timestamp_for_prompt_optimizing="")

generating_meta_prompt(ins)
