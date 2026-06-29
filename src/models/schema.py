from pydantic import BaseModel, Field
from typing import Optional, List


class Provenance(BaseModel):
    field: str
    source: str
    confidence: float
    method: str


class Skill(BaseModel):
    name: str
    confidence: float
    sources: List[str]


class Experience(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    summary: Optional[str] = None


class Education(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    end_year: Optional[int] = None


class CandidateProfile(BaseModel):
    candidate_id: str

    full_name: Optional[str] = None
    headline: Optional[str] = None

    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)

    skills: List[Skill] = Field(default_factory=list)

    experience: List[Experience] = Field(default_factory=list)

    education: List[Education] = Field(default_factory=list)

    overall_confidence: float = 0.0

    provenance: List[Provenance] = Field(default_factory=list)