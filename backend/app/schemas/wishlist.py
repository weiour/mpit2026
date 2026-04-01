from pydantic import BaseModel


class WishlistCreate(BaseModel):
    title: str
    description: str | None = None
    url: str | None = None
    price: int | None = None
    priority: str | None = "medium"
    status: str | None = "active"


class WishlistUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    url: str | None = None
    price: int | None = None
    priority: str | None = None
    status: str | None = None


class WishlistOut(BaseModel):
    id: int
    title: str
    description: str | None
    url: str | None
    price: int | None
    priority: str | None
    status: str | None
    event_id: int

    model_config = {"from_attributes": True}
