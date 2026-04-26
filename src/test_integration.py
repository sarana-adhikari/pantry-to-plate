import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
import json
import os
from app import lambda_handler


class TestIntegration:
    """Integration tests that make real API calls to Gemini."""

    @pytest.mark.skipif(not os.environ.get("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
    def test_real_api_call_success(self):
        """Test a real API call with valid ingredients."""
        event = {"body": json.dumps({"ingredients": ["eggs", "spinach", "feta"]})}
        context = type('Context', (), {'aws_request_id': 'integration_test'})()

        response = lambda_handler(event, context)
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "recipe" in body
        assert isinstance(body["recipe"], str)
        assert len(body["recipe"]) > 0

    @pytest.mark.skipif(not os.environ.get("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
    def test_real_api_call_empty_ingredients(self):
        """Test that empty ingredients are rejected without API call."""
        event = {"body": json.dumps({"ingredients": []})}
        context = type('Context', (), {'aws_request_id': 'integration_test'})()

        response = lambda_handler(event, context)
        assert response["statusCode"] == 400
        assert json.loads(response["body"]) == {"error": "No ingredients provided."}

    @pytest.mark.skipif(not os.environ.get("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
    def test_real_api_call_invalid_input(self):
        """Test invalid JSON input."""
        event = {"body": "not json"}
        context = type('Context', (), {'aws_request_id': 'integration_test'})()

        response = lambda_handler(event, context)
        assert response["statusCode"] == 400
        assert json.loads(response["body"]) == {"error": "Invalid input format."}