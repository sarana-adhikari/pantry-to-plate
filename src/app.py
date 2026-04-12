import json
import urllib.request
import urllib.error
import os
import logging
import time
from system_prompt import CHEF_SYSTEM_PROMPT

# Initialize the professional logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def create_api_response(status_code, body_content):
    """Standardizes the return payload for AWS API Gateway."""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body_content)
    }


def fetch_recipe_from_gemini(ingredients, request_id):
    """Handles the external network request, payload construction, and latency tracking."""
    user_prompt = f"Here are my ingredients: {', '.join(ingredients)}"
    api_key = os.environ.get("GEMINI_API_KEY") 
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    
    payload = {
        "system_instruction": {
            "parts": [{"text": CHEF_SYSTEM_PROMPT}]
        },
        "contents": [{
            "parts": [{"text": user_prompt}]
        }]
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

    logger.info(f"[{request_id}] Sending request to Gemini API...")
    start_time = time.time()
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            latency = time.time() - start_time
            logger.info(f"[{request_id}] Gemini API responded in {latency:.2f} seconds.")
            
            return result['candidates'][0]['content']['parts'][0]['text']
            
    except urllib.error.HTTPError as e:
        latency = time.time() - start_time
        error_details = e.read().decode('utf-8')
        logger.error(f"[{request_id}] GEMINI API HTTP ERROR ({latency:.2f}s): {e.code} - {error_details}")
        # Raise a custom exception to be caught by the handler
        raise Exception(f"HTTP_{e.code}")


def lambda_handler(event, context):
    """Main coordinator function."""
    request_id = context.aws_request_id
    logger.info(f"[{request_id}] ========== NEW INVOCATION ==========")
    
    try:
        body = json.loads(event.get("body", "{}"))
        ingredients = body.get("ingredients", [])
        
        logger.info(f"[{request_id}] USER INPUT INGREDIENTS: {ingredients}")
        
        if not ingredients:
            logger.warning(f"[{request_id}] User submitted an empty ingredient list.")
            return create_api_response(400, {"error": "No ingredients provided."})
            
    except Exception as e:
        logger.error(f"[{request_id}] Failed to parse input JSON payload: {str(e)}")
        return create_api_response(400, {"error": "Invalid input format."})

    try:
        recipe_text = fetch_recipe_from_gemini(ingredients, request_id)
        
        # Guardrail check
        if recipe_text.startswith("CHEF_ERROR:"):
            clean_error_message = recipe_text.replace("CHEF_ERROR:", "").strip()
            logger.warning(f"[{request_id}] AI REJECTED INPUT. Chef Response: {clean_error_message}")
            return create_api_response(400, {"error": clean_error_message})
        
        logger.info(f"[{request_id}] AI RECIPE GENERATED SUCCESSFULLY.")
        return create_api_response(200, {"recipe": recipe_text})
        
    except Exception as e:
        error_msg = str(e)
        # Catch our custom HTTP error from the helper function
        if error_msg.startswith("HTTP_"):
            error_code = int(error_msg.split("_")[1])
            return create_api_response(error_code, {"error": "The Chef's brain is temporarily offline."})

        # Catch all for unexpected systemic failures
        logger.error(f"[{request_id}] UNEXPECTED SYSTEM ERROR: {error_msg}")
        return create_api_response(500, {"error": "An unexpected internal server error occurred."})