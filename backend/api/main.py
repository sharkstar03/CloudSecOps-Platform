from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import logging
from typing import List

from .routes import aws_routes, azure_routes, vulnerability_routes, compliance_routes
from .models import database
from .utils.auth import get_current_user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CloudSecOps Platform API",
    description="API for cloud security operations platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database initialization
@app.on_event("startup")
async def startup():
    logger.info("Starting up the CloudSecOps Platform API")
    await database.init_db()

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down the CloudSecOps Platform API")
    await database.close_db()

# Include routers
app.include_router(aws_routes.router, prefix="/api/aws", tags=["AWS"])
app.include_router(azure_routes.router, prefix="/api/azure", tags=["Azure"])
app.include_router(vulnerability_routes.router, prefix="/api/vulnerabilities", tags=["Vulnerabilities"])
app.include_router(compliance_routes.router, prefix="/api/compliance", tags=["Compliance"])

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "CloudSecOps Platform API",
        "version": "1.0.0",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=int(os.getenv("PORT", "8000")), 
        reload=True
    )