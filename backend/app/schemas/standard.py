from pydantic import BaseModel, Field


class StandardBase(BaseModel):
    is_number: str
    part: str | None = None
    title: str
    domain: str
    publication_date: str
    amendment_history: list[str] = Field(default_factory=list)
    superseded_by: str | None = None
    normative_references: list[str] = Field(default_factory=list)
    certification: str
    abstract: str
    tags: list[str] = Field(default_factory=list)
    pdf_url: str | None = None


class StandardCreate(StandardBase):
    pass


class StandardUpdate(BaseModel):
    is_number: str | None = None
    part: str | None = None
    title: str | None = None
    domain: str | None = None
    publication_date: str | None = None
    amendment_history: list[str] | None = None
    superseded_by: str | None = None
    normative_references: list[str] | None = None
    certification: str | None = None
    abstract: str | None = None
    tags: list[str] | None = None
    pdf_url: str | None = None


class StandardOut(StandardBase):
    id: int

    model_config = {"from_attributes": True}


class VersionInfo(BaseModel):
    current_version: str
    latest_version: str
    is_latest: bool
    amendments: list[str]
    superseded_by: str | None
    key_changes: str | None = None


class CertificationInfo(BaseModel):
    bis_certification: str
    crs_applicable: bool
    hallmarking: bool
    fmcs_note: str
    certification_portal_link: str


class AlliedStandards(BaseModel):
    normative_references: list[StandardOut]
    test_methods: list[StandardOut]
    safety_standards: list[StandardOut]
    installation_standards: list[StandardOut]
    related_products: list[StandardOut]


class RecommendedStandard(BaseModel):
    standard: StandardOut
    relevance_score: float
    version_info: VersionInfo
    certification_info: CertificationInfo
    allied_standards: AlliedStandards


class RecommendRequest(BaseModel):
    query: str = Field(..., min_length=2)
    top_k: int = Field(default=5, ge=1, le=10)
    source_language: str | None = None


class RecommendResponse(BaseModel):
    query: str
    query_translated: str | None = None
    detected_language: str
    latency_ms: float
    recommendations: list[RecommendedStandard]
