from pydantic import BaseModel, Field

class SWOTAnalysisModel(BaseModel):
    """Pydantic model representing structured SWOT metrics."""
    strengths: list[str] = Field(description="Internal strengths of the competitor.")
    weaknesses: list[str] = Field(description="Internal weaknesses of the competitor.")
    opportunities: list[str] = Field(description="Market or technical opportunities.")
    threats: list[str] = Field(description="Competitive threats posed by them.")

class PricingFeatureComparison(BaseModel):
    """Structured pricing tier comparisons."""
    tier_name: str
    price: str
    key_features: list[str]
    billing_cycle: str

class JobPostingTrend(BaseModel):
    """Job listing details mapped from linkedin/career crawls."""
    title: str
    department: str
    location: str
    inferred_skills: list[str]
