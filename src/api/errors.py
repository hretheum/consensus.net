"""
Error handling middleware and utilities for ConsensusNet API.

This module provides consistent error handling across all API endpoints.
"""
import json
import traceback
import uuid
from datetime import datetime
from typing import Union

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from .models import APIErrorResponse, APIErrorDetail


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


async def validation_exception_handler(request: Request, exc: Union[RequestValidationError, ValidationError]) -> JSONResponse:
    """
    Handle Pydantic validation errors with detailed error information.
    
    Args:
        request: The FastAPI request object
        exc: The validation exception
        
    Returns:
        JSONResponse with structured error information
    """
    request_id = str(uuid.uuid4())
    
    # Extract detailed error information
    details = []
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"]) if error["loc"] else None
        details.append(APIErrorDetail(
            code=error["type"],
            message=error["msg"],
            field=field
        ))
    
    error_response = APIErrorResponse(
        error_type="VALIDATION_ERROR",
        message="Request validation failed",
        details=details,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=json.loads(json.dumps(error_response.dict(), cls=DateTimeEncoder))
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions with consistent error format.
    
    Args:
        request: The FastAPI request object
        exc: The HTTP exception
        
    Returns:
        JSONResponse with structured error information
    """
    request_id = str(uuid.uuid4())
    
    # Determine error type based on status code
    error_type_mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED", 
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE"
    }
    
    error_type = error_type_mapping.get(exc.status_code, "HTTP_ERROR")
    
    # If the detail is already a structured error response, use it
    if isinstance(exc.detail, dict) and "error_type" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    
    # Create structured error response
    error_response = APIErrorResponse(
        error_type=error_type,
        message=str(exc.detail),
        details=[],
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=json.loads(json.dumps(error_response.dict(), cls=DateTimeEncoder)),
        headers=getattr(exc, 'headers', None)
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions with generic error response.
    
    Args:
        request: The FastAPI request object
        exc: The unhandled exception
        
    Returns:
        JSONResponse with generic error information
    """
    request_id = str(uuid.uuid4())
    
    # Log the full traceback (in production, use proper logging)
    print(f"Unhandled exception for request {request_id}:")
    print(traceback.format_exc())
    
    # Create generic error response (don't expose internal details)
    error_response = APIErrorResponse(
        error_type="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please try again later.",
        details=[APIErrorDetail(
            code="UNEXPECTED_ERROR",
            message="Internal server error occurred"
        )],
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=json.loads(json.dumps(error_response.dict(), cls=DateTimeEncoder))
    )


def create_error_response(
    error_type: str,
    message: str,
    status_code: int = 500,
    details: list = None,
    request_id: str = None
) -> APIErrorResponse:
    """
    Create a standardized error response.
    
    Args:
        error_type: Machine-readable error type
        message: Human-readable error message
        status_code: HTTP status code
        details: List of detailed error information
        request_id: Optional request identifier
        
    Returns:
        APIErrorResponse object
    """
    if details is None:
        details = []
    
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    return APIErrorResponse(
        error_type=error_type,
        message=message,
        details=details,
        request_id=request_id
    )