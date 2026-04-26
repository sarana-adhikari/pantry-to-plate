import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
import json
import urllib.request
import urllib.error
from unittest.mock import patch, MagicMock
from app import lambda_handler, fetch_recipe_from_gemini, create_api_response


class TestCreateApiResponse:
    def test_success_response(self):
        response = create_api_response(200, {"recipe": "test"})
        assert response["statusCode"] == 200
        assert response["headers"]["Content-Type"] == "application/json"
        assert json.loads(response["body"]) == {"recipe": "test"}

    def test_error_response(self):
        response = create_api_response(400, {"error": "bad request"})
        assert response["statusCode"] == 400
        assert json.loads(response["body"]) == {"error": "bad request"}


class TestFetchRecipeFromGemini:
    @patch('app.urllib.request.urlopen')
    @patch('app.os.environ.get')
    def test_successful_response(self, mock_env, mock_urlopen):
        mock_env.return_value = "test_key"
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "candidates": [{"content": {"parts": [{"text": "Recipe text"}]}}]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = fetch_recipe_from_gemini(["eggs", "spinach"], "test_id")
        assert result == "Recipe text"

    @patch('app.urllib.request.urlopen')
    @patch('app.os.environ.get')
    def test_http_error_429(self, mock_env, mock_urlopen):
        mock_env.return_value = "test_key"
        mock_error = urllib.error.HTTPError(None, 429, "Too Many Requests", None, None)
        mock_error.read = MagicMock(return_value=b'{"error": "rate limit"}')
        mock_urlopen.side_effect = mock_error

        with pytest.raises(Exception, match="HTTP_429"):
            fetch_recipe_from_gemini(["eggs"], "test_id")

    @patch('app.urllib.request.urlopen')
    @patch('app.os.environ.get')
    def test_malformed_response(self, mock_env, mock_urlopen):
        mock_env.return_value = "test_key"
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"invalid": "response"}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        with pytest.raises(KeyError):
            fetch_recipe_from_gemini(["eggs"], "test_id")

    @patch('app.urllib.request.urlopen')
    @patch('app.os.environ.get')
    def test_guardrail_error(self, mock_env, mock_urlopen):
        mock_env.return_value = "test_key"
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "candidates": [{"content": {"parts": [{"text": "CHEF_ERROR: Bad ingredients"}]}}]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = fetch_recipe_from_gemini(["bad"], "test_id")
        assert result == "CHEF_ERROR: Bad ingredients"


class TestLambdaHandler:
    def test_valid_request(self):
        event = {"body": json.dumps({"ingredients": ["eggs", "spinach"]})}
        context = MagicMock()
        context.aws_request_id = "test_id"

        with patch('app.fetch_recipe_from_gemini', return_value="Recipe text"):
            response = lambda_handler(event, context)
            assert response["statusCode"] == 200
            assert json.loads(response["body"]) == {"recipe": "Recipe text"}

    def test_empty_ingredients(self):
        event = {"body": json.dumps({"ingredients": []})}
        context = MagicMock()
        context.aws_request_id = "test_id"

        response = lambda_handler(event, context)
        assert response["statusCode"] == 400
        assert json.loads(response["body"]) == {"error": "No ingredients provided."}

    def test_invalid_json(self):
        event = {"body": "invalid json"}
        context = MagicMock()
        context.aws_request_id = "test_id"

        response = lambda_handler(event, context)
        assert response["statusCode"] == 400
        assert json.loads(response["body"]) == {"error": "Invalid input format."}

    def test_guardrail_rejection(self):
        event = {"body": json.dumps({"ingredients": ["bad"]})}
        context = MagicMock()
        context.aws_request_id = "test_id"

        with patch('app.fetch_recipe_from_gemini', return_value="CHEF_ERROR: Rejected"):
            response = lambda_handler(event, context)
            assert response["statusCode"] == 400
            assert json.loads(response["body"]) == {"error": "Rejected"}

    def test_http_error_handling(self):
        event = {"body": json.dumps({"ingredients": ["eggs"]})}
        context = MagicMock()
        context.aws_request_id = "test_id"

        with patch('app.fetch_recipe_from_gemini', side_effect=Exception("HTTP_429")):
            response = lambda_handler(event, context)
            assert response["statusCode"] == 429
            assert json.loads(response["body"]) == {"error": "The Chef's brain is temporarily offline."}

    def test_unexpected_error(self):
        event = {"body": json.dumps({"ingredients": ["eggs"]})}
        context = MagicMock()
        context.aws_request_id = "test_id"

        with patch('app.fetch_recipe_from_gemini', side_effect=Exception("Unexpected")):
            response = lambda_handler(event, context)
            assert response["statusCode"] == 500
            assert json.loads(response["body"]) == {"error": "An unexpected internal server error occurred."}