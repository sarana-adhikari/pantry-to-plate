import json
import urllib.request
import urllib.error
import os

def lambda_handler(event, context):
    # 1. Parse the incoming ingredients
    try:
        body = json.loads(event.get("body", "{}"))
        ingredients = body.get("ingredients", ["water", "salt"])
    except Exception:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid input format."})}

    # 2. Set up the context window
    system_instruction = """
    You are a professional chef. 
    Create a cohesive, delicious recipe using ONLY the ingredients provided by the user. Format the response with a catchy title, estimated prep time, ingredient measurements, 
    and numbered steps.
    """
    user_prompt = f"Here are my ingredients: {', '.join(ingredients)}"

    api_key = os.environ.get("GEMINI_API_KEY") 
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    
    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [{
            "parts": [{"text": user_prompt}]
        }]
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

    # 3. Execute request with upgraded error handling
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            recipe_text = result['candidates'][0]['content']['parts'][0]['text']
            
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"recipe": recipe_text})
            }
    except urllib.error.HTTPError as e:
        # NEW: This intercepts the 400 error and reads Google's exact error message!
        error_details = e.read().decode('utf-8')
        return {
            "statusCode": e.code,
            "body": json.dumps({
                "error": "Gemini API rejected the request.", 
                "google_details": error_details
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }