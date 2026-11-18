
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.config import settings
from app.agent.service import run_investigation
from app.services.investigation_service import (
    create_investigation,
    engine,
)

router = APIRouter(prefix="/api/v1")


class InvestigationRequest(BaseModel):
    alert: str = Field(min_length=1, max_length=5000)
    siem: str = Field(min_length=1, max_length=100)


@router.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "SIEM-INTEL",
    }


@router.post("/investigations")
def create_new_investigation(request: InvestigationRequest):

    tenant_id = settings.dev_tenant_id

    # Verify that the development tenant exists.
    with engine.connect() as connection:
        tenant = connection.execute(
            text("""
                SELECT id
                FROM tenants
                WHERE id = :tenant_id
            """),
            {"tenant_id": tenant_id},
        ).scalar_one_or_none()

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    # Create the investigation record first.
    investigation = create_investigation(
        tenant_id=tenant_id,
        alert=request.alert,
    )

    # Execute the existing SIEM-INTEL graph.
    result = run_investigation(
        tenant_id=str(investigation["tenant_id"]),
        investigation_id=str(investigation["id"]),
        thread_id=investigation["thread_id"],
        alert=request.alert,
        siem=request.siem,
    )

    return result
