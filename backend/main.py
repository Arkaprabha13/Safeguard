import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager
import uvicorn

try:
    # Try relative imports first (when run as module)
    from .database import connect_to_mongo, close_mongo_connection, create_indexes
    from .routers import auth, users, contacts, activities
except ImportError:
    # Fall back to absolute imports (when run directly)
    from database import connect_to_mongo, close_mongo_connection, create_indexes
    from routers import auth, users, contacts, activities

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    await create_indexes()
    yield
    # Shutdown
    await close_mongo_connection()

# Create FastAPI app
app = FastAPI(
    title="SafeGuard API",
    description="Safety and emergency contact management system",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(contacts.router)
app.include_router(activities.router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to SafeGuard API",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "SafeGuard API"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8000,
        reload=True
    )
