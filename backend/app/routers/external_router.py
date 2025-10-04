import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from services.external_service import (
    fetch_random_quote,
    fetch_quote_with_fallback,
    ExternalAPIError,
    convert_external_api_error_to_http_exception
)
from schemas.external_schemas import QuoteResponse, QuoteWithMetadata
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/external", tags=["external"])


@router.get("/quote", response_model=QuoteResponse)
async def get_random_quote(
    use_fallback: bool = Query(
        True, 
        description="Whether to use fallback quotes if external API fails"
    )
):
    """
    Fetch a random motivational quote from an external API.
    
    This endpoint fetches quotes from quotable.io API with the following features:
    - **Automatic retries** with exponential backoff for transient failures
    - **Fallback quotes** when external API is unavailable (if enabled)
    - **Proper error handling** with detailed error messages
    - **Rate limiting protection** with intelligent retry logic
    
    **Query Parameters:**
    - `use_fallback`: If True (default), returns local fallback quotes when API fails.
                     If False, returns error when external API is unavailable.
    
    **Error Responses:**
    - `502 Bad Gateway`: External API returned invalid response
    - `503 Service Unavailable`: External API is temporarily unavailable  
    - `504 Gateway Timeout`: External API request timed out
    
    **Example Response:**
    ```json
    {
        "content": "The only way to do great work is to love what you do.",
        "author": "Steve Jobs",
        "tags": ["motivational", "work"],
        "length": 52,
        "source": "quotable.io"
    }
    ```
    """
    
    request_id = str(uuid.uuid4())
    logger.info(f"Quote request started [ID: {request_id}]")
    
    try:
        if use_fallback:
            # Use service with fallback capability
            quote_data = await fetch_quote_with_fallback()
            logger.info(f"Quote fetched successfully [ID: {request_id}] from {quote_data.get('source')}")
        else:
            # Use service without fallback - will raise exception on failure
            quote_data = await fetch_random_quote()
            logger.info(f"Quote fetched successfully [ID: {request_id}] from external API")
        
        return QuoteResponse(**quote_data)
        
    except ExternalAPIError as e:
        logger.error(f"External API error [ID: {request_id}]: {e.message}")
        raise convert_external_api_error_to_http_exception(e)
    
    except Exception as e:
        logger.error(f"Unexpected error [ID: {request_id}]: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "An unexpected error occurred while fetching quote",
                "error_type": "internal_server_error",
                "request_id": request_id
            }
        )


@router.get("/quote/detailed", response_model=QuoteWithMetadata)
async def get_random_quote_with_metadata(
    use_fallback: bool = Query(
        True, 
        description="Whether to use fallback quotes if external API fails"
    )
):
    """
    Fetch a random motivational quote with additional metadata.
    
    This endpoint provides the same functionality as `/external/quote` but includes
    additional metadata such as fetch timestamp and request tracking information.
    
    **Additional Metadata:**
    - `fetched_at`: ISO timestamp when the quote was retrieved
    - `request_id`: Unique identifier for request tracking
    - `cache_status`: Future cache implementation status
    
    **Example Response:**
    ```json
    {
        "content": "Innovation distinguishes between a leader and a follower.",
        "author": "Steve Jobs", 
        "tags": ["innovation", "leadership"],
        "length": 61,
        "source": "quotable.io",
        "fetched_at": "2025-10-04T10:30:00Z",
        "request_id": "req_123456789",
        "cache_status": "miss"
    }
    ```
    """
    
    request_id = f"req_{uuid.uuid4().hex[:10]}"
    fetch_time = datetime.utcnow().isoformat() + "Z"
    
    logger.info(f"Detailed quote request started [ID: {request_id}]")
    
    try:
        if use_fallback:
            quote_data = await fetch_quote_with_fallback()
        else:
            quote_data = await fetch_random_quote()
        
        # Add metadata
        quote_data.update({
            "fetched_at": fetch_time,
            "request_id": request_id,
            "cache_status": "miss"  # Future implementation
        })
        
        logger.info(f"Detailed quote fetched successfully [ID: {request_id}]")
        return QuoteWithMetadata(**quote_data)
        
    except ExternalAPIError as e:
        logger.error(f"External API error [ID: {request_id}]: {e.message}")
        raise convert_external_api_error_to_http_exception(e)
    
    except Exception as e:
        logger.error(f"Unexpected error [ID: {request_id}]: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "An unexpected error occurred while fetching detailed quote",
                "error_type": "internal_server_error", 
                "request_id": request_id
            }
        )


@router.get("/quote/health", tags=["health"])
async def check_external_api_health():
    """
    Check the health of the external quote API.
    
    This endpoint performs a health check on the external quotable.io API
    without using fallbacks. Useful for monitoring and alerting.
    
    **Response:**
    - `200 OK`: External API is working correctly
    - `502/503/504`: External API has issues (see error details)
    
    **Example Success Response:**
    ```json
    {
        "status": "healthy",
        "api_source": "quotable.io",
        "response_time_ms": 245,
        "last_check": "2025-10-04T10:30:00Z"
    }
    ```
    """
    
    check_id = f"health_{uuid.uuid4().hex[:8]}"
    start_time = datetime.utcnow()
    
    logger.info(f"API health check started [ID: {check_id}]")
    
    try:
        # Perform health check by fetching a quote
        quote_data = await fetch_random_quote()
        
        end_time = datetime.utcnow()
        response_time = int((end_time - start_time).total_seconds() * 1000)
        
        logger.info(f"API health check passed [ID: {check_id}] in {response_time}ms")
        
        return {
            "status": "healthy",
            "api_source": quote_data.get("source", "unknown"),
            "response_time_ms": response_time,
            "last_check": end_time.isoformat() + "Z",
            "check_id": check_id
        }
        
    except ExternalAPIError as e:
        logger.warning(f"API health check failed [ID: {check_id}]: {e.message}")
        
        end_time = datetime.utcnow()
        response_time = int((end_time - start_time).total_seconds() * 1000)
        
        # Return 503 Service Unavailable for health check failures
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "api_source": "quotable.io",
                "error_message": e.message,
                "response_time_ms": response_time,
                "last_check": end_time.isoformat() + "Z",
                "check_id": check_id
            }
        )
    
    except Exception as e:
        logger.error(f"Health check error [ID: {check_id}]: {str(e)}")
        
        end_time = datetime.utcnow()
        response_time = int((end_time - start_time).total_seconds() * 1000)
        
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error_message": "Health check failed due to internal error",
                "response_time_ms": response_time,
                "last_check": end_time.isoformat() + "Z",
                "check_id": check_id
            }
        )