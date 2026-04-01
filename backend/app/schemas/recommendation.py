from pydantic import BaseModel, Field


class VenueRecommendationOut(BaseModel):
    id: str
    name: str
    address: str | None = None
    rating: float | None = None
    review_count: int | None = None
    price_note: str | None = None
    source_query: str | None = None
    reason: str
    source: str = "2gis"
    tags: list[str] = Field(default_factory=list)
    yandex_maps_url: str | None = None
    two_gis_url: str | None = None


class RecommendationMetaOut(BaseModel):
    city: str | None = None
    provider: str
    generated_summary: str
    search_queries: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class VenueRecommendationsOut(BaseModel):
    items: list[VenueRecommendationOut] = Field(default_factory=list)
    meta: RecommendationMetaOut
