from openai import OpenAI
from time import sleep
import random
import re
import json
import Call_assistant_api as CALL
from datetime import datetime
import winsound
from Writing_result import save_result_to_json, create_Result_json_file
from Get_vector_store_id import get_vector_store_id
from Resolve_the_result_of_Plan_Evaluation import Change_Plan_Evaluation_from_json_to_xlsx, printing_bias_info


# 设置API密钥和代理地址
api_key = ""
api_base = "https://api.openai.com/v1"

# indicator_data_path = r"./Indicators/xlsx2json_output_3_fall_data.json"
indicator_data_path = r"./Indicators/xlsx2json_output_3.json"
vector_store_data_path = r"./NE_Plans/Plans picked according to completeness (county)/Files_info.json"
indicator_generated_info_path = r"./Indicators/indicators_with_generating_info_with_scoring_framework_cleaned_file.json"

context = "Wetland is the key word in this evaluation. Wetlands are areas where water covers the soil, or is present either at or near the surface of the soil all year or for varying periods of time during the year, including during the growing season. Water saturation (hydrology) largely determines how the soil develops and the types of plant and animal communities living in and on the soil. Wetlands may support both aquatic and terrestrial species. The prolonged presence of water creates conditions that favor the growth of specially adapted plants (hydrophytes) and promote the development of characteristic wetland (hydric) soils. Wetlands are usually classified according to soil and plant life as bogs, marshes, swamps, fens, and other similar environments. As a result, word wetlands, bogs, marshes, swamps, equals wetlands. Nebraska local conservation lands or programs such as wildlife management area (WMA), waterfowl production areas (WPA), conservation easement (CE) are regarded as strong linkage with wetlands.\nThe normal code for plan evaluation is using the indicators below. The evaluation uses 0-1-2 system. Each indicator represents one direction of the evaluation. If the plan gets well performance in that direction will get 2 points for that indicator. If the plan has normal performance in that direction will get 1 point for that indicator. If the plan does not shown what the indicator represents will get 0 point for that indicator. "

Scoring_Framework_path = r"./Indicators/indicators_with_Scoring_Framework_with_MSE.json"
indicator_county_path = r"./Indicators/xlsx2json_output_test_fall_data_indicator_county.json"
optimization_result_path = r"./Result_of_Optimizing_interpretation_and_scoring_framework/"

new_scoring_framework_path = r"./Indicators/indicators_with_generating_info_dict_for_modify_modified_at_24-10-30 19-17-56_extracted_cleaned.json"

vs_id = ""

default_instruction = "Task: Conduct a comprehensive evaluation of the County Comprehensive Development Plan regarding a specified indicator, using an enhanced scoring system that captures nuanced assessments.  \n\nScoring Framework:  \n- **0 - Not Addressed (0 points):** The plan fails to mention or incorporate the indicator, demonstrating no acknowledgement of its significance. The indicator is mentioned but superficially, with limited context and unsupported relevance.  \n- **1 - Discussed with Insufficient Depth (1 point):** The plan references the indicator without integrating it meaningfully into its objectives. Lack of actionable strategies or evidence of impact is evident. The indicator is integrated with some strategic relevance and partial evidence but lacks full feasibility or comprehensive linkage to goals.  \n- **2 - Thoroughly Integrated (2 points):** The indicator is meticulously woven into the plan with established evidence, reflective of strategic relevance and clear feasibility in alignment with broader objectives.  \n\nEvaluation Process:  \n- Utilize a detailed and structured rubric to assess the plan's alignment with each scoring level, carefully noting examples and evidence.  \n- Validate the assigned score by comparing plan elements to criteria benchmarks, ensuring thorough and strategic integration for higher scores.  \n- Engage in regular training and calibration workshops to refine scoring accuracy and consistency, reducing errors and variance across evaluations.  \n- Leverage advanced analytical and AI-assisted tools for real-time feedback and pattern recognition, enhancing the precision of assessments.  \n\nConclude evaluations with well-documented justifications for scores, fostering clarity and transparency. Refer back to established feedback channels for resolving any scoring discrepancies or challenges."
structural_response_instruction = "\n\nResponse Format: \n### Score: <here to put the score (only number range in 0, 1, and 2)>\n\n### Reason:\n1. ...\n2. ...\n3. ...\n..."

default_scoring_framework = "0 - Does Not Match (0 points) - The plan does not address or mention the indicator at all. No effort is made to incorporate or consider the indicator. Shows no understanding of the indicator's relevance. \n\n1 - Partially Matches (1 point) - The plan briefly mentions the indicator but lacks depth or specificity. The mention might be tangential or incomplete, not fully aligned with the objectives. The explanation is minimal and may not seem practical or well-supported. Feasibility and integration with the overall plan are weak or unclear. \n\n2 - Fully Matches (2 points) - The plan thoroughly addresses the indicator with detailed, specific content. Provides a clear explanation of how the indicator will be implemented. The approach is realistic, well-supported by evidence, and feasible. Demonstrates strategic alignment with the plan's goals, showing how the indicator plays a critical role in its success."


line = '>'+'='*80+'<'

__thread_improving_id__ = ''
__thread_evaluating_id__ = ''

client = OpenAI(api_key=api_key, base_url=api_base)



def read_data(filepath):
    '''
    load json data
    '''
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)
    print(f"<Reading data> finish reading data from '{filepath}'.")
    return data



def save_result_to_json(file_path, data):
    '''
    save directory data as json
    '''
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)



def random_folat(min_val=0.3,max_val=1.3):
    return min_val + (max_val - min_val) * random.random()



def random_lag(lag_min=1.3, lag_max=2.3):
    # Generate a random delay between 1 and 11 seconds
    if lag_max < 4:
        sleep(random_folat(min_val=lag_min, max_val=lag_max))
    else:
        sleep(random_folat(min_val=lag_max/2, max_val=lag_max))



def Notifying():
    winsound.PlaySound('Madobe2015Winter_13.wav', winsound.SND_FILENAME)
    winsound.PlaySound('Madobe2015Winter_13.wav', winsound.SND_FILENAME)
    winsound.PlaySound('Madobe2015Winter_13.wav', winsound.SND_FILENAME)


def extract_content(text, tag):
    """Extracts content between specified XML-like tags."""
    pattern = fr"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None



'''<Evaluator>'''
def evaluate_indicator(indicator, interpretation, scoring_framework):
    assistant_id = "" # default using GPT 4o mini

    '''<read data>'''
    indicator_county_data = read_data(indicator_county_path)
    vector_store_data = read_data(vector_store_data_path)  # 读取 County-Vector_Store_id 的信息
    '''</read data>'''

    '''<output info>'''
    # 创建结果存储的基本信息
    result_file_path, timestamp_evaluation = create_Result_json_file(retult_directory_path=optimization_result_path)
    result_data = {}
    '''</output info>'''

    for county_item in indicator_county_data[indicator]:
        county_name = county_item['County_name']
        value = county_item['Value']
        vector_store_id = get_vector_store_id(vector_store_data, county_name)

        prompt = f"indicator: '{indicator}'. \n\nHere is the interpretation of the indicator: \n{interpretation}\n\n{scoring_framework}\n\nEvaluate the provided 'The {county_name} County Comprehensive Development Plan' against the given indicator. {structural_response_instruction}"  # accuracy: 56

        CALL.updating_assistant_vector_store(assistant_id=assistant_id, vector_store_id=vector_store_id)
        '''<Creating new thread for single County Plan Evaluation>'''
        while True:
            try:
                thread = CALL.create_thread(vector_store_id=vs_id, target=f"")
                __thread_evaluating_id__ = thread.id
                run = CALL.run_assistant(thread_id=__thread_evaluating_id__, assistant_id=assistant_id)
                i_create_thread = 0
                '''<run>'''
                while True:
                    run = CALL.retrieve_run(thread_id=__thread_evaluating_id__, run_id=run.id)
                    if run.status == "completed":
                        break
                    random_lag(1.3, i_create_thread)
                    print(f"<Create thread> Creating...")

                    if i_create_thread % 10 == 0 and i_create_thread != 0:
                        print(f"<Run> Retrying create_thread and Run_assistant...")
                        thread = CALL.create_thread(vector_store_id=vs_id)
                        __thread_evaluating_id__ = thread.id
                        run = CALL.run_assistant(thread_id=__thread_evaluating_id__, assistant_id=assistant_id)
                        print(f"<Run> Wait for completion of the run. The {i_create_thread} times trying...")
                    elif i_create_thread % 5 == 0 and i_create_thread != 0:
                        print(f"<Create thread> Fail [Fail]")
                        print(f"<Create thread> Retrying create thread...")
                        run_ = CALL.run_assistant(thread_id=__thread_evaluating_id__, assistant_id=assistant_id)
                        if run_ == None:
                            pass
                        else:
                            run = run_
                    if i_create_thread >= 25:
                        print(f"<Create thread> Fail to get response.")
                        break
                    i_create_thread += 1
                    print(f"<Create thread> Wait for completion of the thread creation. The {i_create_thread} times trying...")
                    '''</Run>'''
                print(f"<create_thread> Compleat. Thread_id:'{__thread_evaluating_id__}'")
                break
            except Exception as e:
                print(e)
                continue
        '''</Creating new thread for single County Plan Evaluation>'''

        '''<call assistant>'''
        miss = False

        while True:
            try:
                CALL.using_thread(prompt, __thread_evaluating_id__)
                run = CALL.run_assistant(__thread_evaluating_id__, assistant_id)

                i_run = 0
                # Wait for completion of the run
                print(f"<Run> begin to Run...")
                while True:
                    i_run += 1
                    run = CALL.retrieve_run(thread_id=__thread_evaluating_id__, run_id=run.id)
                    if run.status == "completed":
                        print(f"<Run> Run completed [Complete]")
                        break

                    random_lag(lag_min=1, lag_max=i_run)
                    if i_run % 11 == 0 and i_run != 0:
                        print(f"<Run> Retrying create_thread and Run_assistant...")
                        thread = CALL.create_thread(vector_store_id=vs_id)
                        __thread_evaluating_id__ = thread.id
                        CALL.using_thread(prompt, __thread_evaluating_id__)
                        run = CALL.run_assistant(__thread_evaluating_id__, assistant_id)
                        print(f"<Run> Wait for completion of the run. The {i_run} times trying...")
                    elif i_run % 7 == 0 and i_run != 0:
                        print(f"<Run> Retrying Run_assistant...")
                        run_ = CALL.run_assistant(__thread_evaluating_id__, assistant_id)
                        if run_ == None:
                            pass
                        else:
                            run = run_
                        print(f"<Run> Wait for completion of the run. The {i_run} times trying...")
                    else:
                        print(f"<Run> Wait for completion of the run. The {i_run} times trying...")
                    if i_run >= 31:
                        print(f"<Run> Fail to get response.")
                        miss = True
                        break
                break
            except Exception as e:
                print(f"Error, at indicator: '{indicator}', \nError content: '{e}'")
                continue
        while True:
            try:
                if miss:
                    messages_temp = CALL.list_messages(__thread_evaluating_id__)
                    run_steps_temp = CALL.list_run_steps_result(thread_id=__thread_evaluating_id__, run_id=run.id)
                    references_temp, factual_basis_temp = CALL.get_file_search(run_steps=run_steps_temp)
                    result_data = CALL.add_data(data=result_data, county_name=county_name, indicator=indicator,
                                           input_text="Get no response", value=value, score='None',
                                           messages=str(messages_temp), run_steps=run_steps_temp,
                                           references=references_temp, factual_basis=factual_basis_temp)
                    print(f" <Result> save the fail_record to data successfully")
                    break
                print(f" <Processing> Processing response data...")
                messages = CALL.list_messages(__thread_evaluating_id__)
                run_steps = CALL.list_run_steps_result(__thread_evaluating_id__, run.id)
                input_text, score = CALL.get_indicator_and_score(messages)
                CALL.print_result_for_each_indicator(input_text, score, indicator)
                references, factual_basis = CALL.get_file_search(run_steps=run_steps)
                result_data = CALL.add_data(data=result_data, county_name=county_name, indicator=indicator,
                                       input_text=input_text, value=value, score=score, messages=str(messages),
                                       run_steps=run_steps, references=references, factual_basis=factual_basis)
                print(f" <Result> save the result to data successfully")
                break
            except Exception as e:
                print(f"Error processing indicator {indicator} for county {county_name}: {e}")
                continue
        # Saving the result to json file.
        try:
            save_result_to_json(result_file_path, result_data)
            print(f" <Result> Results is saved successfully.")
        except Exception as e:
            print(f" <Result> Error saving result data: {e}")
        '''</call assistant>'''



    return result_file_path, timestamp_evaluation
'''</Evaluator>'''



'''<Optimizer>'''
def optimize_scoring_framework(indicator_OPRO):
    '''优化某一个indicator'''
    improving_assistant_id = ""

    '''<read data>'''
    scoring_framework_data = read_data(Scoring_Framework_path)
    '''</read data>'''

    '''<Processing>'''
    if indicator_OPRO not in scoring_framework_data:
        print(f" <Indicator> indicator: '{indicator_OPRO}' is not in the data.")
        return
    best_accuracy = scoring_framework_data[indicator_OPRO]['Best_accuracy']
    best_scoring_framework = scoring_framework_data[indicator_OPRO]['Best_Scoring_Framework']
    total_evaluations = scoring_framework_data[indicator_OPRO]['Scoring_Frameworks'][best_scoring_framework]['total_evaluations']
    error_evaluations = scoring_framework_data[indicator_OPRO]['Scoring_Frameworks'][best_scoring_framework]['error_evaluations']
    higher_error = scoring_framework_data[indicator_OPRO]['Scoring_Frameworks'][best_scoring_framework]['higher_error']
    lower_error = scoring_framework_data[indicator_OPRO]['Scoring_Frameworks'][best_scoring_framework]['lower_error']
    interpretation_LLM = scoring_framework_data[indicator_OPRO]['Scoring_Frameworks'][best_scoring_framework]['Interpretation_LLM']

    tendency = f"In evaluating {total_evaluations} assessment objects, {error_evaluations} did not align with the correct score. Of these, {higher_error} object was scored higher than appropriate, and {lower_error} objects were scored lower than the correct score."

    '''<Case by case>'''
    if higher_error > lower_error:
        tendency += f" Overall, the scores tend to be higher than they should be."
    elif higher_error < lower_error:
        tendency += f" Overall, the scores tend to be lower than they should be."


    """
    if higher_error > lower_error:
        tendency += f" Overall, the scores tend to be higher than they should be, indicating a tendency toward score inflation.  To address this, adjust the Scoring Framework by making the criteria stricter, enhancing the distinctiveness of the criteria, or removing content that is unrelated or of low relevance to the indicators.  This will ensure the scores better reflect the content being assessed, particularly for indicator '{indicator_OPRO}'."
    elif higher_error < lower_error:
        tendency += f" Overall, the scores tend to be lower than they should be, indicating a tendency toward score deflation. To address this, adjust the Scoring Framework by making the criteria more lenient or by improving the distinctiveness of the criteria. This will ensure the scores better reflect the content being assessed, particularly for indicator '{indicator_OPRO}'."
    
    if indicator_OPRO == 'Environmental regulations for natural system protection':
        tendency += " Clarifying the difference between 2 points and 1 point will be the focus of your generation this time."

    if indicator_OPRO == 'Stormwater management':
        tendency += " More than half of the errors scored 1 point to plans that should have received 0 points, and some even gave 2 points. The Scoring Framework should be stricter and should correctly assess the differences between 0 points, 1 point, and 2 points."

    if indicator_OPRO == 'Water related BMPs':
        tendency += " To make the Scoring Framework focus on the 'Best Management Practices (BMPs)' but not the 'Water'. Clarify the distinctions between 0 points and 1 point in the scoring framework."

    if indicator_OPRO == 'Local tax incentives to support conservation':
        tendency += " When evaluating plans using the current metric explanations and scoring framework, more than half of the evaluations scored the plans 1 point higher than the correct score. This indicates that the scoring criteria should be made stricter, making it more difficult to achieve higher scores."
    """
    '''</Case by case>'''

    prompt_for_improving = f"**Task:**\nAs a distinguished expert in plan evaluation, your objective is to generate a better interpretation and a better Scoring framework against the existing interpretation and Scoring Framework based on their actual performance, and scoring tendencies during plan evaluations. The new interpretation and scoring framework should considering the knowledge of Plan evaluation (the provide knowledge base).\n\n**Context:**\n{context}\n\n**Indicator:**\n{indicator_OPRO}\n\n**Current Interpretation:**\n{interpretation_LLM}\n\n**Current Scoring Framework:**\n{best_scoring_framework}\n\n**Performance Evaluation:**\n- Accuracy: {best_accuracy}%\n- Scoring Tendency:\n{tendency}\n\nEnsure that your response is clear, informative, and tailored to help the reader fully understand the indicator and its relevance. Your response only contain the scoring framework, do not provide any other word or text.\n\n# Output Format\n<interpretation> put the interpretation here </interpretation>\n\n<scoring framework>\n2 Points - sub-title...\n1 Point - sub-title...\n0 Points - sub-title...\n</scoring framework>"

    '''<generate scoring framework>'''
    '''<call assistant>'''
    '''<Creating new thread for single County Plan Evaluation>'''
    while True:
        try:
            thread = CALL.create_thread(vector_store_id=vs_id, target=f"")
            __thread_improving_id__ = thread.id
            run = CALL.run_assistant(thread_id=__thread_improving_id__, assistant_id=improving_assistant_id)
            i_create_thread = 0
            '''<run>'''
            while True:
                run = CALL.retrieve_run(thread_id=__thread_improving_id__, run_id=run.id)
                if run.status == "completed":
                    break
                random_lag(1.3, i_create_thread)
                print(f" <Create thread> Creating...")

                if i_create_thread % 10 == 0 and i_create_thread != 0:
                    print(f" <Run> Retrying create_thread and Run_assistant...")
                    thread = CALL.create_thread(vector_store_id=vs_id)
                    __thread_improving_id__ = thread.id
                    run = CALL.run_assistant(thread_id=__thread_improving_id__, assistant_id=improving_assistant_id)
                    print(f" <Run> Wait for completion of the run. The {i_create_thread} times trying...")
                elif i_create_thread % 5 == 0 and i_create_thread != 0:
                    print(f" <Create thread> Fail [Fail]")
                    print(f" <Create thread> Retrying create thread...")
                    run_ = CALL.run_assistant(thread_id=__thread_improving_id__, assistant_id=improving_assistant_id)
                    if run_ == None:
                        pass
                    else:
                        run = run_
                if i_create_thread >= 25:
                    print(f"<Create thread> Fail to get response.")
                    break
                i_create_thread += 1
                print(f" <Create thread> Wait for completion of the thread creation. The {i_create_thread} times trying...")
                '''</Run>'''
            print(f" <create_thread> Compleat. Thread_id:'{__thread_improving_id__}'")
            break
        except Exception as e:
            print(e)
            continue
    '''</Creating new thread for single County Plan Evaluation>'''

    miss = False

    while True:
        try:
            CALL.using_thread(prompt_for_improving, __thread_improving_id__)
            run = CALL.run_assistant(__thread_improving_id__, improving_assistant_id)

            i_run = 0
            # Wait for completion of the run
            print(f" <Run> begin to Run...")
            while True:
                i_run += 1
                run = CALL.retrieve_run(thread_id=__thread_improving_id__, run_id=run.id)
                if run.status == "completed":
                    print(f" <Run> Run completed [Complete]")
                    break

                random_lag(lag_min=1, lag_max=i_run)
                if i_run % 11 == 0 and i_run != 0:
                    print(f" <Run> Retrying create_thread and Run_assistant...")
                    thread = CALL.create_thread(vector_store_id=vs_id)
                    __thread_improving_id__ = thread.id
                    CALL.using_thread(prompt_for_improving, __thread_improving_id__)
                    run = CALL.run_assistant(__thread_improving_id__, improving_assistant_id)
                    print(f" <Run> Wait for completion of the run. The {i_run} times trying...")
                elif i_run % 7 == 0 and i_run != 0:
                    print(f" <Run> Retrying Run_assistant...")
                    run_ = CALL.run_assistant(__thread_improving_id__, improving_assistant_id)
                    if run_ == None:
                        pass
                    else:
                        run = run_
                    print(f" <Run> Wait for completion of the run. The {i_run} times trying...")
                else:
                    print(f" <Run> Wait for completion of the run. The {i_run} times trying...")
                if i_run >= 31:
                    print(f" <Run> Fail to get response.")
                    miss = True
                    break
            break
        except Exception as e:
            print(f" <Run> Error, at indicator: '{indicator_OPRO}', \nError content: '{e}'")
            continue

    '''</call assistant>'''
    '''<resolve scoring framework>'''
    messages = CALL.list_messages(__thread_improving_id__)
    text = CALL.get_message(messages)
    scoring_framework_New = extract_content(text, "scoring framework")
    interpretation_New = extract_content(text, "interpretation")
    '''</resolve scoring framework>'''
    '''</generate scoring framework>'''
    return interpretation_New, scoring_framework_New
'''</Optimizer>'''


def optimization(best_accuracy_limit=40):
    '''
    1. read data
    
    2. result data info
    
    3. process
    '''

    indicator_list = ['Conservation projects/programs',
                      'Local tax incentives to support conservation',
                      'Financial/economic incentive for conservation',
                      'Link local approvals with 404 permit and/or 401 certifications/swampbuster/title 117',
                      'Implementation timelines/trend']
    special = 'Implementation timelines/trend'

    '''<read data>'''
    scoring_framework_data = read_data(Scoring_Framework_path)
    new_scoring_framework_data = read_data(new_scoring_framework_path)
    '''</read data>'''

    '''<Result info>'''
    optimization_timestamp = datetime.now().strftime("%y-%m-%d %H-%M-%S")
    output_path = Scoring_Framework_path.replace('.json', f'_optimizing_{optimization_timestamp}.json')
    '''</Result info>'''




    for indicator_OPRO in scoring_framework_data:

        count_loop_number = 0
        simular_count = 0
        previous_accuracy = None
        previous_MSE = None
        while True:
            if count_loop_number >= 1:
                print(f"{line}\n <FAIL> Optimize this output for exhaustion...")
                break

            if simular_count >= 2:
                print(f" <WRONG> Keep getting the same evaluation result...")
                print(f"{line}\n <FAIL> Optimize this output for exhaustion...")
                break
            count_loop_number += 1
            best_accuracy = scoring_framework_data[indicator_OPRO]['Best_accuracy']
            best_MSE = scoring_framework_data[indicator_OPRO]['Best_mean_squared_error']
            best_scoring_framework = scoring_framework_data[indicator_OPRO]['Best_Scoring_Framework']
            best_interpretation = scoring_framework_data[indicator_OPRO]['Scoring_Frameworks'][best_scoring_framework]['Interpretation_LLM']

            higher_error = scoring_framework_data[indicator_OPRO]['Scoring_Frameworks'][best_scoring_framework]['higher_error']
            lower_error = scoring_framework_data[indicator_OPRO]['Scoring_Frameworks'][best_scoring_framework]['lower_error']

            if indicator_OPRO in indicator_list:
            #if best_accuracy <= best_accuracy_limit:
                if indicator_OPRO in indicator_list:
                #if higher_error != lower_error:
                    print(f"{line}\n <OPTIMIZE> Optimizing Scoring Framework for indicator: '{indicator_OPRO}'")
                    if indicator_OPRO in indicator_list:
                        if count_loop_number == 1:
                            if indicator_OPRO == special:
                                new_interpretation = ''
                            else:
                                new_interpretation = best_interpretation
                            new_scoring_framework = default_scoring_framework

                        else:
                            # generate interpretation and scoring framework base on the best one
                            new_interpretation, new_scoring_framework = optimize_scoring_framework(indicator_OPRO)
                    else:
                        # generate interpretation and scoring framework base on the best one
                        new_interpretation, new_scoring_framework = optimize_scoring_framework(indicator_OPRO)
                    # initializing basic info for saving new scoring framework
                    scoring_framework_data[indicator_OPRO]['Scoring_Frameworks'][new_scoring_framework] = {"Interpretation_LLM": new_interpretation,
                                                                                                           "total_evaluations": None,
                                                                                                           "error_evaluations": None,
                                                                                                           "higher_error": None,
                                                                                                           "lower_error": None,
                                                                                                           "excessive_error": None,
                                                                                                           "accuracy": None,
                                                                                                           "mean_squared_error": None,
                                                                                                           "Detail": {},
                                                                                                           "Evaluate_status": False,
                                                                                                           "Evaluation_result_timestamp": None,
                                                                                                           "Father_Scoring_Framework": best_scoring_framework}
                    # save the result
                    save_result_to_json(output_path, scoring_framework_data)
                    # evaluate
                    result_file_path, timestamp_evaluation = evaluate_indicator(indicator_OPRO, new_interpretation, new_scoring_framework)
                    # resolve evaluation result
                    Change_Plan_Evaluation_from_json_to_xlsx(result_file_path, timestamp_evaluation,result_director_path=optimization_result_path)

                    Notifying()


                    # read data
                    bias_data = read_data(optimization_result_path+"result_start_at_"+timestamp_evaluation+"_bias_info.json")
                    resolved_result_data = read_data(optimization_result_path+"result_start_at_"+timestamp_evaluation+"_resolved.json")

                    accuracy = bias_data['Accuracy']
                    MSE = bias_data['Mean Squared Error (MSE)']

                    scoring_framework_data[indicator_OPRO]['Scoring_Frameworks'][new_scoring_framework]['accuracy'] = accuracy
                    scoring_framework_data[indicator_OPRO]['Scoring_Frameworks'][new_scoring_framework]['mean_squared_error'] = MSE
                    scoring_framework_data[indicator_OPRO]['Scoring_Frameworks'][new_scoring_framework]['excessive_error'] = bias_data['Excessive_difference']
                    scoring_framework_data[indicator_OPRO]['Scoring_Frameworks'][new_scoring_framework]['lower_error'] = bias_data['Lower_error']
                    scoring_framework_data[indicator_OPRO]['Scoring_Frameworks'][new_scoring_framework]['higher_error'] = bias_data['Higher_error']
                    scoring_framework_data[indicator_OPRO]['Scoring_Frameworks'][new_scoring_framework]['error_evaluations'] = bias_data['Higher_error'] + bias_data['Lower_error']

                    detail = {}
                    total_evaluations = 0
                    for county, info in resolved_result_data.items():
                        for indicator_item in info:
                            if indicator_item['Indicator'] == indicator_OPRO:
                                total_evaluations += 1
                                detail[county] = {"Value": indicator_item['value'],
                                                  "Score": indicator_item['Score']}

                    scoring_framework_data[indicator_OPRO]['Scoring_Frameworks'][new_scoring_framework]['total_evaluations'] = total_evaluations
                    scoring_framework_data[indicator_OPRO]['Scoring_Frameworks'][new_scoring_framework]['Detail'] = detail
                    scoring_framework_data[indicator_OPRO]['Scoring_Frameworks'][new_scoring_framework]['Evaluate_status'] = True
                    scoring_framework_data[indicator_OPRO]['Scoring_Frameworks'][new_scoring_framework]['Evaluation_result_timestamp'] = timestamp_evaluation

                    save_result_to_json(output_path, scoring_framework_data)
                    if previous_accuracy == accuracy:
                        if previous_MSE == MSE:
                            simular_count += 1
                        else:
                            simular_count = 0
                    previous_accuracy = accuracy
                    previous_MSE = MSE
                    scoring_framework_data[indicator_OPRO]['Best_accuracy'] = accuracy
                    scoring_framework_data[indicator_OPRO]['Best_mean_squared_error'] = MSE
                    scoring_framework_data[indicator_OPRO]['Best_Scoring_Framework'] = new_scoring_framework
                    save_result_to_json(output_path, scoring_framework_data)
                else:
                    print(f"{line}\n <SKIP> Skip the indicator: '{indicator_OPRO}' for higher error number equal to lower.")
                    break
            else:
                print(f"{line}\n <FINISH> Finishing optimization for indicator: '{indicator_OPRO}'")
                break




optimization()