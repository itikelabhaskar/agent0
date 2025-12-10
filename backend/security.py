"""
Security utilities: SQL sanitization, authentication, authorization
"""
import re
from fastapi import HTTPException, Header, Depends, Request
from typing import Optional
import sqlparse
from backend.config import config
from agent.tools import run_bq_query

# ============================================
# SQL SANITIZATION
# ============================================

DANGEROUS_PATTERNS = [
    r'\bDROP\b', r'\bDELETE\b', r'\bTRUNCATE\b', r'\bINSERT\b',
    r'\bUPDATE\b', r'\bCREATE\b', r'\bALTER\b', r'\bGRANT\b',
    r'\bREVOKE\b', r'\bEXEC\b', r'\b--\b', r'/\*', r'\*/',
    r';.*SELECT', r'UNION.*SELECT'
]

def sanitize_sql(sql: str, allow_only_select: bool = True) -> str:
    """
    Sanitize SQL to prevent injection attacks
    
    Args:
        sql: SQL query string
        allow_only_select: If True, only allow SELECT statements
        
    Returns:
        Sanitized SQL
        
    Raises:
        HTTPException: If SQL contains dangerous patterns
    """
    sql_upper = sql.upper().strip()
    
    # Check if starts with SELECT (if required)
    if allow_only_select and not sql_upper.startswith('SELECT'):
        raise HTTPException(
            status_code=400,
            detail="Only SELECT queries are allowed"
        )
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, sql_upper):
            raise HTTPException(
                status_code=400,
                detail=f"SQL contains disallowed pattern: {pattern}"
            )
    
    # Parse SQL to validate syntax
    try:
        parsed = sqlparse.parse(sql)
        if not parsed:
            raise HTTPException(status_code=400, detail="Invalid SQL syntax")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL parsing error: {e}")
    
    return sql

def sanitize_identifier(identifier: str) -> str:
    """
    Sanitize table/column identifiers
    Only allow alphanumeric, underscore, dash, dot
    """
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', identifier):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid identifier: {identifier}"
        )
    return identifier

def build_parameterized_query(template: str, **params) -> str:
    """
    Build parameterized query safely
    
    Example:
        build_parameterized_query(
            "SELECT * FROM {table} WHERE customer_id = @customer_id",
            table=sanitize_identifier("customers"),
            customer_id=123
        )
    """
    sanitized_params = {}
    for key, value in params.items():
        if isinstance(value, str) and not key.startswith('table'):
            # Escape single quotes in string values
            sanitized_params[key] = value.replace("'", "''")
        else:
            sanitized_params[key] = value
    
    return template.format(**sanitized_params)

# ============================================
# AUTHENTICATION & AUTHORIZATION
# ============================================

def get_api_key(x_api_key: Optional[str] = Header(None)) -> Optional[str]:
    """Extract API key from header"""
    return x_api_key

def verify_api_key(api_key: Optional[str] = Depends(get_api_key)):
    """
    Verify API key for protected endpoints
    Skips check if ENABLE_AUTH=false
    """
    if not config.ENABLE_AUTH:
        return None
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide X-API-Key header"
        )
    
    if api_key != config.API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    
    return api_key

async def get_current_user(request: Request, api_key: str = Depends(verify_api_key)):
    """
    Get current user from session or header
    Falls back to admin if auth disabled
    """
    if not config.ENABLE_AUTH:
        return {
            "user_id": "system",
            "email": "system@agentx.local",
            "role": "admin"
        }
    
    # Try to get user from custom header
    user_email = request.headers.get("X-User-Email")
    if not user_email:
        raise HTTPException(
            status_code=401,
            detail="User email required. Provide X-User-Email header"
        )
    
    # Lookup user in database
    from backend.enhancements import get_user_by_email
    user = get_user_by_email(user_email)
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User not found: {user_email}"
        )
    
    return user

def require_role(required_role: str):
    """
    Dependency to require specific role
    
    Usage:
        @app.post("/admin-only")
        async def admin_endpoint(user = Depends(require_role("admin"))):
            ...
    """
    async def role_checker(user = Depends(get_current_user)):
        from backend.enhancements import check_permission
        if not check_permission(user["role"], required_role):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required role: {required_role}, your role: {user['role']}"
            )
        return user
    return role_checker

# ============================================
# RATE LIMITING (Simple in-memory)
# ============================================

from collections import defaultdict
from datetime import datetime, timedelta

rate_limit_store = defaultdict(list)

def check_rate_limit(identifier: str, max_requests: int = 100, window_minutes: int = 1):
    """
    Simple rate limiting
    
    Args:
        identifier: User ID or IP address
        max_requests: Max requests per window
        window_minutes: Time window in minutes
    """
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=window_minutes)
    
    # Clean old requests
    rate_limit_store[identifier] = [
        ts for ts in rate_limit_store[identifier] 
        if ts > window_start
    ]
    
    # Check limit
    if len(rate_limit_store[identifier]) >= max_requests:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {max_requests} requests per {window_minutes} minute(s)"
        )
    
    # Add current request
    rate_limit_store[identifier].append(now)

