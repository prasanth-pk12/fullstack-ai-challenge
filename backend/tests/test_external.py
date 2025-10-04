import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, TimeoutException, RequestError, Response
import sys
import os
from typing import Dict, Any

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from main import app
from services.external_service import (
    fetch_random_quote,
    fetch_quote_with_fallback,
    ExternalAPIError,
    convert_external_api_error_to_http_exception
)


class TestExternalService:
    """Test external service functionality with mocked API calls"""
    
    @pytest.mark.asyncio
    async def test_fetch_random_quote_success(self):
        """Test successful quote fetching from external API"""
        mock_response_data = {
            "content": "The only way to do great work is to love what you do.",
            "author": "Steve Jobs",
            "tags": ["motivational", "work"],
            "length": 52
        }
        
        # Mock the httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        with patch('services.external_service.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await fetch_random_quote()
            
            assert result["content"] == mock_response_data["content"]
            assert result["author"] == mock_response_data["author"]
            assert result["tags"] == mock_response_data["tags"]
            assert result["length"] == mock_response_data["length"]
            assert result["source"] == "quotable.io"
    
    @pytest.mark.asyncio
    async def test_fetch_random_quote_missing_required_field(self):
        """Test handling of API response missing required fields"""
        mock_response_data = {
            "content": "Test quote",
            # Missing "author" field
            "tags": ["test"],
            "length": 10
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        with patch('services.external_service.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            with pytest.raises(ExternalAPIError) as exc_info:
                await fetch_random_quote()
            
            # The service catches validation errors and returns a generic message
            assert "Unexpected error occurred while fetching quote" in str(exc_info.value)
            assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_fetch_random_quote_api_error(self):
        """Test handling of API HTTP errors"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        with patch('services.external_service.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            with pytest.raises(ExternalAPIError) as exc_info:
                await fetch_random_quote()
            
            # The service catches API errors and returns a generic message after all retries
            assert "Unexpected error occurred while fetching quote" in str(exc_info.value)
            assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_fetch_random_quote_rate_limit_with_retry(self):
        """Test rate limit handling with retry logic"""
        # First call returns 429 (rate limited), second call succeeds
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "content": "Success after retry",
            "author": "Test Author",
            "tags": ["test"],
            "length": 18
        }
        
        with patch('services.external_service.httpx.AsyncClient') as mock_client:
            # Mock multiple calls - first fails with 429, second succeeds
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=[mock_response_429, mock_response_success]
            )
            
            with patch('services.external_service.asyncio.sleep', new_callable=AsyncMock):
                result = await fetch_random_quote()
                
                assert result["content"] == "Success after retry"
                assert result["author"] == "Test Author"
    
    @pytest.mark.asyncio
    async def test_fetch_random_quote_timeout_error(self):
        """Test handling of timeout errors"""
        with patch('services.external_service.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=TimeoutException("Request timed out")
            )
            
            with patch('services.external_service.asyncio.sleep', new_callable=AsyncMock):
                with pytest.raises(ExternalAPIError) as exc_info:
                    await fetch_random_quote()
                
                assert "timed out" in str(exc_info.value)
                assert exc_info.value.status_code == 504
    
    @pytest.mark.asyncio
    async def test_fetch_random_quote_connection_error(self):
        """Test handling of connection errors"""
        with patch('services.external_service.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=RequestError("Connection failed")
            )
            
            with patch('services.external_service.asyncio.sleep', new_callable=AsyncMock):
                with pytest.raises(ExternalAPIError) as exc_info:
                    await fetch_random_quote()
                
                assert "Failed to connect" in str(exc_info.value)
                assert exc_info.value.status_code == 502
    
    @pytest.mark.asyncio
    async def test_fetch_quote_with_fallback_success(self):
        """Test successful fallback functionality when API works"""
        mock_response_data = {
            "content": "API quote",
            "author": "API Author",
            "tags": ["api"],
            "length": 9
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        with patch('services.external_service.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await fetch_quote_with_fallback()
            
            assert result["content"] == "API quote"
            assert result["source"] == "quotable.io"
            assert "fallback_reason" not in result
    
    @pytest.mark.asyncio
    async def test_fetch_quote_with_fallback_on_error(self):
        """Test fallback functionality when API fails"""
        with patch('services.external_service.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=TimeoutException("API timeout")
            )
            
            with patch('services.external_service.asyncio.sleep', new_callable=AsyncMock):
                result = await fetch_quote_with_fallback()
                
                assert result["source"] == "local_fallback"
                assert "fallback_reason" in result
                assert "content" in result
                assert "author" in result
                assert len(result["content"]) > 0


class TestExternalEndpoints:
    """Test external API endpoints with mocked responses"""
    
    @pytest.mark.asyncio
    async def test_get_random_quote_success(self):
        """Test successful quote endpoint"""
        mock_response_data = {
            "content": "Test quote for endpoint",
            "author": "Test Author",
            "tags": ["test"],
            "length": 23
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        with patch('services.external_service.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/external/quote")
            
            assert response.status_code == 200
            data = response.json()
            assert data["content"] == mock_response_data["content"]
            assert data["author"] == mock_response_data["author"]
            assert data["source"] == "quotable.io"
    
    @pytest.mark.asyncio
    async def test_get_random_quote_with_fallback_disabled(self):
        """Test quote endpoint with fallback disabled and API failure"""
        with patch('services.external_service.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=TimeoutException("API timeout")
            )
            
            with patch('services.external_service.asyncio.sleep', new_callable=AsyncMock):
                async with AsyncClient(app=app, base_url="http://test") as ac:
                    response = await ac.get("/external/quote?use_fallback=false")
                
                assert response.status_code == 504  # Gateway timeout
                data = response.json()
                assert "timed out" in data["detail"]["message"]
    
    @pytest.mark.asyncio
    async def test_get_random_quote_with_fallback_enabled(self):
        """Test quote endpoint with fallback enabled and API failure"""
        with patch('services.external_service.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=TimeoutException("API timeout")
            )
            
            with patch('services.external_service.asyncio.sleep', new_callable=AsyncMock):
                async with AsyncClient(app=app, base_url="http://test") as ac:
                    response = await ac.get("/external/quote?use_fallback=true")
                
                assert response.status_code == 200
                data = response.json()
                assert data["source"] == "local_fallback"
                assert "fallback_reason" in data
    
    @pytest.mark.asyncio
    async def test_get_random_quote_detailed(self):
        """Test detailed quote endpoint with metadata"""
        mock_response_data = {
            "content": "Detailed quote test",
            "author": "Detailed Author",
            "tags": ["detailed"],
            "length": 18
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        with patch('services.external_service.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/external/quote/detailed")
            
            assert response.status_code == 200
            data = response.json()
            assert data["content"] == mock_response_data["content"]
            assert "fetched_at" in data
            assert "request_id" in data
            assert "cache_status" in data
            assert data["cache_status"] == "miss"
    
    @pytest.mark.asyncio
    async def test_check_external_api_health_success(self):
        """Test health check endpoint when API is healthy"""
        mock_response_data = {
            "content": "Health check quote",
            "author": "Health Author",
            "tags": ["health"],
            "length": 18
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        with patch('services.external_service.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/external/quote/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["api_source"] == "quotable.io"
            assert "response_time_ms" in data
            assert "last_check" in data
            assert "check_id" in data
    
    @pytest.mark.asyncio
    async def test_check_external_api_health_failure(self):
        """Test health check endpoint when API is unhealthy"""
        with patch('services.external_service.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=TimeoutException("Health check timeout")
            )
            
            with patch('services.external_service.asyncio.sleep', new_callable=AsyncMock):
                async with AsyncClient(app=app, base_url="http://test") as ac:
                    response = await ac.get("/external/quote/health")
                
                assert response.status_code == 503  # Service unavailable
                data = response.json()
                assert data["detail"]["status"] == "unhealthy"
                # The actual error message is more specific about multiple attempts
                assert "timed out after multiple attempts" in data["detail"]["error_message"]


class TestErrorConversion:
    """Test error conversion utilities"""
    
    def test_convert_external_api_error_to_http_exception(self):
        """Test conversion of ExternalAPIError to HTTPException"""
        # Test 502 Bad Gateway
        error_502 = ExternalAPIError("API returned invalid response", 502, {"error": "invalid"})
        http_exc = convert_external_api_error_to_http_exception(error_502)
        assert http_exc.status_code == 502
        assert http_exc.detail["message"] == "API returned invalid response"
        assert http_exc.detail["error_type"] == "external_api_error"
        
        # Test 503 Service Unavailable
        error_503 = ExternalAPIError("Service temporarily unavailable", 503)
        http_exc = convert_external_api_error_to_http_exception(error_503)
        assert http_exc.status_code == 503
        
        # Test 504 Gateway Timeout
        error_504 = ExternalAPIError("Request timed out", 504)
        http_exc = convert_external_api_error_to_http_exception(error_504)
        assert http_exc.status_code == 504
        
        # Test unknown error code defaults to 500
        error_unknown = ExternalAPIError("Unknown error", 999)
        http_exc = convert_external_api_error_to_http_exception(error_unknown)
        assert http_exc.status_code == 500


class TestAPIIntegration:
    """Integration tests with various scenarios"""
    
    @pytest.mark.asyncio
    async def test_quote_endpoint_parameter_validation(self):
        """Test quote endpoint parameter validation"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Test with valid boolean values
            response = await ac.get("/external/quote?use_fallback=true")
            assert response.status_code in [200, 502, 503, 504]  # Could be any depending on API state
            
            response = await ac.get("/external/quote?use_fallback=false")
            assert response.status_code in [200, 502, 503, 504]  # Could be any depending on API state
    
    @pytest.mark.asyncio
    async def test_all_endpoints_return_valid_json(self):
        """Test that all endpoints return valid JSON responses"""
        endpoints = [
            "/external/quote",
            "/external/quote/detailed",
            "/external/quote/health"
        ]
        
        for endpoint in endpoints:
            with patch('services.external_service.httpx.AsyncClient') as mock_client:
                # Mock a successful response
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "content": "Test quote",
                    "author": "Test Author",
                    "tags": ["test"],
                    "length": 10
                }
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
                
                async with AsyncClient(app=app, base_url="http://test") as ac:
                    response = await ac.get(endpoint)
                
                assert response.status_code == 200
                # Verify response is valid JSON
                data = response.json()
                assert isinstance(data, dict)
                
                # Verify common fields based on endpoint
                if "health" not in endpoint:
                    assert "content" in data
                    assert "author" in data
                else:
                    assert "status" in data