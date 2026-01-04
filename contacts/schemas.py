from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)
from typing import (
    Optional,
)

from app.users.schemas import (
    UserObjectSchema,
)


class ContactCreate(BaseModel):
    user: str
    contact: str
    favourite: Optional[str] = None


class GetAllContactsResults(BaseModel):
    status_code: int = Field(..., example=200)
    result: list[UserObjectSchema]


class AddContact(BaseModel):
    contact: EmailStr = Field(..., example="contact@example.com")