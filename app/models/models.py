from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to tokens
    tokens = relationship("Token", back_populates="owner")

class Token(Base):
    __tablename__ = "tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)  # User-friendly name for the token
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiration
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    description = Column(Text, nullable=True)
    
    # Relationship to user
    owner = relationship("User", back_populates="tokens")
    
    def generate_token(self):
        """Generate a new token string."""
        self.token = f"user:{self.owner.username}:{uuid.uuid4().hex[:12]}"
        return self.token