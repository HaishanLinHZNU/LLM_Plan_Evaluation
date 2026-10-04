import json

# 从 file_info 读取 County—_name, indicator, value

file_path = './NE_Plans/Plans picked according to completeness (county)/Files_info.json'

# Function to read and process the JSON file
def read_vector_store_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


def get_vector_store_id(data, county_name):
    # Get the Vector_Store_id for the given file name
    vector_store_id = data.get(county_name, {}).get("Vector_Store_id")

    if vector_store_id is not None:
        return vector_store_id
        print("<get_vector_store_id> Success.")
    else:
        print("<get_vector_store_id> County name not found.")
        return None

'''
# Example usage
data = read_vector_store_data(file_path)
file_name = "Saunders"
vector_store_id = get_vector_store_id(data, County_name)
print(f"Vector_Store_id for {file_name}: {vector_store_id}")
'''