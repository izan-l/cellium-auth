from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.core.database import get_db, engine
from app.models.models import Base
from app.routers import auth
from app.services.auth_service import UserService
from app.schemas.schemas import UserCreate
import os
from dotenv import load_dotenv

load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Excel MCP Auth Service",
    description="Authentication service for Excel MCP Bridge",
    version="1.0.0"
)

# CORS middleware
default_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    # Production add-in / web UI origin(s)
    "https://addin.cellium.dev",
]

origins_env = os.getenv("CORS_ALLOW_ORIGINS")
allow_origins = (
    [o.strip() for o in origins_env.split(",") if o.strip()]
    if origins_env
    else default_origins
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Create admin user if it doesn't exist."""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        
        # Check if admin user exists
        admin_user = UserService.get_user_by_email(db, admin_email)
        if not admin_user:
            admin_data = UserCreate(
                email=admin_email,
                username="admin",
                password=admin_password
            )
            admin_user = UserService.create_user(db, admin_data)
            admin_user.is_admin = True
            db.commit()
            print(f"Created admin user: {admin_email}")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    uvicorn.run("main:app", host=host, port=port, reload=debug)
