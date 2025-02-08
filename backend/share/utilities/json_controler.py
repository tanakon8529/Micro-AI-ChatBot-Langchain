import json

def data_base_model_to_string(data):
    return data.json()

def data_string_or_dict_to_json_dump(data):
    return json.dumps(data)

def data_string_to_json_load(data):
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None
