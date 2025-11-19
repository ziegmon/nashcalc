import json

def save_to_file(scenario, file_path):
    try:
        with open(file_path, 'w') as f:
            json.dump(scenario, f, indent=4)
    except Exception as e:
        raise ValueError(f"Error saving file: {str(e)}")

def load_from_file(file_path):
    try:
        with open(file_path, 'r') as f:
            scenario = json.load(f)
        # Validate scenario structure
        required_keys = ["attacker_moves", "defender_moves", "payoffs", "n_attacker", "n_defender"]
        for key in required_keys:
            if key not in scenario:
                raise ValueError(f"Missing required key: {key}")
        if not isinstance(scenario["attacker_moves"], list) or not isinstance(scenario["defender_moves"], list):
            raise ValueError("Moves must be lists")
        if not isinstance(scenario["payoffs"], list):
            raise ValueError("Payoffs must be a list")
        if scenario["n_attacker"] != len(scenario["attacker_moves"]):
            raise ValueError("Attacker move count mismatch")
        if scenario["n_defender"] != len(scenario["defender_moves"]):
            raise ValueError("Defender move count mismatch")
        expected_payoffs = scenario["n_attacker"] * scenario["n_defender"]
        if len(scenario["payoffs"]) != expected_payoffs:
            raise ValueError(f"Payoff count mismatch: expected {expected_payoffs}, got {len(scenario['payoffs'])}")
        return scenario
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format")
    except Exception as e:
        raise ValueError(f"Error loading file: {str(e)}")