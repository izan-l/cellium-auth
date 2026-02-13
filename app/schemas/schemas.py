from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Token Schemas
class TokenBase(BaseModel):
    name: str
    description: Optional[str] = None

class TokenCreate(TokenBase):
    expires_at: Optional[datetime] = None

class TokenUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class Token(TokenBase):
    id: int
    token: str
    user_id: int
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Auth Schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: User

class TokenValidationRequest(BaseModel):
    token: str

class TokenValidationResponse(BaseModel):
    valid: bool
    user: Optional[User] = None
    error: Optional[str] = None