from pydantic import BaseModel


class KQLGenerationResult(BaseModel):
    kql: str
    reason: str