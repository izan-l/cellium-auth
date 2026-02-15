from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token, verify_token
from app.schemas.schemas import (
    LoginRequest, LoginResponse, TokenCreate, Token, 
    TokenValidationRequest, TokenValidationResponse
)
from app.services.auth_service import UserService, TokenService

router = APIRouter()
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current user from JWT token."""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    user = UserService.get_user_by_username(db, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint - authenticate user and return JWT token."""
    user = UserService.authenticate_user(db, request.username, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

@router.get("/tokens", response_model=list[Token])
async def list_tokens(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all tokens for the current user."""
    tokens = TokenService.get_user_tokens(db, current_user.id)
    return tokens

@router.post("/tokens", response_model=Token)
async def create_token(
    token_data: TokenCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new token for the current user."""
    token = TokenService.create_token(db, token_data, current_user.id)
    return token

@router.delete("/tokens/{token_id}")
async def revoke_token(
    token_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke a token."""
    success = TokenService.revoke_token(db, token_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )
    return {"message": "Token revoked successfully"}

@router.get("/test-token")
async def create_test_token(db: Session = Depends(get_db)):
    """Create a test token for development/testing purposes."""
    # Find or create test user
    test_user = UserService.get_user_by_username(db, "admin")
    if not test_user:
        return {"error": "Admin user not found. Please ensure admin user exists."}
    
    # Create a test token
    from app.schemas.schemas import TokenCreate
    from datetime import datetime, timedelta
    
    token_data = TokenCreate(
        name="Test Token for MCP",
        description="Auto-generated test token for MCP development",
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    
    test_token = TokenService.create_token(db, token_data, test_user.id)
    
    return {
        "token": test_token.token,
        "name": test_token.name,
        "user": test_user.username,
        "expires_at": test_token.expires_at,
        "format_info": {
            "expected_format": "user:username:randomhash",
            "actual_format": test_token.token,
            "format_valid": test_token.token.startswith("user:")
        }
    }

@router.post("/validate", response_model=TokenValidationResponse)
async def validate_token(request: TokenValidationRequest, db: Session = Depends(get_db)):
    """Validate a token and return user information."""
    user = TokenService.validate_token_and_get_user(db, request.token)
    
    if user:
        return TokenValidationResponse(valid=True, user=user)
    else:
        return TokenValidationResponse(valid=False, error="Invalid or expired token")

@router.post("/validate-jwt", response_model=TokenValidationResponse)
async def validate_jwt_token(request: TokenValidationRequest, db: Session = Depends(get_db)):
    """Validate a JWT token and return user information."""
    user = TokenService.validate_jwt_and_get_user(db, request.token)
    
    if user:
        return TokenValidationResponse(valid=True, user=user)
    else:
        return TokenValidationResponse(valid=False, error="Invalid or expired JWT token")