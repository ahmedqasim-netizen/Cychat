from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)
from typing import (
    Optional,
)

from app.users.models import (
    ChatStatus,
    UserRole,
)


class UserObjectSchema(BaseModel):

    id: int = Field(..., example=1)
    nickname: str = Field(..., example="JohnDoe")
    email: EmailStr = Field(..., example="testing@gmail.com")
    phone_number: Optional[str] = Field(None, example="123456789")
    user_role: Optional[str] = Field("user", example=UserRole.user)
    public_key: Optional[str] = Field(None, example="Base64 encoded ECDH public key for E2E encryption")


    class Config:
        from_attributes = True


class UserLoginSchema(BaseModel):

    email: EmailStr = Field(..., example="testing@gmail.com")
    password: str = Field(..., example="A secure password goes here.")


class UpdateStatus(BaseModel):

    chat_status: str = Field(..., example=ChatStatus.online)


class PersonalInfo(BaseModel):

    nickname: str = Field(..., example="JohnDoe")
    phone_number: Optional[str] = Field(None, example="123456789")


class ResetPassword(BaseModel):

    old_password: str = Field(..., example="Your old password.")
    new_password: str = Field(..., example="Your new password.")
    confirm_password: str = Field(..., example="Your new password.")


class UpdatePublicKey(BaseModel):

    public_key: str = Field(..., example="Base64 encoded ECDH public key", max_length=500)