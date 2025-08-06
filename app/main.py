# app/main.py
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from core.config import settings
from core.logger import setup_logger
from app.api.v1.router import router as api_router

# Setup logger
logger = setup_logger()

# In a startup script or at the top of main.py, before the app starts

import os
import json

# Assume 'load_secret_from_manager' is your function to get the JSON string
def load_secret_from_manager():
    # In a real app, this would fetch from HashiCorp Vault, AWS Secrets Manager, etc.
    # For this example, we'll just read from a local file to simulate.
    with open("secrets/logistics-truck-8e649bec2a5b.json", "r") as f:
        return f.read()

def setup_gcp_credentials():
    """
    Loads the GCP credential from a secret manager and saves it to a temporary file.
    Sets the required environment variable.
    """
    gcp_json_content = load_secret_from_manager()
    
    # Define a path for the temporary credentials file
    credentials_path = "secrets/logistics-truck-8e649bec2a5b.json"

    # Write the content to the file
    with open(credentials_path, "w") as f:
        f.write(gcp_json_content)
    
    # Set the environment variable that Google Cloud libraries automatically look for
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    print(f"GCP credentials set up at: {credentials_path}")

# Run this setup function before initializing any services
setup_gcp_credentials()

# Initialize FastAPI app
app = FastAPI(
    title="Agentic RAG Backend",
    description="Modular backend for Agentic RAG system with Pinecone, Gemini, and LangChain",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != settings.API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return credentials.credentials

# Include API routes
app.include_router(api_router, prefix="/api/v1", dependencies=[Depends(verify_token)])

@app.get("/")
async def root():
    return {"message": "Agentic RAG Backend is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )