#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import uvicorn

app = FastAPI(title="URL Security Analyzer API - Minimal")

# Pydantic models
class URLRequest(BaseModel):
    url: HttpUrl

class URLResponse(BaseModel):
    url: str
    score: float
    category: str
    reasons: list[str]
    status: str

@app.post("/check-url", response_model=URLResponse)
def check_url(request: URLRequest):
    # Simple mock response for testing
    return {
        "url": str(request.url),
        "score": 0.95,
        "category": "SAFE",
        "reasons": ["Test response"],
        "status": "URL is safe and allowed."
    }

@app.get("/logs")
def get_logs():
    return []

if __name__ == "__main__":
    print("Starting minimal server...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 