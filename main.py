from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from url_validator import validate_url
from database import SessionLocal, URLLog

app = FastAPI(title="URL Security Analyzer API")

# Pydantic models
class URLRequest(BaseModel):
    url: HttpUrl

class URLResponse(BaseModel):
    url: str
    score: float
    category: str
    reasons: list[str]
    status: str

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/check-url", response_model=URLResponse)
def check_url(request: URLRequest, db: Session = Depends(get_db)):
    result = validate_url(request.url)

    # Log to database
    log_entry = URLLog(
        url=result["url"],
        score=result["score"],
        category=result["category"]
    )
    log_entry.set_reasons(result["reasons"])
    db.add(log_entry)
    db.commit()

    if result["category"] != "SAFE":
        raise HTTPException(
            status_code=403,
            detail={
                "message": "URL blocked due to potential security threats.",
                "score": result["score"],
                "category": result["category"],
                "reasons": result["reasons"]
            }
        )

    return {
        "url": result["url"],
        "score": result["score"],
        "category": result["category"],
        "reasons": result["reasons"],
        "status": "URL is safe and allowed."
    }

@app.get("/logs", summary="View scanned URL history")
def get_logs(db: Session = Depends(get_db)):
    logs = db.query(URLLog).order_by(URLLog.timestamp.desc()).all()
    return [
        {
            "url": log.url,
            "score": log.score,
            "category": log.category,
            "reasons": log.get_reasons(),
            "timestamp": log.timestamp
        }
        for log in logs
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
