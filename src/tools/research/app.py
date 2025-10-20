# import json
# import asyncio
# from research_tool import research_logic
# import ast



# def lambda_handler(event, context):
#     print("Raw parameters:", json.dumps(event["parameters"], indent=2))

#     print(f"Received event from Bedrock Agent: {json.dumps(event)}")
    
#     try:
#         params = event.get('parameters', [])
        
#         queries_param = next((p for p in params if p['name'] == 'queries'), None)
        
#         if not queries_param:
#             raise ValueError("Missing required parameter: 'queries'")
            
#         queries_value = queries_param['value']

#         try:
#             queries = json.loads(queries_value)
#         except json.JSONDecodeError:
           
#             queries = ast.literal_eval(queries_value)
#         print("Queries parsed:", queries)

#     except Exception as e:
#         print("ERROR:", str(e))
#         queries = json.loads(queries_value)

#         #print(queries)

#         result = asyncio.run(research_logic(queries=queries))
        
#         response = {
#             'response': {
#                 'actionGroup': event['actionGroup'],
#                 'function': event['function'],
#                 'functionResponse': {
#                     'responseBody': {
#                         'TEXT': {'body': json.dumps(result)}
#                     }
#                 }
#             },
#             'sessionId': event['sessionId'],
#             'sessionAttributes': event.get('sessionAttributes', {})
#         }

#         return response

#     except Exception as e:
#         print(f"ERROR: {e}")


import json
import ast
import asyncio
from research_tool import research_logic  
def lambda_handler(event, context):
    print("Raw parameters:", json.dumps(event.get("parameters", []), indent=2))
    print("Received event from Bedrock Agent:", json.dumps(event))

    try:
        params = event.get('parameters', [])
        queries_param = next((p for p in params if p['name'] == 'queries'), None)

        if not queries_param:
            raise ValueError("Missing required parameter: 'queries'")

        queries_value = queries_param['value']
        queries = None

        # --- Robust parsing section ---
        if isinstance(queries_value, list):
            queries = queries_value

        elif isinstance(queries_value, str):
            queries_value = queries_value.strip()

            try:
                # Try normal JSON parse first
                queries = json.loads(queries_value)
            except json.JSONDecodeError:
                try:
                    # Fallback: handle unquoted comma-separated list
                    cleaned = queries_value.strip("[]")
                    if cleaned:
                        queries = [q.strip().strip('"').strip("'") for q in cleaned.split(",")]
                    else:
                        queries = []
                except Exception as inner_e:
                    print(f"Fallback parsing failed: {inner_e}")
                    raise ValueError("Unable to parse 'queries' as a valid list.")
        else:
            raise ValueError(f"Unexpected type for queries_value: {type(queries_value)}")

        print("Parsed queries:", queries)

       
        result = asyncio.run(research_logic(queries=queries))


        response = {
            'response': {
                'actionGroup': event.get('actionGroup'),
                'function': event.get('function'),
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {'body': json.dumps(result)}
                    }
                }
            },
            'sessionId': event.get('sessionId'),
            'sessionAttributes': event.get('sessionAttributes', {})
        }

        return response

    except Exception as e:
        print(f"ERROR: {e}")
        return {
            'response': {
                'actionGroup': event.get('actionGroup'),
                'function': event.get('function'),
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {'body': f"Error: {str(e)}"}
                    }
                }
            },
            'sessionId': event.get('sessionId'),
            'sessionAttributes': event.get('sessionAttributes', {})
        }
