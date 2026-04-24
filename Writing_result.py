import json
import os
from datetime import datetime


def create_Result_json_file(retult_directory_path = "D:/Plans_Evaluation/Result_of_Plan_Evaluation/", part=''):
    # Create a timestamped file name
    timestamp = datetime.now().strftime("%y-%m-%d %H-%M-%S")
    if part == '':
        result_file_path = f'{retult_directory_path}result_start_at_{timestamp}.json'
    else:
        result_file_path = f'{retult_directory_path}{part}_result_start_at_{timestamp}.json'
    return result_file_path, timestamp


# Function to add data to the dictionary
def add_data(data, county_name, indicator,input_text, value, score, messages, run_steps, references, factual_basis):
    '''
    logging parameters info for original data 'result_start_at_{timestamp}.json'

    'result_start_at_{timestamp}.json':
        - Using county_name as main key and indicator as the sub-key for saving all data

    return: a dictionary saving the original data of a loop of plan evaluation
    '''
    if county_name not in data:
        data[county_name] = []
    data[county_name].append({
        "indicator": indicator,
        "input": input_text,
        "value": value,
        "score": score, # basically is text with score and the reason why LLM giving this score
        "message": messages, # original messages list
        "run_steps": str(run_steps),
        "references": str(references),
        "factual_basis": factual_basis
    })
    return data


def save_result_to_json(file_path, data):
    '''
    save directory data as json
    '''
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
    '''
    try:
        # Load existing data if the file exists
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                existing_data = json.load(file)
                # Merge the existing data with new data
                for county, entries in data.items():
                    if county in existing_data:
                        existing_data[county].extend(entries)
                    else:
                        existing_data[county] = entries
        else:
            existing_data = data
    except Exception as e:
        print(f"<Save result to json> error rase when processing data with '{e}'")
    try:
        # Write the updated data back to the file
        with open(file_path, 'w') as file:
            json.dump(existing_data, file, indent=4)

        print(f"Evaluation result saved to \n{file_path}.json")
    except Exception as e:
        print(f"<Save result to json> error rase when writing data to json with '{e}'")
    '''