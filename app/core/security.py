import os
import hashlib
from jose import JWTError, jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return get_password_hash(plain_password) == hashed_password

def get_password_hash(password: str) -> str:
    """Hash a password using SHA-256 (simple for development)."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None