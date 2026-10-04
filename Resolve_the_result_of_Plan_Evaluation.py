import json
import pandas as pd
import numpy as np
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Alignment # Import Font for styling


# Constants for file naming and paths
result_filename = "result_start_at_"



# Load the JSON data
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


# Function to extract score and reason from each evaluation entry
def extract_score_reason(entry):
    """
    Extracts the score and reason from an evaluation entry.

    Args:
        entry (dict): An evaluation entry containing 'score' and other fields.

    Returns:
        tuple: A tuple containing the extracted score (int) and a list of reason lines.
               Returns (None, None) if extraction fails.
    """
    score_text = entry.get("score", "")

    # Extract the score number between "### Score:" and "### Reason:"
    if "###Score:" in score_text and "###Reason:" in score_text:
        score_text = score_text.replace("###Score:", "### Score:")
        score_text = score_text.replace("###Reason:", "### Reason:")
    if "### Score:" in score_text and "### Reason:" in score_text:
        try:
            score_part = score_text.split("### Score:")[1].split("\n\n### Reason:")[0].strip()
            reason_part = score_text.split("### Reason:")[1].strip()
            score = int(score_part)
            # Split the reason into lines
            reason_lines = [line for line in reason_part.split('\n') if line.strip()]
            return score, reason_lines
        except (IndexError, ValueError):
            return None, None
    return None, None


# Helper function to extract errors
def extract_errors(data):
    """
    Extracts the list of errors (value - score) from the data.

    Args:
        data (dict): The input data containing counties and their evaluations.

    Returns:
        list: A list of error values.
    """
    errors = []
    for county, evaluations in data.items():
        for evaluation in evaluations:
            score, _ = extract_score_reason(evaluation)
            if score is not None:
                try:
                    value = int(evaluation["value"])
                    errors.append(score - value)
                except ValueError:
                    continue  # Skip if value is not an integer
    return errors


# Helper function to extract actual and predicted values for confusion matrix
def extract_predictions(data):
    """
    Extracts actual and predicted values from the data for confusion matrix calculation.

    Args:
        data (dict): The input data containing counties and their evaluations.

    Returns:
        tuple: Two lists containing actual and predicted values respectively.
    """
    actual = []
    predicted = []
    for county, evaluations in data.items():
        for evaluation in evaluations:
            score, _ = extract_score_reason(evaluation)
            if score is not None:
                try:
                    value = int(evaluation["value"])
                    actual.append(value)
                    predicted.append(score)
                except ValueError:
                    continue  # Skip if value is not an integer
    return actual, predicted


# Function to calculate accuracy
def calculate_accuracy_in_total(data):
    """
    Calculates the accuracy of predictions.

    Args:
        data (dict): The input data containing counties and their evaluations.

    Returns:
        float: The accuracy percentage.
    """
    total_evaluations = 0
    correct_evaluations = 0

    for county, evaluations in data.items():
        for evaluation in evaluations:
            score, _ = extract_score_reason(evaluation)
            if score is not None:
                try:
                    value = int(evaluation["value"])
                except ValueError:
                    continue  # Skip if value is not an integer
                total_evaluations += 1
                if value == score:
                    correct_evaluations += 1

    accuracy = (correct_evaluations / total_evaluations) * 100 if total_evaluations > 0 else 0
    return accuracy


def resolving_result_for_indicators(data):
    """
    Calculates the accuracy of predictions.

    Args:
        data (dict): The input data containing counties and their evaluations.

    Returns:
        float: The accuracy percentage.
    """
    indicators = {}
    for county, evaluations in data.items():
        for evaluation in evaluations:
            # 1. adding indicator in to indicators dictionary
            indicator = evaluation["indicator"]
            if indicator not in indicators:
                indicators[indicator] = {
                    "total_evaluations": 0,
                    "error_evaluations": 0,
                    "higher_error": 0,
                    "lower_error": 0,
                    "excessive_error": 0,
                    "accuracy": 0,
                    "Detail": {}
                }
            # 2. update
            score, _ = extract_score_reason(evaluation)
            if score is not None:
                try:
                    value = int(evaluation["value"])
                except ValueError:
                    continue  # Skip if value is not an integer
                indicators[indicator]["total_evaluations"] += 1
                if value != score:
                    indicators[indicator]["error_evaluations"] += 1
                    if score - value > 0:
                        indicators[indicator]["higher_error"] += 1
                    else:
                        indicators[indicator]["lower_error"] += 1
                    if (score - value) > 1 or (score - value) < -1:
                        indicators[indicator]["excessive_error"] += 1
                county_detail = {
                    county: {
                        "Value": value,
                        "Score": score
                    }
                }
                indicators[indicator]["Detail"].update(county_detail)
    for indicator in indicators:
        indicators[indicator]["accuracy"] = ((indicators[indicator]["total_evaluations"] - indicators[indicator]["error_evaluations"]) / indicators[indicator]["total_evaluations"]) * 100 if indicators[indicator]["total_evaluations"] > 0 else 0

    return indicators



def resolving_result_for_county(data):
    """
    Calculates the accuracy of predictions.

    Args:
        data (dict): The input data containing counties and their evaluations.

    Returns:
        float: The accuracy percentage.
    """
    counties = {}
    for county_name, evaluations in data.items():
        # 1. adding county in to counties dictionary
        if county_name not in counties:
            counties[county_name] = {
                "total_evaluations": 0,
                "error_evaluations": 0,
                "higher_error": 0,
                "lower_error": 0,
                "excessive_error": 0,
                "accuracy": 0,
                "Detail": {}
            }
        for evaluation in evaluations:
            indicator = evaluation["indicator"]
            # 2. update
            score, _ = extract_score_reason(evaluation)
            if score is not None:
                try:
                    value = int(evaluation["value"])
                except ValueError:
                    continue  # Skip if value is not an integer
                counties[county_name]["total_evaluations"] += 1
                if value != score:
                    counties[county_name]["error_evaluations"] += 1
                    if score - value > 0:
                        counties[county_name]["higher_error"] += 1
                    else:
                        counties[county_name]["lower_error"] += 1
                    if (score - value) > 1 or (score - value) < -1:
                        counties[county_name]["excessive_error"] += 1
                indicator_detail = {
                    indicator: {
                        "Value": value,
                        "Score": score
                    }
                }
                counties[county_name]["Detail"].update(indicator_detail)

    for county_name in counties:
        counties[county_name]["accuracy"] = ((counties[county_name]["total_evaluations"] - counties[county_name][
            "error_evaluations"]) / counties[county_name]["total_evaluations"]) * 100 if counties[county_name][
                                                                                             "total_evaluations"] > 0 else 0

    return counties


# Function to calculate Mean Error (ME)
def calculate_mean_error(data):
    """
    Calculates the Mean Error (ME) of predictions.

    Args:
        data (dict): The input data containing counties and their evaluations.

    Returns:
        float: The mean error.
    """
    errors = extract_errors(data)
    mean_error = np.mean(errors) if errors else 0
    return mean_error


# Function to calculate Mean Squared Error (MSE)
def calculate_mean_squared_error(data):
    """
    Calculates the Mean Squared Error (MSE) of predictions.

    Args:
        data (dict): The input data containing counties and their evaluations.

    Returns:
        float: The mean squared error.
    """
    errors = extract_errors(data)
    squared_errors = [(error ** 2) for error in errors]
    mean_squared_error = np.mean(squared_errors) if squared_errors else 0
    return mean_squared_error


# Function to calculate Standard Deviation of Errors
def calculate_standard_deviation_of_errors(data):
    """
    Calculates the standard deviation of errors.

    Args:
        data (dict): The input data containing counties and their evaluations.

    Returns:
        float: The standard deviation of errors.
    """
    errors = extract_errors(data)
    std_dev_errors = np.std(errors) if errors else 0
    return std_dev_errors


# Function to calculate Confusion Matrix
def calculate_confusion_matrix(data):
    """
    Calculates the confusion matrix comparing actual and predicted values,
    including row and column totals.

    Args:
        data (dict): The input data containing counties and their evaluations.

    Returns:
        dict: The confusion matrix in a GPT-readable dictionary format with totals.
    """
    actual, predicted = extract_predictions(data)
    labels = [0, 1, 2]
    matrix = {actual_label: {pred_label: 0 for pred_label in labels} for actual_label in labels}

    for a, p in zip(actual, predicted):
        if a in labels and p in labels:
            matrix[a][p] += 1

    # Calculate row totals
    for a in labels:
        matrix[a]['Total'] = sum(matrix[a][p] for p in labels)

    # Calculate column totals
    column_totals = {p: 0 for p in labels}
    for a in labels:
        for p in labels:
            column_totals[p] += matrix[a][p]
    overall_total = sum(column_totals[p] for p in labels)
    column_totals['Total'] = overall_total

    # Add the column totals to the matrix under the 'Total' row
    matrix['Total'] = {}
    for p in labels:
        matrix['Total'][p] = column_totals[p]
    matrix['Total']['Total'] = overall_total

    # Convert to a dictionary with headers for GPT readability
    confusion_matrix_gpt = {
        "Predicted \\ Actual": ["Actual 0", "Actual 1", "Actual 2", "Total"],
        "Predicted 0": [matrix[0][0], matrix[1][0], matrix[2][0], matrix['Total'][0]],
        "Predicted 1": [matrix[0][1], matrix[1][1], matrix[2][1], matrix['Total'][1]],
        "Predicted 2": [matrix[0][2], matrix[1][2], matrix[2][2], matrix['Total'][2]],
        "Total": [matrix[0]['Total'], matrix[1]['Total'], matrix[2]['Total'], matrix['Total']['Total']]
    }

    return confusion_matrix_gpt


# Function to save bias information and confusion matrix to JSON
def save_bias_info(timestamp, accuracy, mean_error, mean_squared_error, std_dev_errors, confusion_matrix, indicators, result_director_path):
    """
    Saves the calculated metrics and confusion matrix to a JSON file.

    Args:
        timestamp (str): The timestamp used in the filename.
        accuracy (float): The calculated accuracy.
        mean_error (float): The calculated mean error.
        mean_squared_error (float): The calculated mean squared error.
        std_dev_errors (float): The calculated standard deviation of errors.
        confusion_matrix (dict): The calculated confusion matrix.
    """
    highter = 0
    lower = 0
    excessive = 0
    for indicator in indicators:
        highter += indicators[indicator]["higher_error"]
        lower += indicators[indicator]["lower_error"]
        excessive += indicators[indicator]["excessive_error"]

    path_for_json = result_director_path + result_filename + timestamp + "_resolved.json"
    bias_info = {
        "Result_path": path_for_json,
        "Accuracy": accuracy,
        "Mean Error (ME)": mean_error,
        "Mean Squared Error (MSE)": mean_squared_error,
        "Standard Deviation of Errors": std_dev_errors,
        "Higher_error": highter,
        "Lower_error":lower,
        "Excessive_difference": excessive,
        "Confusion Matrix": confusion_matrix,
        "Indicators": indicators
    }
    bisa_info_path = result_director_path + result_filename + timestamp + "_bias_info.json"

    with open(bisa_info_path, 'w') as outfile:
        json.dump(bias_info, outfile, indent=4)

# Adjust column widths for better readability
def Adjust_column_widths(workbook):
    for column_cells in workbook.columns:
        length = max(len(str(cell.value)) for cell in column_cells)
        column_letter = column_cells[0].column_letter
        workbook.column_dimensions[column_letter].width = length + 2
    return workbook


def styling_Evaluation_sheet(path_for_xlsx, df, false_cells, excessive_difference_cells, negative_difference_cells):
    '''
    Styling Evaluation sheet
    '''
    # Load the workbook to style the sheets
    wb = load_workbook(path_for_xlsx)

    # Style the Evaluation sheet
    ws_Evaluation = wb['Evaluation']

    false_color = "FFCC99"
    excessive_difference_color = "FF9933"

    for row_idx, indicator in enumerate(df['Indicator'], start=2):  # Starting at row 2
        for county in df.columns[1:]:  # Skip the first "Indicator" column
            col_idx = df.columns.get_loc(county) + 1  # Excel column index
            ws_Evaluation.cell(row=row_idx, column=col_idx).alignment = Alignment(horizontal='center')
            if county.endswith('_score') and (indicator, county) in false_cells:
                ws_Evaluation.cell(row=row_idx, column=col_idx).alignment = Alignment(horizontal='right')
                if county.endswith('_score') and (indicator, county) in excessive_difference_cells:
                    ws_Evaluation.cell(row=row_idx, column=col_idx).fill = PatternFill(start_color=excessive_difference_color,
                                                                                 end_color=excessive_difference_color,
                                                                                 fill_type="solid")
                else:
                    ws_Evaluation.cell(row=row_idx, column=col_idx).fill = PatternFill(start_color=false_color,
                                                                                 end_color=false_color,
                                                                                 fill_type="solid")

            if county.endswith('_score') and (indicator, county) in negative_difference_cells:
                ws_Evaluation.cell(row=row_idx, column=col_idx).alignment = Alignment(horizontal='left')

    # Adjust column widths for better readability
    Adjust_column_widths(ws_Evaluation)

    # Save the workbook with all modifications
    wb.save(path_for_xlsx)


def styling_Confusion_Matrix_sheet(path_for_xlsx):
    '''
    Styling Confusion Matrix sheet
    '''
    wb = load_workbook(path_for_xlsx)
    # Style the confusion matrix
    ws_confusion = wb['Confusion Matrix']

    # Set colors for confusion matrix
    header_color = "B7DEE8"
    total_header_color = "92CDDC"
    row_header_color = "FCD5BF"
    total_row_color = "FABF8F"
    diagonal_color = "D8E4BC"
    total_cell_color = "4BACC6"

    # Style the header
    for col in range(2, 5):  # Columns for 0, 1, 2
        cell = ws_confusion.cell(row=1, column=col)
        cell.fill = PatternFill(start_color=header_color, end_color=header_color, fill_type="solid")

    # Style the total header
    ws_confusion.cell(row=1, column=5).fill = PatternFill(start_color=total_header_color, end_color=total_header_color, fill_type="solid")

    # Style the row headers
    for row in range(2, 5):  # Rows for 0, 1, 2, Total
        cell = ws_confusion.cell(row=row, column=1)
        cell.fill = PatternFill(start_color=row_header_color, end_color=row_header_color, fill_type="solid")

    # Style the total row header
    ws_confusion.cell(row=5, column=1).fill = PatternFill(start_color=total_row_color, end_color=total_row_color, fill_type="solid")

    # Style the diagonal and total cells
    for i in range(3):
        ws_confusion.cell(row=i + 2, column=i + 2).fill = PatternFill(start_color=diagonal_color, end_color=diagonal_color, fill_type="solid")
    ws_confusion.cell(row=5, column=5).fill = PatternFill(start_color=total_cell_color, end_color=total_cell_color, fill_type="solid")

    # Adjust column widths for better readability
    Adjust_column_widths(ws_confusion)

    # Save the workbook with all modifications
    wb.save(path_for_xlsx)


def styling_Indicators_and_Counties_sheet(path_for_xlsx, df, sheet_name):
    '''
    Styling Indicators sheet
    '''
    # Load the workbook to style the sheets
    wb = load_workbook(path_for_xlsx)

    # Style the Evaluation sheet
    ws = wb[sheet_name]

    green = "CCFF99"
    blue = "FFFF99"
    pink = "FF9999"
    red = "FF6600"
    yellow = "FFC000"
    higher = "FF6699"
    lower = "9999FF"
    half = "C5D9F1"

    # 删除作为序号的第一列
    ws.delete_cols(1)

    for row_idx, indicator in enumerate(df[sheet_name], start=2):  # Starting at row 2
        '''读取变量'''
        accuracy = df.at[row_idx-2,'accuracy']
        excessive_error = df.at[row_idx-2,'excessive_error']
        error_evaluations = df.at[row_idx-2,'error_evaluations']
        higher_error = df.at[row_idx-2,'higher_error']

        '''设置格式'''
        # 对 indicator 列设置左对齐
        ws.cell(row=row_idx, column=1).alignment = Alignment(horizontal='left')

        # 对过大的误差一列染色
        if df.at[row_idx-2,'excessive_error']:
            ws.cell(row=row_idx, column=6).fill = PatternFill(start_color=yellow, end_color=yellow, fill_type="solid")

        # 对高于正确答案的染色
        if error_evaluations == 0:
            pass
        elif (higher_error/error_evaluations*100)>50:
            ws.cell(row=row_idx, column=1).fill = PatternFill(start_color=higher, end_color=higher, fill_type="solid")
            ws.cell(row=row_idx, column=4).fill = PatternFill(start_color=higher, end_color=higher, fill_type="solid")
        elif (higher_error/error_evaluations*100)==50:
            ws.cell(row=row_idx, column=1).fill = PatternFill(start_color=half, end_color=half, fill_type="solid")
            ws.cell(row=row_idx, column=4).fill = PatternFill(start_color=half, end_color=half, fill_type="solid")
            ws.cell(row=row_idx, column=5).fill = PatternFill(start_color=half, end_color=half, fill_type="solid")
        else:
            ws.cell(row=row_idx, column=1).fill = PatternFill(start_color=lower, end_color=lower, fill_type="solid")
            ws.cell(row=row_idx, column=5).fill = PatternFill(start_color=lower, end_color=lower, fill_type="solid")


        # 对精确度染色
        if accuracy >= 80:
            ws.cell(row=row_idx, column=7).fill = PatternFill(start_color=green, end_color=green, fill_type="solid")
        elif accuracy >= 60:
            ws.cell(row=row_idx, column=7).fill = PatternFill(start_color=blue, end_color=blue, fill_type="solid")
        elif accuracy >= 30:
            ws.cell(row=row_idx, column=7).fill = PatternFill(start_color=pink, end_color=pink, fill_type="solid")
        else:
            ws.cell(row=row_idx, column=7).fill = PatternFill(start_color=red, end_color=red, fill_type="solid")


    # Adjust column widths for better readability
    Adjust_column_widths(ws)

    # Save the workbook with all modifications
    wb.save(path_for_xlsx)



# Function to resolve and save JSON data
def resolve_and_save_json(data, timestamp, result_director_path):
    """
    Processes the input data and saves a resolved JSON file with detailed evaluation information.

    Args:
        data (dict): The input data containing counties and their evaluations.
        timestamp (str): The timestamp used in the filename.
    """
    path_for_json = f"{result_director_path}{result_filename}{timestamp}_resolved.json"

    resolved_data = {}

    # Populate resolved_data with indicators as keys
    for county, evaluations in data.items():
        resolved_data[county] = []
        for evaluation in evaluations:
            score, reason_lines = extract_score_reason(evaluation)
            if score is None:
                continue  # Skip if score extraction failed
            try:
                value = int(evaluation["value"])
            except ValueError:
                continue  # Skip if value is not an integer

            TF = value == score
            HorL = score - value

            updated_evaluation = {
                "Indicator": evaluation.get("indicator", ""),
                "value": value,
                "Score": score,
                "TorF": TF,
                "High_or_low": HorL,
                "Reason": reason_lines,
                "Factual_base": evaluation.get("factual_basis", []),
                "Request": evaluation.get("input", ""),
                "Response": evaluation.get("score", ""),
                "message": evaluation.get("message", ""),
                "Run_steps": evaluation.get("run_steps", "")
            }
            resolved_data[county].append(updated_evaluation)

    # Save the updated data to a new JSON file
    with open(path_for_json, 'w') as outfile:
        json.dump(resolved_data, outfile, indent=4)

def resolve_and_save_xlsx(data, timestamp, indicators, counties, result_director_path):
    path_for_xlsx = result_director_path + result_filename + timestamp + "_resolved.xlsx"

    '''
    read data and change to DataFrame
    '''

    # 存结构化数据 for Evaluation sheet
    structured_data = {}

    # 存错误的格子
    false_cells = []
    # 存差值过大的格子 (差值绝对值为2)
    excessive_difference_cells = []
    # 存比分数低于正确值的格子
    negative_difference_cells = []

    # Populate structured_data with indicators as keys
    for county_name, evaluations in data.items():
        for evaluation in evaluations:
            try:
                indicator = evaluation['indicator']
                score = extract_score_reason(evaluation)[0]
                TF = evaluation["value"] == str(score)
                error = score - eval(evaluation["value"])
                if indicator not in structured_data:
                    structured_data[indicator] = {}

                structured_data[indicator][f'{county_name}_value'] = eval(evaluation["value"])
                structured_data[indicator][f'{county_name}_score'] = score

                if not TF:
                    false_cells.append((indicator, f'{county_name}_score'))
                if error > 1 or error < -1: # error == 2 | -2
                    excessive_difference_cells.append((indicator, f'{county_name}_score'))
                if error < 0: # error == -1 | -2
                    negative_difference_cells.append((indicator, f'{county_name}_score'))
            except Exception as e:
                print(f"<Resolve and save xlsx> error at county: '{county_name}' \nindicator: '{indicator}'\n with {e}")
                continue


    '''
    Processing sheet "Evaluation"
    '''
    # Convert the dictionary to a DataFrame
    df = pd.DataFrame.from_dict(structured_data, orient='index').reset_index()
    df = df.rename(columns={'index': 'Indicator'})

    # Save the Evaluation DataFrame to an Excel file
    df.to_excel(path_for_xlsx, index=False, sheet_name='Evaluation')

    styling_Evaluation_sheet(path_for_xlsx, df, false_cells, excessive_difference_cells, negative_difference_cells)

    '''
    Processing sheet "Confusion Matrix"
    '''
    # Calculate confusion matrix
    confusion_matrix_gpt = calculate_confusion_matrix(data)

    # Create a new DataFrame for confusion matrix
    confusion_df = pd.DataFrame(confusion_matrix_gpt).set_index("Predicted \\ Actual")

    # Save the confusion matrix to the same Excel file
    with pd.ExcelWriter(path_for_xlsx, engine='openpyxl', mode='a') as writer:
        confusion_df.to_excel(writer, sheet_name='Confusion Matrix')

    styling_Confusion_Matrix_sheet(path_for_xlsx)


    '''
    Processing Sheet "Indicators"
    '''
    # delete unnecessary info ("Detail")
    for indicator_element in indicators:
        del indicators[indicator_element]["Detail"]

    # convert the dictionary to Dataframe
    indicators_df = pd.DataFrame.from_dict(indicators, orient='index').reset_index()
    indicators_df = indicators_df.rename(columns={'index': 'Indicators'})


    '''
    Save the indicators info to the same Excel file
    '''
    with pd.ExcelWriter(path_for_xlsx, engine='openpyxl', mode='a') as writer:
        indicators_df.to_excel(writer, sheet_name='Indicators')

    styling_Indicators_and_Counties_sheet(path_for_xlsx, indicators_df, 'Indicators')


    '''
    Processing Sheet "Counties"
    '''
    # delete unnecessary info ("Detail")
    for county_element in counties:
        del counties[county_element]["Detail"]

    # convert the dictionary to Dataframe
    counties_df = pd.DataFrame.from_dict(counties, orient='index').reset_index()
    counties_df = counties_df.rename(columns={'index': 'Counties'})


    '''
    Save the counties info to the same Excel file
    '''
    with pd.ExcelWriter(path_for_xlsx, engine='openpyxl', mode='a') as writer:
        counties_df.to_excel(writer, sheet_name='Counties')

    styling_Indicators_and_Counties_sheet(path_for_xlsx, counties_df , 'Counties')



def printing_bias_info(result_file_path, timestamp):
    data = open_file(result_file_path)

    # Calculate metrics
    accuracy = calculate_accuracy_in_total(data)
    mean_error = calculate_mean_error(data)
    mean_squared_error = calculate_mean_squared_error(data)
    std_dev_errors = calculate_standard_deviation_of_errors(data)
    confusion_matrix = calculate_confusion_matrix(data)
    indicators = resolving_result_for_indicators(data)
    counties = resolving_result_for_county(data)

    # Print the results
    print(f">{'-' * 50}<")
    print(f"Accuracy: {accuracy:.2f}%")
    print(f"Mean Error (ME): {mean_error:.2f}")
    print(f"Mean Squared Error (MSE): {mean_squared_error:.2f}")
    print(f"Standard Deviation of Errors: {std_dev_errors:.2f}")
    print("Confusion Matrix:")
    print(f">{'-' * 50}<")
    for key, value in confusion_matrix.items():
        print(f"{key}: {value}")



# Function to calculate and save all metrics including Confusion Matrix
def Change_Plan_Evaluation_from_json_to_xlsx(result_file_path, timestamp, result_director_path = "./Result_of_Plan_Evaluation/"):
    """
    Orchestrates the entire process of loading data, calculating metrics,
    saving results to JSON and Excel files.

    Args:
        result_file_path (str): The path to the input JSON file.
        timestamp (str): The timestamp used in the filenames.
    """
    data = open_file(result_file_path)

    # Calculate metrics
    accuracy = calculate_accuracy_in_total(data)
    mean_error = calculate_mean_error(data)
    mean_squared_error = calculate_mean_squared_error(data)
    std_dev_errors = calculate_standard_deviation_of_errors(data)
    confusion_matrix = calculate_confusion_matrix(data)
    indicators = resolving_result_for_indicators(data)
    counties = resolving_result_for_county(data)

    # Print the results
    print(f"Accuracy: {accuracy:.2f}%")
    print(f"Mean Error (ME): {mean_error:.2f}")
    print(f"Mean Squared Error (MSE): {mean_squared_error:.2f}")
    print(f"Standard Deviation of Errors: {std_dev_errors:.2f}")
    print("Confusion Matrix:")
    for key, value in confusion_matrix.items():
        print(f"{key}: {value}")

    # Save bias information and confusion matrix to a JSON file
    save_bias_info(timestamp, accuracy, mean_error, mean_squared_error, std_dev_errors, confusion_matrix, indicators, result_director_path)

    # Call the functions to process the data and save the results
    resolve_and_save_json(data, timestamp, result_director_path)
    resolve_and_save_xlsx(data, timestamp, indicators, counties, result_director_path)
    print(f"Data processed and saved to {result_director_path}")




# Example usage:
# Change_Plan_Evaluation_from_json_to_xlsx(result_file_path=f"./Result_of_Plan_Evaluation/result_start_at_25-02-25 20-15-26.json", timestamp="25-02-25 20-15-26")
