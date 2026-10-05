# we define the http method and fns here

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(prefix="/api/v1")


class InvestigationRequest(BaseModel):
    alert: str
    siem: str


@router.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "SIEM-INTEL",
    }


@router.post("/investigations")
def create_investigation(request: InvestigationRequest):

    return {
        "message": "Investigation received",
        "alert": request.alert,
        "siem": request.siem,
    }