from sqlalchemy.orm import Session
from app.models.models import User, Token
from app.schemas.schemas import UserCreate, TokenCreate
from app.core.security import get_password_hash, verify_password, verify_token
from datetime import datetime
from typing import Optional, List

class UserService:
    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """Create a new user."""
        db_user = User(
            email=user.email,
            username=user.username,
            hashed_password=get_password_hash(user.password)
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        user = UserService.get_user_by_username(db, username)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

class TokenService:
    @staticmethod
    def create_token(db: Session, token_data: TokenCreate, user_id: int) -> Token:
        """Create a new token for a user."""
        db_token = Token(
            name=token_data.name,
            description=token_data.description,
            user_id=user_id,
            expires_at=token_data.expires_at
        )
        # Set owner for token generation
        db_token.owner = db.query(User).filter(User.id == user_id).first()
        db_token.generate_token()
        
        db.add(db_token)
        db.commit()
        db.refresh(db_token)
        return db_token
    
    @staticmethod
    def get_token_by_string(db: Session, token_string: str) -> Optional[Token]:
        """Get token by token string."""
        return db.query(Token).filter(Token.token == token_string, Token.is_active == True).first()
    
    @staticmethod
    def get_user_tokens(db: Session, user_id: int) -> List[Token]:
        """Get all active tokens for a user."""
        return db.query(Token).filter(Token.user_id == user_id, Token.is_active == True).all()
    
    @staticmethod
    def revoke_token(db: Session, token_id: int, user_id: int) -> bool:
        """Revoke a token (soft delete by setting is_active=False)."""
        db_token = db.query(Token).filter(Token.id == token_id, Token.user_id == user_id).first()
        if db_token:
            db_token.is_active = False
            db.commit()
            return True
        return False
    
    @staticmethod
    def validate_token_and_get_user(db: Session, token_string: str) -> Optional[User]:
        """Validate token and return associated user."""
        token = TokenService.get_token_by_string(db, token_string)
        if not token:
            return None
        
        # Check expiration
        if token.expires_at and token.expires_at < datetime.utcnow():
            return None
        
        # Update last used
        token.last_used_at = datetime.utcnow()
        db.commit()
        
        return token.owner

    @staticmethod
    def validate_jwt_and_get_user(db: Session, jwt_token: str) -> Optional[User]:
        """Validate JWT token and return associated user."""
        payload = verify_token(jwt_token)
        
        if payload is None:
            return None
            
        username = payload.get("sub")
        if username is None:
            return None
            
        user = UserService.get_user_by_username(db, username)
        return user