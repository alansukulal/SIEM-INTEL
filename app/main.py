from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="SIEM-INTEL",
    description="Agentic SIEM investigation and automation platform",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "SIEM-INTEL is running"
    }


app.include_router(router)
