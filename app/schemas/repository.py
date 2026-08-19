"""
Pydantic schemas — API request/response validation ke liye.

ORM Model vs Pydantic Schema:
- ORM Model = database table represent karta hai
- Pydantic Schema = API input/output validate karta hai
- Dono alag hain — yeh important separation hai
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class RepositoryCreate(BaseModel):
    """
    POST /repositories ke liye request body.
    User yeh data dega.
    """
    # Path required hai — bina path ke kya analyze karein?
    path: str = Field(..., description="Local path to the repository")
    # Name optional hai — default folder ka naam hoga
    name: str | None = Field(None, description="Custom name for the repository")
    # URL optional hai — GitHub link store karne ke liye
    url: str | None = Field(None, description="Git URL of the repository")


class RepositoryResponse(BaseModel):
    """
    Repository endpoints ka response.
    User ko yeh data milega.
    """
    id: UUID
    name: str
    path: str
    url: str | None
    language: str | None
    total_files: int | None
    total_lines: int | None
    created_at: datetime

    class Config:
        # ORM model se directly banane ki permission
        from_attributes = True


class RepositoryIngestResponse(BaseModel):
    """
    Repository ingestion ka detailed response.
    """
    repository: RepositoryResponse
    # Kitni files analyze ki ja sakti hain
    analyzable_files: int
    # Kaunse frameworks mile
    frameworks: list[str]
    # Kaunsi files entry points hain
    entry_points: list[str]
    # Ingestion successful raha?
    message: str