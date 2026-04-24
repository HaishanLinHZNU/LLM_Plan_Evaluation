import sys
from openai import OpenAI
from time import sleep
import random
import json
import logging
from tqdm import tqdm
import os
from Writing_result import add_data, save_result_to_json, create_Result_json_file
from Get_vector_store_id import get_vector_store_id
from Resolve_the_result_of_Plan_Evaluation import Change_Plan_Evaluation_from_json_to_xlsx, printing_bias_info

api_key = ""
api_base = ''

indicator_data_path = r"D:/Plans_Evaluation/Parameter/__xlsx2json_output_fall_data_part_2__.json"
vector_store_data_path = r"D:/Plans_Evaluation/Parameter/__File_info_full_data__.json"
indicator_generated_info_path = r"D:/Plans_Evaluation/Parameter/__indicators_with_Scoring_Framework__.json"
assistant_id_for_part_path = r"D:/Plans_Evaluation/Parameter/__assistant_id_for_each_part__.json"
result_directory_path = "D:/Plans_Evaluation/Result_of_Plan_Evaluation/"

__Part__ = "Part_2"

thread_prompt_default_v2 = "You are an expert Comprehensive Development Plan analyst. Use you knowledge base, which is a County Comprehensive Development Plan, evaluate the provided Plan against the given indicator according to the Scoring Criteria.\nTask: Evaluate the provided County Comprehensive Development Plan against the given indicator.\nScoring Criteria: Assign a score from 0 to 2 for the indicator based on the following definitions: 0 - Does Not Match: The plan does not address or mention the indicator. 1 - Basically Matches: The plan mentions the indicator but lacks detail, depth, or only tangentially addresses it. 2 - Totally Matches: The plan thoroughly addresses the indicator with detailed information and in-depth analysis.\nExpected Response: Provide a single score (0, 1, or 2) based on the criteria above. No additional text is needed."
thread_prompt_default_v3 = "Task: Evaluate the provided County Comprehensive Development Plan against the given indicator. \n\nScoring Criteria: \n0 - Does Not Match (0 points) \nThe plan does not address or mention the indicator at all. No effort is made to incorporate or consider the indicator. Shows no understanding of the indicator's relevance. \n\n1 - Partially Matches (1 point) \nThe plan briefly mentions the indicator but lacks depth or specificity. The mention might be tangential or incomplete, not fully aligned with the objectives. The explanation is minimal and may not seem practical or well-supported. Feasibility and integration with the overall plan are weak or unclear. \n\n2 - Fully Matches (2 points) \nThe plan thoroughly addresses the indicator with detailed, specific content. Provides a clear explanation of how the indicator will be implemented. The approach is realistic, well-supported by evidence, and feasible. Demonstrates strategic alignment with the plan's goals, showing how the indicator plays a critical role in its success. \n\nInstructions for Scoring: \nBe critical and cautious when awarding 2 points. Only give a score of 2 if all conditions are clearly met (thorough explanation, high feasibility, strategic integration). If the plan addresses the indicator but lacks depth, clarity, or feasibility, lean towards a score of 1. If the indicator is not addressed or its relevance is not demonstrated, assign a score of 0. \n\nExpected Response: \nProvide a single score (0, 1, or 2) based on the criteria above, and the reason or factual base of it. "
structural_response_instruction = "\n\nResponse Format: \n### Score: <here to put the score (only number range in 0, 1, and 2)>\n\n### Reason:\n1. ...\n2. ...\n3. ...\n..."

default_instruction = "Task: Conduct a comprehensive evaluation of the County Comprehensive Development Plan regarding a specified indicator, using an enhanced scoring system that captures nuanced assessments.  \n\nScoring Framework:  \n- **0 - Not Addressed (0 points):** The plan fails to mention or incorporate the indicator, demonstrating no acknowledgement of its significance. The indicator is mentioned but superficially, with limited context and unsupported relevance.  \n- **1 - Discussed with Insufficient Depth (1 point):** The plan references the indicator without integrating it meaningfully into its objectives. Lack of actionable strategies or evidence of impact is evident. The indicator is integrated with some strategic relevance and partial evidence but lacks full feasibility or comprehensive linkage to goals.  \n- **2 - Thoroughly Integrated (2 points):** The indicator is meticulously woven into the plan with established evidence, reflective of strategic relevance and clear feasibility in alignment with broader objectives.  \n\nEvaluation Process:  \n- Utilize a detailed and structured rubric to assess the plan's alignment with each scoring level, carefully noting examples and evidence.  \n- Validate the assigned score by comparing plan elements to criteria benchmarks, ensuring thorough and strategic integration for higher scores.  \n- Engage in regular training and calibration workshops to refine scoring accuracy and consistency, reducing errors and variance across evaluations.  \n- Leverage advanced analytical and AI-assisted tools for real-time feedback and pattern recognition, enhancing the precision of assessments.  \n\nConclude evaluations with well-documented justifications for scores, fostering clarity and transparency. Refer back to established feedback channels for resolving any scoring discrepancies or challenges."

__thread_id__ = ''

client = OpenAI(api_key=api_key, base_url=api_base)



# Function to read and process the JSON file
def read_data(filepath, target=""):
    '''
    load json data
    '''
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)
    print(f"{target} <Reading data> finish reading data from '{filepath}'.")
    return data



def random_folat(min_val=0.3,max_val=1.3):
    return min_val + (max_val - min_val) * random.random()



def random_lag(lag_min=1.3, lag_max=2.3):
    # Generate a random delay between 1 and 11 seconds
    if lag_max < 4:
        sleep(random_folat(min_val=lag_min, max_val=lag_max))
    else:
        sleep(random_folat(min_val=lag_max/2, max_val=lag_max))


def verify_file_exists(file_path):
    """Check if the specified file exists."""
    if os.path.isfile(file_path):
        return True
    else:
        return False

def verify_if_county_already_processed(data, county_name):
    for c_name, _ in data.items():
        if county_name == c_name:
            return True
    return False

def verify_if_indicator_already_processed(data, county_name, indicator_waiting_for_process):
    for items in data[county_name]:
        if indicator_waiting_for_process == items['indicator']:
            return True
    return False



def create_assistants(instructions, tools=[], assistant_name="Plans analyzing assistant", model="gpt-3.5-turbo", vector_store_id=[]):
    '''
    return an assistant object
    '''
    random_lag()
    if vector_store_id:
        assistant = client.beta.assistants.create(
            name=assistant_name,
            instructions=instructions,
            tools=tools,
            model=model,
            tool_resources={
                "file_search": {
                    "vector_store_ids": vector_store_id
                }
            }
        )
    else:
        assistant = client.beta.assistants.create(
            name=assistant_name,
            instructions=instructions,
            tools=tools,
            model=model,
        )
    return assistant



# 创建线程
def create_thread(vector_store_id, target=""):
    '''
    create a thread attaching vector store

    return a thread object
    '''
    i=3
    while True:
        try:
            print(f"{target} <create_thread> Creating new thread")
            random_lag(1.3,i)
            thread = client.beta.threads.create(
                tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}
            )
            print(f"{target} <create_thread> [Complete]")
            return thread
        except Exception as e:
            print(f"{target} <create_thread> Fail to create new thread. with error: '{e}'")
            print(f"{target} <create_thread> Retrying...")
            i+=1
            continue



def run_assistant(thread_id, assistant_id, target=""):
    '''
    create a run using thread id and assistant id

    return a run object
    '''
    i=3
    while True:
        try:
            random_lag(1.3,i)
            print(f"{target} <run_assistant> creating run")
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
            )
            print(f"{target} <run_assistant> [Complete]")
            return run
        except Exception as e:
            text = f"{target} <run_assistant> fail to create run with [{e}]. [Fail]"
            if "already has an active run" in text:
                print(f"{target} <run_assistant> An activate run already exist, fail to create new run.")
                return None
            print(text)
            i+=1
            continue



def retrieve_run(thread_id, run_id):
    '''
    check the realtime parameter of a run

    return a run object
    '''
    random_lag()
    run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
    return run



def list_messages(thread_id, target=""):
    '''
    Get the messages from a thread (not resolved messages)

    return a list (of messages)
    '''
    i = 3
    while True:
        try:
            random_lag(1.3,i)
            print(f"{target} <list message> Getting message from response...")
            thread_messages = client.beta.threads.messages.list(thread_id=thread_id)
            print(f"{target} <list message> [Complete]")
            return thread_messages
        except Exception as e:
            print(f"{target} <list message> Fail to get message with exception [{e}].")
            print(f"{target} <list message> Retrying...")
            i+=1
            continue



def list_run_steps_result(thread_id, run_id, target=""):
    '''
    Get the middle result from runsteps (not resolved results of file search)

    return a list (of results of file search)
    '''
    while True:
        try:
            random_lag()
            print(f"{target} <list run_step> Getting result of run_step from response...")
            run_step = (client.beta.threads.runs.steps.list(
                thread_id=thread_id,
                run_id=run_id,
                include=["step_details.tool_calls[*].file_search.results[*].content"]
            ))
            print(f"{target} <list run_step> [Complete]")
            return run_step
        except Exception as e:
            print(f"{target} <list run_step> Fail to get result of run_step with exception [{e}].")
            print(f"{target} <list run_step> Retrying...")
            continue



def get_file_search(run_steps, target=""):
    '''
    resolve the results of file search, the references and their score of relevancy

    arg: a list of middle result from runsteps

    return: original data of reference, and the resolve dictionary, storing Factual_base and its relevancy score pear, list
    '''
    references = None
    factual_basis = []
    try:
        print(f"{target} <Get references> Getting references...")
        references = run_steps.data[1].step_details.tool_calls[0].file_search.results
        print(f"{target} <Get references> Complete")

        # 从 result 列表 (reference) 中获取依据与对应相似度分数
        for result in references:
            factual_basis.append({"Factual_base": result.content[0].text, "Score": result.score})

    except Exception as e:
        logging.error(f"{target} <Get references> An error occurred while getting data from reference: {e}")
        print(f"{target} <Get references> An error occurred while getting data from reference: {e}")

    return references, factual_basis



def get_message(messages):
    '''
    Get the previous response from message list

    arg: a list of messages (from list_messages(thread_id))

    return: a string message
    '''
    message = messages.data[0].content[0].text.value
    return message



def get_indicator_and_score(messages):
    '''
    get the input indicator and the response of it

    basically is just get the last two data from messages list

    return: indicator, the request message, and response text
    '''
    response = messages.data[0].content[0].text.value
    indicator = messages.data[1].content[0].text.value
    return indicator, response



# 使用相同的thread_id
def using_thread(prompt, thread_id, target=""):
    i=3
    while True:
        try:
            random_lag(1.3,i)
            print(f"{target} <thread_update> adding message to thread...")
            message = client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=prompt
            )
            print(f"{target} <thread_update> thread update completed [Complete]")
            return message
        except Exception as e:
            print(f"{target} <thread_update> Fail to add message with exception [{e}].")
            print(f"{target} <thread_update> Retrying...")
            i+=1
            continue



def create_file(file_path, target=""):
    '''
    arg: path of file to be uploaded (str)

    return: OpenAI API file object
    '''
    i=3
    while True:
        try:
            print(f"{target} <Create_file> Creating file...")
            random_lag(1.3,i)
            file = client.files.create(file=open(file_path, "rb"), purpose="assistants")
            print(f"{target} <Create_file> File create completed [Complete]")
            return file
        except Exception as e:
            print(f"{target} <Create_file> Fail to Creat file with exception [{e}] [Fail]")
            print(f"{target} <Create_file> Retrying...")
            i+=1
            continue



def updating_assistant_instruction_and_model(assistant_id, instruction, target="", model="gpt-4o-mini", temperature=1.0):
    '''
    to change the instruction used by assistant, according to assistant id and instruction text

    arg: assistant_id (str),
         instruction (str),
         model (str)

    return: OpenAI API assistant object.
    '''
    print(f"{target} <Assistant update> Updating assistant instruction and model...")
    i=3
    while True:
        try:
            random_lag(1.3,i)
            assistant = client.beta.assistants.update(
                assistant_id=assistant_id,
                instructions=instruction,
                model=model,
                temperature=temperature
            )
            print(f'{target} <Assistant update> Assistant update instruction completed')
            return assistant
        except Exception as e:
            logging.error(f"{target} <Assistant update> Error updating assistant with instruction: '{instruction}' {e}")
            print(f"{target} <Assistant update> Error updating assistant with instruction: '{instruction}' {e}")
            i+=1
            continue



def updating_assistant_vector_store(assistant_id, vector_store_id, target="", temperature=1.0, max_num_results=10):
    '''
    to change the vector store used by assistant, according to assistant id and vector store id

    arg: assistant_id (str),
         vector_store_id (str)

    return: OpenAI API assistant object.
    '''
    i=3
    while True:
        try:
            random_lag(1.3,i)
            assistant = client.beta.assistants.update(
                assistant_id=assistant_id,
                tools=[
                    {
                        "type": "file_search",
                        "file_search": {"max_num_results": max_num_results}  # Set max number of results here
                    }
                ],
                tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
                temperature=temperature
            )
            print(f'{target} <Assistant update> Assistant update vector store completed [Complete]')
            return assistant
        except Exception as e:
            logging.error(f"{target} <Assistant update> Error updating assistant with Vector Store id: '{vector_store_id}' {e}")
            print(
                f"{target} <Assistant update> Error updating assistant with Vector Store id: '{vector_store_id}'\n{target} <update> Error:{e}")
            i+=1
            continue



def updating_assistant_max_num_results_for_file_search(assistant_id, max_num_results, target="", temperature=1.0):
    '''
    to change the vector store used by assistant, according to assistant id and vector store id

    arg: assistant_id (str),
         vector_store_id (str)

    return: OpenAI API assistant object.
    '''
    i=3
    while True:
        try:
            random_lag(1.3,i)
            assistant = client.beta.assistants.update(
                assistant_id=assistant_id,
                tools=[
                    {
                        "type": "file_search",
                        "file_search": {"max_num_results": max_num_results}  # Set max number of results here
                    }
                ],
                temperature=temperature
            )
            print(f'{target} <Assistant update> Assistant update max_num_results completed [Complete]')
            return assistant
        except Exception as e:
            logging.error(f"{target} <Assistant update> Error updating assistant with max_num_results: '{max_num_results}' {e}")
            print(
                f"{target} <Assistant update> Error updating assistant with max_num_results: '{max_num_results}'\n{target} <update> Error:{e}")
            i+=1
            continue



def print_result_for_each_indicator(input_text, score, indicator, target=""):
    '''
    Print result of each indicator
    '''
    line = f">----------------------------------------------------------------------------------------------<"
    print(f"{target} <Processing> Process Completed [Complete]\n{line}")
    print(f"{target} <Result> input_text: '{input_text}'\n{line}")
    print(f"{target} <Result> Response: \n'{score}'\n{line}")
    logging.info(f"Evaluation complete for indicator: {indicator} with score: {score}")



def knowledge_retrieve(instruction=default_instruction, model="gpt-4o-mini", timestamp_for_resuming=None, temperature=1.0):

    total_count = 0
    processing_no = 1
    assistant_id_data = read_data(assistant_id_for_part_path, f"[{processing_no}/{total_count}]")

    assistant_id = assistant_id_data[__Part__] # default using GPT 4o mini

    logging.info(f"Starting knowledge retrieval'")
    print(f"Starting knowledge retrieval\n>==============================================================================================<")
    print(f"[{processing_no}/{total_count}] <Reading data> Reading data...")

    if timestamp_for_resuming == None:
        # 创建结果存储的基本信息
        result_file_path, timestamp = create_Result_json_file(retult_directory_path=result_directory_path, part=__Part__)
        result_data = {}
        logging.info(f"Result file created at '{result_file_path}'")
    elif timestamp_for_resuming:
        file_path = f"{result_directory_path}{__Part__}_result_start_at_{timestamp_for_resuming}.json"
        if verify_file_exists(file_path):
            result_file_path = file_path
            timestamp = timestamp_for_resuming
            result_data = read_data(result_file_path, f"[{processing_no}/{total_count}]")
        else:
            print(f"<timestamp error> can not find a json file at '{file_path}'")
            sys.exit()
    else:
        print(f"<timestamp error> ......")
        sys.exit()



    # 从 indicator_info 和 vector_store_info 读取信息
    try:
        indicator_data = read_data(indicator_data_path, f"[{processing_no}/{total_count}]")  # 读取 County-Indicator 的信息
        vector_store_data = read_data(vector_store_data_path, f"[{processing_no}/{total_count}]")  # 读取 County-Vector_Store_id 的信息
        indicator_generated_info = read_data(indicator_generated_info_path, f"[{processing_no}/{total_count}]")  # 读取生成的 indicator 的解释和评分标准
        logging.info( f"Successfully read indicator data from '{indicator_data_path}' and vector store data from '{vector_store_data_path}'")
    except Exception as e:
        logging.error(f"An error occurred while reading data: {e}")
        print(f"[{processing_no}/{total_count}] <Reading data> An error occurred While reading data: {e}")
        return

    # 任务计数
    for county, indicators in indicator_data.items():
        total_count += len(indicators)

    # 更新 assistant
    updating_assistant_instruction_and_model(assistant_id=assistant_id,
                                             instruction=(instruction + structural_response_instruction),
                                             target=f"[{processing_no}/{total_count}]",
                                             model=model,
                                             temperature=temperature)

    # 循环进行评估处理数据
    for county_name, indicators in tqdm(indicator_data.items(), desc=f"Evaluation"):
        print(f">=============================== Processing county: {county_name} ================================<")

        '''<检查当前郡是否已经完成，若是则跳过更新 assistant 和创建 thread 的部分>'''
        finish_mark = True
        for item in indicators:
            indicator = item['indicator']
            if verify_if_county_already_processed(result_data, county_name):
                if verify_if_indicator_already_processed(result_data, county_name, indicator):
                    print(
                        f"[{processing_no}/{total_count}] <EXIST> Already process indicator: '{indicator}' for County: '{county_name}'")
                    processing_no += 1
                    continue
            else:
                finish_mark = False
                break
            finish_mark = False

        if finish_mark:
            continue
        '''</检查当前郡是否已经完成，若是则跳过更新 assistant 和创建 thread 的部分>'''

        try:
            # 读取当前 County 对应的 Vector Store id
            print(f"[{processing_no}/{total_count}] <Processing> Processing county: '{county_name}'")
            logging.info(f"Processing county: '{county_name}'")
            vector_store_id = get_vector_store_id(vector_store_data, county_name)
            print(f"[{processing_no}/{total_count}] <Processing> Switching vector store to id: '{vector_store_id}'...")
            if not vector_store_id:
                raise ValueError(f"Vector store ID not found for county: '{county_name}'")

            # 根据 Vector Store id 更新 assistant 的向量存储
            updating_assistant_vector_store(assistant_id=assistant_id, vector_store_id=vector_store_id, target=f"[{processing_no}/{total_count}]", temperature=temperature)
            __max_num_results__ = 5
            logging.info(f"Updated assistant with vector store ID: '{vector_store_id}' for county: '{county_name}'")
            print(f"[{processing_no}/{total_count}] <Processing> Switching successfully. Updated assistant with vector store ID: '{vector_store_id}' for county: '{county_name}'")
        except Exception as e:
            logging.error(f"[{processing_no}/{total_count}] <Processing> Error Switching vector store for county '{county_name}': {e}")
            print(f"[{processing_no}/{total_count}] <Processing> Error Switching vector store for county '{county_name}': {e}")
            continue

        '''<Creating new thread for single County Plan Evaluation>'''
        try:
            thread = create_thread(vector_store_id=vector_store_id, target=f"[{processing_no}/{total_count}]")
            __thread_id__ = thread.id
            run = run_assistant(thread_id=__thread_id__, assistant_id=assistant_id, target=f"[{processing_no}/{total_count}]")
            i_create_thread = 0
            '''<run>'''
            while True:
                run = retrieve_run(thread_id=__thread_id__, run_id=run.id)
                if run.status == "completed":
                    break
                random_lag(1.3, i_create_thread)
                print(f"[{processing_no}/{total_count}] <Create thread> Creating...")

                if i_create_thread % 10 == 0 and i_create_thread != 0:
                    print(f"[{processing_no}/{total_count}] <Run> Retrying create_thread and Run_assistant...")
                    thread = create_thread(vector_store_id=vector_store_id, target=f"[{processing_no}/{total_count}]")
                    __thread_id__ = thread.id
                    run = run_assistant(thread_id=__thread_id__, assistant_id=assistant_id, target=f"[{processing_no}/{total_count}]")
                    print(f"[{processing_no}/{total_count}] <Run> Wait for completion of the run. The {i_create_thread} times trying...")
                elif i_create_thread % 5 == 0 and i_create_thread != 0:
                    print(f"[{processing_no}/{total_count}] <Create thread> Fail [Fail]")
                    print(f"[{processing_no}/{total_count}] <Create thread> Retrying create thread...")
                    run_ = run_assistant(thread_id=__thread_id__, assistant_id=assistant_id, target=f"[{processing_no}/{total_count}]")
                    if run_ == None:
                        pass
                    else:
                        run = run_
                if i_create_thread >= 25:
                    print(f"[{processing_no}/{total_count}] <Create thread> Fail to get response.")
                    break
                i_create_thread += 1
                print(f"[{processing_no}/{total_count}] <Create thread> Wait for completion of the thread creation. The {i_create_thread} times trying...")
                '''</Run>'''
            print(f"[{processing_no}/{total_count}] <create_thread> Compleat. Thread_id:'{__thread_id__}'")
        except Exception as e:
            logging.error(f"[{processing_no}/{total_count}] <Processing> Error creating thread for county '{county_name}': {e}")
            print(f"[{processing_no}/{total_count}] <Processing> Error creating thread for county '{county_name}': {e}")
        '''</Creating new thread for single County Plan Evaluation>'''

        # Processing each indicator
        for item in tqdm(indicators, desc=f"Processing {county_name}...", leave=False):

            miss = False
            #random_lag()
            indicator = item['indicator']
            value = item['value']

            '''<跳过已经完成评估的 indicator>'''
            if verify_if_county_already_processed(result_data, county_name):
                if verify_if_indicator_already_processed(result_data, county_name, indicator):
                    continue
            '''<、跳过已经完成评估的 indicator>'''

            print(f">----------- Indicator: {indicator} -----------<")
            print(f"[{processing_no}/{total_count}] <Processing> Evaluating indicator: '{indicator}' for county: '{county_name}'")
            logging.info(f"Evaluating indicator: '{indicator}' for county: '{county_name}'")


            '''<Prompt>'''

            scoring_framework = indicator_generated_info[indicator]['Best_Scoring_Framework']

            interpretation = indicator_generated_info[indicator]['Scoring_Frameworks'][scoring_framework]['Interpretation_LLM']



            prompt = f"indicator: '{indicator}'. \n\nHere is the interpretation of the indicator: \n{interpretation}\n\nScoring framework:\n{scoring_framework}\n\nEvaluate the provided 'The {county_name} County Comprehensive Development Plan' against the given indicator. {structural_response_instruction}"  # accuracy: 56

            #prompt = f"indicator: '{indicator}'. \n\nHere is the interpretation of the indicator: \n{interpretation}\n\nHere the detail evaluate criteria:\n{sub_Criteria}\n\n{scoring_framework}\n\nEvaluate the provided 'The {county_name} County Comprehensive Development Plan' against the given indicator. {structural_response_instruction}"  # accuracy: 58

            #prompt = f"indicator: '{indicator}'. {scoring_framework}  Evaluate the provided 'The {county_name} County Comprehensive Development Plan' against the given indicator. {structural_response_instruction}"  # accuracy: 56

            #prompt = f"indicator: '{indicator}'. Evaluate the provided 'The {county_name} County Comprehensive Development Plan' against the given indicator."

            #prompt = f"indicator: '{indicator}'. Evaluate the provided comprehensive development plan against the given indicator."

            '''</Prompt>'''

            while True:
                try:
                    using_thread(prompt, __thread_id__, f"[{processing_no}/{total_count}]")
                    run = run_assistant(__thread_id__, assistant_id, f"[{processing_no}/{total_count}]")

                    i_run = 0
                    # Wait for completion of the run
                    print(f"[{processing_no}/{total_count}] <Run> begin to Run...")
                    while True:
                        i_run += 1
                        run = retrieve_run(thread_id=__thread_id__, run_id=run.id)
                        if run.status == "completed":
                            print(f"[{processing_no}/{total_count}] <Run> Run completed [Complete]")
                            break

                        random_lag(lag_min=1, lag_max=i_run)
                        if i_run%11 == 0 and i_run!=0:
                            print(f"[{processing_no}/{total_count}] <Run> Retrying create_thread and Run_assistant...")
                            thread = create_thread(vector_store_id=vector_store_id,
                                                   target=f"[{processing_no}/{total_count}]")
                            __thread_id__ = thread.id
                            using_thread(prompt, __thread_id__, f"[{processing_no}/{total_count}]")
                            run = run_assistant(__thread_id__, assistant_id, f"[{processing_no}/{total_count}]")
                            print(f"[{processing_no}/{total_count}] <Run> Wait for completion of the run. The {i_run} times trying...")
                        elif i_run % 7 == 0 and i_run != 0:
                            print(f"[{processing_no}/{total_count}] <Run> Retrying Run_assistant...")
                            run_ = run_assistant(__thread_id__, assistant_id, f"[{processing_no}/{total_count}]")
                            if run_ == None:
                                pass
                            else:
                                run = run_
                            print(f"[{processing_no}/{total_count}] <Run> Wait for completion of the run. The {i_run} times trying...")
                        else:
                            print(f"[{processing_no}/{total_count}] <Run> Wait for completion of the run. The {i_run} times trying...")
                        if i_run >= 31:
                            print(f"[{processing_no}/{total_count}] <Run> Fail to get response.")
                            miss = True
                            break
                    break
                except Exception as e:
                    logging.error(f"Error processing indicator {indicator} for county {county_name}: {e}")
                    print(f"Error processing indicator {indicator} for county {county_name}: {e}")
                    continue
            while True:
                try:
                    if miss:
                        messages_temp = list_messages(__thread_id__, f"[{processing_no}/{total_count}]")
                        run_steps_temp = list_run_steps_result(thread_id=__thread_id__, run_id=run.id,
                                                               target=f"[{processing_no}/{total_count}]")
                        references_temp, factual_basis_temp = get_file_search(run_steps=run_steps_temp,
                                                                              target=f"[{processing_no}/{total_count}]")
                        result_data = add_data(data=result_data, county_name=county_name, indicator=indicator,
                                               input_text="Get no response", value=value, score='None',
                                               messages=str(messages_temp), run_steps=run_steps_temp,
                                               references=references_temp, factual_basis=factual_basis_temp)
                        print(f"[{processing_no}/{total_count}] <Result> save the fail_record to data successfully")
                        break
                    print(f"[{processing_no}/{total_count}] <Processing> Processing response data...")
                    messages = list_messages(__thread_id__, f"[{processing_no}/{total_count}]")
                    run_steps = list_run_steps_result(__thread_id__, run.id, f"[{processing_no}/{total_count}]")
                    input_text, score = get_indicator_and_score(messages)
                    print_result_for_each_indicator(input_text, score, indicator, f"[{processing_no}/{total_count}]")

                    references, factual_basis = get_file_search(run_steps=run_steps,
                                                                target=f"[{processing_no}/{total_count}]")

                    result_data = add_data(data=result_data, county_name=county_name, indicator=indicator,
                                           input_text=input_text, value=value, score=score, messages=str(messages),
                                           run_steps=run_steps, references=references, factual_basis=factual_basis)
                    print(f"[{processing_no}/{total_count}] <Result> save the result to data successfully")
                    break
                except Exception as e:
                    logging.error(f"Error processing indicator {indicator} for county {county_name}: {e}")
                    print(f"Error processing indicator {indicator} for county {county_name}: {e}")
                    continue

            # Saving the result to json file.
            try:
                save_result_to_json(result_file_path, result_data)
                print(f"\n[{processing_no}/{total_count}] <Result> Results is saved successfully.")
                logging.info(f"[{processing_no}/{total_count}] <Result> Results is saved successfully.")
            except Exception as e:
                logging.error(f"[{processing_no}/{total_count}] <Result> Error saving result data: {e}")
                print(f"[{processing_no}/{total_count}] <Result> Error saving result data: {e}")
            print(f">{'-'*50}<")
            printing_bias_info(result_file_path, timestamp)
            print(f">{'-' * 50}<")
            processing_no += 1

    # Saving the result to json file.
    try:
        save_result_to_json(result_file_path, result_data)
        print(f"[{processing_no}/{total_count}] <Result> Results successfully saved to {result_file_path}")
        logging.info(f"Results successfully saved to {result_file_path}")
    except Exception as e:
        logging.error(f"[{processing_no}/{total_count}] <Result> Error saving result data: {e}")
        print(f"[{processing_no}/{total_count}] <Result> Error saving result data: {e}")

    return result_file_path, timestamp


# 主函数
def Plan_evaluation(instruction=default_instruction, model="gpt-4o-mini", timestamp_for_resuming=None, temperature=1.0):
    # Setup logging
    logging.basicConfig(
        filename='Plan_evaluation.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='a'  # Append to the log file
    )
    result_file_path, timestamp = knowledge_retrieve(instruction, model, timestamp_for_resuming=timestamp_for_resuming, temperature=temperature)
    Change_Plan_Evaluation_from_json_to_xlsx(result_file_path, timestamp)
    print(f"Max_num_result = {10}")
    return timestamp

# Plan_evaluation(timestamp_for_resuming="")

# Plan_evaluation()