from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)
from typing import (
    Dict,
    Optional,
)

from app.users.schemas import (
    UserObjectSchema,
)


class UserSchema(BaseModel):
    user: Optional[UserObjectSchema] = Field(
        ...,
        example=UserObjectSchema(
            id=1,
            nickname="JohnDoe",
            email="testing@gmail.com",
            phone_number="123456789",
            user_role="user",
        ),
    )
    token: Optional[Dict[str, str]] = Field(
        ..., example="Token value(e.g. 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9')"
    )
    status_code: int = Field(
        ...,
        example="A response status code. (e.g. 200 on a successful attempt.)",
    )
    message: str = Field(
        ...,
        example="A message to indicate whether or not the login was successful!",
    )


class UserLoginSchema(BaseModel):
    email: EmailStr = Field(..., example="Your email address to log in.")
    password: str = Field(..., example="A secure password goes here.")


class UserCreate(BaseModel):
    nickname: str = Field(..., example="Your nickname.", max_length=40)
    email: str = Field(
        ..., example="Your email address to register into the app.", max_length=50
    )
    password: str = Field(..., example="A secure password goes here.", max_length=120)
    phone_number: Optional[str] = Field(None, example="Your phone number.", max_length=20)


class Token(BaseModel):
    access_token: str = Field(
        ..., example="Token value(e.g. 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9')"
    )


class TokenData(BaseModel):
    email: Optional[str] = Field(..., example="Your email address.")


class ResponseSchema(BaseModel):

    status_code: int = Field(
        ...,
        example=400,
    )
    message: str = Field(
        ...,
        example="A message to indicate that the request was not successful!",
    )