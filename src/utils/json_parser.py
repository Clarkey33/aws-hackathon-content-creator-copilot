import json

def robust_json_parser(json_string: str) -> dict:
   
    try:
        start_index = json_string.find('{')
        end_index = json_string.rfind('}')
        
        if start_index != -1 and end_index != -1:
            json_part = json_string[start_index : end_index + 1]
            return json.loads(json_part)
        else:
            raise ValueError("Could not find a valid JSON object in the string.")
    except Exception as e:
        print(f"ERROR: Robust JSON parsing failed. Reason: {e}")
        print(f"Original string: {json_string}")
        return {"error": "Failed to parse JSON response from model."}
    



