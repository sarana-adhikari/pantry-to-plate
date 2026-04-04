import json
import urllib.request
import urllib.error
import os
import logging

# 1. Initialize the professional logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("========== NEW INVOCATION ==========")
    
    # 2. Parse and Log the incoming ingredients
    try:
        body = json.loads(event.get("body", "{}"))
        ingredients = body.get("ingredients", [])
        
        # Log exactly what the user typed before we do anything else
        logger.info(f"USER INPUT INGREDIENTS: {ingredients}")
        
        if not ingredients:
            logger.warning("User submitted an empty ingredient list.")
            return {"statusCode": 400, "body": json.dumps({"error": "No ingredients provided."})}
            
    except Exception as e:
        logger.error(f"Failed to parse input JSON payload: {str(e)}")
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid input format."})}

    # 3. AI Guardrails (System Instructions)
    system_instruction = """
    You are a professional chef. Create a cohesive, delicious recipe using ONLY the ingredients provided by the user. 
    Format the response with a catchy title, estimated prep time, ingredient measurements, and numbered steps.
    
    CRITICAL GUARDRAIL RULES:
    1. If the user provides items that are not edible food (e.g., inanimate objects, chemicals, nonsense words), politely refuse.
    2. If the user asks a question or makes a statement completely unrelated to cooking, politely refuse.
    3. If you must refuse based on Rules 1 or 2, your ENTIRE response MUST begin with the exact string "CHEF_ERROR:" followed by a brief, polite explanation of why you cannot cook with those inputs.
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

    # 4. Execute request and Log the AI's Output
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            recipe_text = result['candidates'][0]['content']['parts'][0]['text']
            
            # Catch the AI triggering a guardrail
            if recipe_text.startswith("CHEF_ERROR:"):
                clean_error_message = recipe_text.replace("CHEF_ERROR:", "").strip()
                logger.warning(f"AI REJECTED INPUT. Chef Response: {clean_error_message}")
                
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": clean_error_message})
                }
            
            # Log successful recipe generation
            logger.info(f"AI RECIPE GENERATED SUCCESSFULLY:\n{recipe_text}")
            
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"recipe": recipe_text})
            }
            
    except urllib.error.HTTPError as e:
        error_details = e.read().decode('utf-8')
        logger.error(f"GEMINI API HTTP ERROR: {e.code} - {error_details}")
        return {
            "statusCode": e.code,
            "body": json.dumps({
                "error": "The Chef's brain is temporarily offline.", 
                "details": "Check CloudWatch logs for the exact Google API error."
            })
        }
    except Exception as e:
        logger.error(f"UNEXPECTED SYSTEM ERROR: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "An unexpected internal server error occurred."})
        }