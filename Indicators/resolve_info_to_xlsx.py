import json
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Alignment # Import Font for styling



def Adjust_column_widths(workbook):
    for column_cells in workbook.columns:
        length = max(len(str(cell.value)) for cell in column_cells)
        column_letter = column_cells[0].column_letter
        workbook.column_dimensions[column_letter].width = length + 2
    return workbook



def extract_data_from_json(json_file_path, timestamp=''):
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    extracted_data = []

    for indicator, metrics in data.items():
        extracted_data.append({
            'Indicator': indicator,
            f'{timestamp}\nBest_accuracy': metrics['Best_accuracy'],
            'Best_mean_squared_error': metrics['Best_mean_squared_error']
        })

    return extracted_data


def save_to_excel(data, output_file_path, timestamp=''):
    # Create a new workbook and select the active worksheet
    wb = Workbook()
    ws = wb.active

    # Write the headers
    ws.append(['Indicator', f'{timestamp}\nBest_accuracy', f'Best_mean_squared_error'])

    # Define the fill colors
    green = "CCFF99"
    blue = "FFFF99"
    pink = "FF9999"
    red = "FF6600"

    # Iterate over the data and write to the worksheet
    for row_idx, row in enumerate(data):
        ws.append([row['Indicator'], row[f'{timestamp}\nBest_accuracy'], row['Best_mean_squared_error']])

        # Apply styling to the accuracy column
        accuracy = row[f'{timestamp}\nBest_accuracy']

        if accuracy >= 80:
            ws.cell(row=row_idx + 2, column=2).fill = PatternFill(start_color=green, end_color=green, fill_type="solid")
        elif accuracy >= 60:
            ws.cell(row=row_idx + 2, column=2).fill = PatternFill(start_color=blue, end_color=blue, fill_type="solid")
        elif accuracy >= 30:
            ws.cell(row=row_idx + 2, column=2).fill = PatternFill(start_color=pink, end_color=pink, fill_type="solid")
        else:
            ws.cell(row=row_idx + 2, column=2).fill = PatternFill(start_color=red, end_color=red, fill_type="solid")

    # Adjust column widths for better readability
    Adjust_column_widths(ws)

    # Save the workbook
    wb.save(output_file_path)


# # Input and output file paths
# json_file_path = r"./indicators_with_Scoring_Framework_with_MSE_optimizing_24-11-02 18-56-10.json"  # Update this with your JSON file path
# output_file_path = json_file_path.replace('.json', '.xlsx')
#
# # Extract data from JSON and save to Excel
# data = extract_data_from_json(json_file_path, '24-11-02 18-56-10')
# save_to_excel(data, output_file_path, '24-11-02 18-56-10')
