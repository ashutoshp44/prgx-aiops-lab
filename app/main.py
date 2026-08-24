from fastapi import FastAPI
from datetime import datetime, timezone

app = FastAPI(
    title="PRGX AIOps API",
    version="1.0.0"
)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "prgx-aiops-api",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/")
def root():
    return {
        "message": "PRGX AIOps API is running"
    }


@app.get("/predict")
def predict():
    return {
        "prediction": "normal",
        "confidence": 0.95
    }
