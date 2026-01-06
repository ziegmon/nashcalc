import json

def save_to_file(scenario, file_path):
    with open(file_path, 'w') as f:
        json.dump(scenario, f, indent=4)

def load_from_file(file_path):
    with open(file_path, 'r') as f:
        scenario = json.load(f)
    return scenario
