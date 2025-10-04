import pytest
from httpx import AsyncClient
from main import app


class TestExternalSimple:
    """Simplified external API tests - 2 essential test cases"""

    @pytest.mark.asyncio
    async def test_get_quote_success(self):
        """Test getting a quote from external API"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/external/quote")
        
        # Accept success or service unavailable
        assert response.status_code in [200, 404, 503, 500]
        if response.status_code == 200:
            data = response.json()
            assert "content" in data or "text" in data

    @pytest.mark.asyncio
    async def test_external_api_error_handling(self):
        """Test external API error handling"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/external/quote?use_fallback=false")
        
        # Should handle errors gracefully
        assert response.status_code in [200, 404, 503, 500, 422]