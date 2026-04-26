import sys
import os
import json
from unittest.mock import patch

# Point Python to your src/ directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import app

# A dummy context object to satisfy the AWS Lambda requirement
class FakeContext:
    aws_request_id = "test-execution-123"

# The @patch decorator intercepts your helper function
@patch('app.fetch_recipe_from_gemini')
def test_lambda_handler_success(mock_fetch):
    # 1. Arrange: Setup the fake input and forced output
    mock_fetch.return_value = "Here is your fake test recipe."
    
    fake_event = {
        "body": json.dumps({"ingredients": ["chicken", "rice"]})
    }

    # 2. Act: Run your handler
    response = app.lambda_handler(fake_event, FakeContext())
    body = json.loads(response["body"])

    # 3. Assert: Verify the logic worked exactly as expected
    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "application/json"
    assert "recipe" in body
    assert body["recipe"] == "Here is your fake test recipe."
    
    # Verify the handler successfully passed the ingredients to the helper function
    mock_fetch.assert_called_once_with(["chicken", "rice"], "test-execution-123")

@patch('app.fetch_recipe_from_gemini')
def test_lambda_handler_empty_ingredients(mock_fetch):
    # 1. Arrange
    fake_event = {
        "body": json.dumps({"ingredients": []})
    }

    # 2. Act
    response = app.lambda_handler(fake_event, FakeContext())
    body = json.loads(response["body"])

    # 3. Assert
    assert response["statusCode"] == 400
    assert "error" in body
    # Ensure the API was NEVER called since the input was invalid
    mock_fetch.assert_not_called()