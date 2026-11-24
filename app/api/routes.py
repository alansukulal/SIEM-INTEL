
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.config import settings
from app.agent.service import run_investigation
from app.services.investigation_service import (
    create_investigation,
    engine,
)
from app.services.investigation_service import (
    create_investigation,
    update_investigation_status,
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

    investigation_id = str(investigation["id"])
    tenant_id = str(investigation["tenant_id"])
    thread_id = investigation["thread_id"]

    try:
        # Execute the existing SIEM-INTEL graph.
        result = run_investigation(
            tenant_id=tenant_id,
            investigation_id=investigation_id,
            thread_id=thread_id,
            alert=request.alert,
            siem=request.siem,
        )

        # Mark investigation as completed.
        update_investigation_status(
            tenant_id=tenant_id,
            investigation_id=investigation_id,
            status="completed",
        )

        return result

    except Exception as exc:

        try:
            update_investigation_status(
                tenant_id=tenant_id,
                investigation_id=investigation_id,
                status="failed",
            )
        except Exception:
            # Preserve the original investigation error.
            pass

        raise HTTPException(
            status_code=500,
            detail="Investigation execution failed",
        ) from exc