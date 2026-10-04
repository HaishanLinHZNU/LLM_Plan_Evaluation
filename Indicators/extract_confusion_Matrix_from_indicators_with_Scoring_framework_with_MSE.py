import json
import pandas as pd




def open_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        return data



def extract_predictions_total(data):
    """
    Extracts actual and predicted values from the data for confusion matrix calculation.

    Args:
        data (dict): The input data containing counties and their evaluations.

    Returns:
        tuple: Two lists containing actual and predicted values respectively.
    """
    actual = []
    predicted = []
    for indicator, info in data.items():
        best_scoring_framework = info['Best_Scoring_Framework']
        result_detail = info['Scoring_Frameworks'][best_scoring_framework]['Detail']
        for county, detail in result_detail.items():
            actual.append(detail['Value'])
            predicted.append(detail['Score'])
    return actual, predicted



def extract_predictions_single_indicator(data, indicator):
    """
    Extracts actual and predicted values from the data for confusion matrix calculation.

    Args:
        data (dict): The input data containing counties and their evaluations.

    Returns:
        tuple: Two lists containing actual and predicted values respectively.
    """
    actual = []
    predicted = []

    best_scoring_framework = data[indicator]['Best_Scoring_Framework']
    result_detail = data[indicator]['Scoring_Frameworks'][best_scoring_framework]['Detail']
    for county, detail in result_detail.items():
        actual.append(detail['Value'])
        predicted.append(detail['Score'])
    return actual, predicted



def calculate_confusion_matrix(actual, predicted):
    """
    Calculates the confusion matrix comparing actual and predicted values,
    including row and column totals.

    Args:
        data (dict): The input data containing counties and their evaluations.

    Returns:
        dict: The confusion matrix in a GPT-readable dictionary format with totals.
    """
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
        "Predicted \\ Actual": ["Predicted 0", "Predicted 1", "Predicted 2", "Total"],
        "Actual 0": [matrix[0][0], matrix[0][1], matrix[0][2], matrix[0]['Total']],
        "Actual 1": [matrix[1][0], matrix[1][1], matrix[1][2], matrix[1]['Total']],
        "Actual 2": [matrix[2][0], matrix[2][1], matrix[2][2], matrix[2]['Total']],
        "Total": [matrix['Total'][0], matrix['Total'][1], matrix['Total'][2], matrix['Total']['Total']]
    }

    df_confusion_matrix = pd.DataFrame()

    for key, value in confusion_matrix_gpt.items():
        df_confusion_matrix[key] = value

    df_confusion_matrix.set_index('Predicted \\ Actual', inplace=True)

    return df_confusion_matrix




def calculate_confusion_matrix_for_total(file_path):
    data = open_file(file_path=file_path)
    actual, predicted = extract_predictions_total(data)
    df_confusion_matrix = calculate_confusion_matrix(actual, predicted)
    print(f">{'-'*80}<\n{df_confusion_matrix}\n>{'-'*80}<")



def calculate_confusion_matrix_for_single_indicator(data, indicator):
    actual, predicted = extract_predictions_single_indicator(data, indicator)
    df_confusion_matrix = calculate_confusion_matrix(actual, predicted)
    return f">{'-'*80}<\n{df_confusion_matrix}\n>{'-'*80}<"



def display_confusion_matrix_for_each_indicator():
    file_path = r"./Indicators/indicators_with_Scoring_Framework_with_MSE.json"
    data = open_file(file_path)
    for indicator, info in data.items():
        print(f"\n{'='*80}\nIndicator: {indicator}\nAccuracy: {info['Best_accuracy']}")
        confusion_matrix = calculate_confusion_matrix_for_single_indicator(data, indicator)
        print(confusion_matrix)
        input('enter any key to continue')


# indicator = "Natural or environmental resources described (open space, green space, river corridors)"



# display_confusion_matrix_for_each_indicator()



# calculate_confusion_matrix_for_total(file_path)