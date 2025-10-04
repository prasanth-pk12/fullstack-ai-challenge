import httpx
import asyncio
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import logging

# Configure logging
logger = logging.getLogger(__name__)

# External API configuration
QUOTE_API_URL = "https://api.quotable.io/random"
REQUEST_TIMEOUT = 10.0  # 10 seconds timeout
MAX_RETRIES = 3


class ExternalAPIError(Exception):
    """Custom exception for external API errors"""
    def __init__(self, message: str, status_code: int = 500, api_response: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.api_response = api_response
        super().__init__(self.message)


async def fetch_random_quote() -> Dict[str, Any]:
    """
    Fetch a random motivational quote from quotable.io API
    
    Returns:
        Dict containing quote data with keys: content, author, tags, length
        
    Raises:
        ExternalAPIError: When API request fails or returns invalid data
    """
    
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        retry_count = 0
        last_exception = None
        
        while retry_count < MAX_RETRIES:
            try:
                logger.info(f"Fetching quote from API (attempt {retry_count + 1}/{MAX_RETRIES})")
                
                response = await client.get(QUOTE_API_URL)
                
                # Check if request was successful
                if response.status_code == 200:
                    data = response.json()
                    
                    # Validate required fields are present
                    required_fields = ["content", "author"]
                    for field in required_fields:
                        if field not in data:
                            raise ExternalAPIError(
                                f"Missing required field '{field}' in API response",
                                status_code=502,
                                api_response=data
                            )
                    
                    logger.info(f"Successfully fetched quote by {data.get('author')}")
                    return {
                        "content": data["content"],
                        "author": data["author"],
                        "tags": data.get("tags", []),
                        "length": data.get("length", len(data["content"])),
                        "source": "quotable.io"
                    }
                
                elif response.status_code == 429:
                    # Rate limit exceeded, wait and retry
                    wait_time = 2 ** retry_count  # Exponential backoff
                    logger.warning(f"Rate limited by API, waiting {wait_time}s before retry")
                    await asyncio.sleep(wait_time)
                    retry_count += 1
                    continue
                
                else:
                    # Other HTTP errors
                    logger.error(f"API returned status {response.status_code}: {response.text}")
                    raise ExternalAPIError(
                        f"External API returned status {response.status_code}",
                        status_code=502,
                        api_response={"status_code": response.status_code, "text": response.text}
                    )
                    
            except httpx.TimeoutException as e:
                last_exception = e
                retry_count += 1
                logger.warning(f"Request timeout (attempt {retry_count}/{MAX_RETRIES})")
                
                if retry_count < MAX_RETRIES:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    await asyncio.sleep(wait_time)
                    continue
                    
            except httpx.RequestError as e:
                last_exception = e
                retry_count += 1
                logger.warning(f"Request error: {str(e)} (attempt {retry_count}/{MAX_RETRIES})")
                
                if retry_count < MAX_RETRIES:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    await asyncio.sleep(wait_time)
                    continue
                    
            except Exception as e:
                # Unexpected errors
                logger.error(f"Unexpected error fetching quote: {str(e)}")
                raise ExternalAPIError(
                    "Unexpected error occurred while fetching quote",
                    status_code=500
                )
        
        # All retries exhausted
        logger.error(f"All {MAX_RETRIES} attempts failed, last error: {str(last_exception)}")
        
        if isinstance(last_exception, httpx.TimeoutException):
            raise ExternalAPIError(
                "External API request timed out after multiple attempts",
                status_code=504
            )
        elif isinstance(last_exception, httpx.RequestError):
            raise ExternalAPIError(
                f"Failed to connect to external API: {str(last_exception)}",
                status_code=502
            )
        else:
            raise ExternalAPIError(
                "External API is currently unavailable",
                status_code=503
            )


async def fetch_quote_with_fallback() -> Dict[str, Any]:
    """
    Fetch a random quote with fallback to local quotes if external API fails
    
    Returns:
        Dict containing quote data
    """
    
    # List of fallback quotes in case external API fails
    fallback_quotes = [
        {
            "content": "The only way to do great work is to love what you do.",
            "author": "Steve Jobs",
            "tags": ["motivational", "work"],
            "length": 52,
            "source": "local_fallback"
        },
        {
            "content": "Innovation distinguishes between a leader and a follower.",
            "author": "Steve Jobs",
            "tags": ["innovation", "leadership"],
            "length": 61,
            "source": "local_fallback"
        },
        {
            "content": "The future belongs to those who believe in the beauty of their dreams.",
            "author": "Eleanor Roosevelt",
            "tags": ["dreams", "future", "motivational"],
            "length": 70,
            "source": "local_fallback"
        },
        {
            "content": "Success is not final, failure is not fatal: it is the courage to continue that counts.",
            "author": "Winston Churchill",
            "tags": ["success", "courage", "perseverance"],
            "length": 85,
            "source": "local_fallback"
        },
        {
            "content": "The only impossible journey is the one you never begin.",
            "author": "Tony Robbins",
            "tags": ["journey", "beginning", "motivation"],
            "length": 56,
            "source": "local_fallback"
        }
    ]
    
    try:
        # Try to fetch from external API first
        return await fetch_random_quote()
        
    except ExternalAPIError as e:
        # Log the error but continue with fallback
        logger.warning(f"External API failed: {e.message}, using fallback quote")
        
        # Return a random fallback quote
        import random
        fallback_quote = random.choice(fallback_quotes)
        fallback_quote["fallback_reason"] = e.message
        
        return fallback_quote


def convert_external_api_error_to_http_exception(error: ExternalAPIError) -> HTTPException:
    """
    Convert ExternalAPIError to FastAPI HTTPException
    
    Args:
        error: The ExternalAPIError to convert
        
    Returns:
        HTTPException with appropriate status code and detail
    """
    
    status_code_mapping = {
        502: status.HTTP_502_BAD_GATEWAY,
        503: status.HTTP_503_SERVICE_UNAVAILABLE,
        504: status.HTTP_504_GATEWAY_TIMEOUT,
        500: status.HTTP_500_INTERNAL_SERVER_ERROR
    }
    
    http_status = status_code_mapping.get(error.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return HTTPException(
        status_code=http_status,
        detail={
            "message": error.message,
            "error_type": "external_api_error",
            "api_response": error.api_response
        }
    )