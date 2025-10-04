import httpx
import asyncio
import ssl
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import logging

# Configure logging
logger = logging.getLogger(__name__)

# External API configuration
QUOTE_API_URL = "https://api.quotable.io/random"
REQUEST_TIMEOUT = 10.0  # 10 seconds timeout
MAX_RETRIES = 3

# SSL configuration for handling certificate issues
SSL_VERIFY = True  # Set to False in development if needed


class ExternalAPIError(Exception):
    """Custom exception for external API errors"""
    def __init__(self, message: str, status_code: int = 500, api_response: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.api_response = api_response
        super().__init__(self.message)


async def fetch_random_quote() -> Dict[str, Any]:
    """
    Fetch a random motivational quote from quotable.io API with SSL fallback
    
    Returns:
        Dict containing quote data with keys: content, author, tags, length
        
    Raises:
        ExternalAPIError: When API request fails or returns invalid data
    """
    
    last_exception = None
    
    # Try with SSL verification first, then without if SSL issues occur
    for verify_ssl in [True, False]:
        try:
            async with httpx.AsyncClient(
                timeout=REQUEST_TIMEOUT,
                verify=verify_ssl,
                follow_redirects=True
            ) as client:
                retry_count = 0
                
                while retry_count < MAX_RETRIES:
                    try:
                        ssl_mode = "strict" if verify_ssl else "lenient"
                        logger.info(f"Fetching quote from API (attempt {retry_count + 1}/{MAX_RETRIES}, SSL: {ssl_mode})")
                        
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
                            
                            logger.info(f"Successfully fetched quote by {data.get('author')} (SSL: {ssl_mode})")
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
                        break  # Exit retry loop to try next SSL setting
                        
                    except httpx.RequestError as e:
                        last_exception = e
                        retry_count += 1
                        
                        # Check if it's an SSL error
                        error_str = str(e).lower()
                        is_ssl_error = any(ssl_term in error_str for ssl_term in [
                            'ssl', 'certificate', 'cert', 'tls', 'handshake'
                        ])
                        
                        if is_ssl_error and verify_ssl:
                            logger.warning(f"SSL error detected: {str(e)}, will retry with relaxed SSL")
                            break  # Exit retry loop to try without SSL verification
                        
                        logger.warning(f"Request error: {str(e)} (attempt {retry_count}/{MAX_RETRIES})")
                        
                        if retry_count < MAX_RETRIES:
                            wait_time = 2 ** retry_count  # Exponential backoff
                            await asyncio.sleep(wait_time)
                            continue
                        break  # Exit retry loop
                        
                    except Exception as e:
                        # Unexpected errors
                        last_exception = e
                        logger.error(f"Unexpected error fetching quote: {str(e)}")
                        break  # Exit retry loop
                
                # If we got here with verify_ssl=False, SSL fallback also failed
                if not verify_ssl:
                    break
                    
        except Exception as e:
            last_exception = e
            logger.error(f"Failed to create HTTP client (SSL: {verify_ssl}): {str(e)}")
            if not verify_ssl:  # If even relaxed SSL failed, give up
                break
    
    # All attempts exhausted
    logger.error(f"All attempts failed, last error: {str(last_exception)}")
    
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
            "length": 59,
            "source": "local_fallback"
        },
        {
            "content": "Life is what happens to you while you're busy making other plans.",
            "author": "John Lennon",
            "tags": ["life", "planning"],
            "length": 64,
            "source": "local_fallback"
        },
        {
            "content": "The future belongs to those who believe in the beauty of their dreams.",
            "author": "Eleanor Roosevelt",
            "tags": ["future", "dreams", "motivation"],
            "length": 69,
            "source": "local_fallback"
        },
        {
            "content": "It is during our darkest moments that we must focus to see the light.",
            "author": "Aristotle",
            "tags": ["perseverance", "hope"],
            "length": 68,
            "source": "local_fallback"
        },
        {
            "content": "Success is not final, failure is not fatal: it is the courage to continue that counts.",
            "author": "Winston Churchill",
            "tags": ["success", "failure", "courage"],
            "length": 84,
            "source": "local_fallback"
        },
        {
            "content": "The way to get started is to quit talking and begin doing.",
            "author": "Walt Disney",
            "tags": ["action", "motivation"],
            "length": 57,
            "source": "local_fallback"
        },
        {
            "content": "Don't let yesterday take up too much of today.",
            "author": "Will Rogers",
            "tags": ["present", "motivation"],
            "length": 45,
            "source": "local_fallback"
        },
        {
            "content": "You learn more from failure than from success. Don't let it stop you. Failure builds character.",
            "author": "Unknown",
            "tags": ["failure", "learning", "character"],
            "length": 95,
            "source": "local_fallback"
        },
        {
            "content": "If you are working on something that you really care about, you don't have to be pushed. The vision pulls you.",
            "author": "Steve Jobs",
            "tags": ["passion", "vision", "work"],
            "length": 113,
            "source": "local_fallback"
        }
    ]
    
    try:
        # Try to fetch from external API first
        return await fetch_random_quote()
        
    except ExternalAPIError as e:
        # External API failed, use fallback quote
        import random
        fallback_quote = random.choice(fallback_quotes)
        fallback_quote["fallback_reason"] = e.message
        
        logger.warning(f"External API failed: {e.message}, using fallback quote")
        return fallback_quote


def convert_external_api_error_to_http_exception(error: ExternalAPIError) -> HTTPException:
    """
    Convert ExternalAPIError to FastAPI HTTPException
    
    Args:
        error: The ExternalAPIError to convert
        
    Returns:
        HTTPException with appropriate status code and detail
    """
    
    detail = {
        "message": error.message,
        "error_type": "external_api_error"
    }
    
    if error.api_response:
        detail["api_response"] = str(error.api_response)
    
    return HTTPException(
        status_code=error.status_code,
        detail=detail
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