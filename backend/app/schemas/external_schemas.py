from pydantic import BaseModel, Field
from typing import List, Optional


class QuoteResponse(BaseModel):
    """Schema for quote response"""
    content: str = Field(..., min_length=1, max_length=1000, description="The quote text")
    author: str = Field(..., min_length=1, max_length=200, description="The author of the quote")
    tags: List[str] = Field(default_factory=list, description="Tags associated with the quote")
    length: int = Field(..., ge=1, description="Character length of the quote")
    source: str = Field(..., description="Source of the quote (API or fallback)")
    fallback_reason: Optional[str] = Field(None, description="Reason for using fallback if applicable")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "The only way to do great work is to love what you do.",
                "author": "Steve Jobs",
                "tags": ["motivational", "work"],
                "length": 52,
                "source": "quotable.io"
            }
        }


class ExternalAPIError(BaseModel):
    """Schema for external API error responses"""
    message: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")
    api_response: Optional[dict] = Field(None, description="Original API response if available")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "External API is currently unavailable",
                "error_type": "external_api_error",
                "api_response": {
                    "status_code": 503,
                    "text": "Service Unavailable"
                }
            }
        }


class QuoteWithMetadata(QuoteResponse):
    """Extended quote response with additional metadata"""
    fetched_at: str = Field(..., description="ISO timestamp when quote was fetched")
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracking")
    cache_status: Optional[str] = Field(None, description="Cache status (hit/miss/disabled)")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Innovation distinguishes between a leader and a follower.",
                "author": "Steve Jobs",
                "tags": ["innovation", "leadership"],
                "length": 61,
                "source": "quotable.io",
                "fetched_at": "2025-10-04T10:30:00Z",
                "request_id": "req_123456789",
                "cache_status": "miss"
            }
        }