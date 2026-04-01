from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str
    region: str | None = None

    model_config = {"from_attributes": True}


class UserUpdateIn(BaseModel):
    name: str | None = None
    region: str | None = None
