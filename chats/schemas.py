from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)
from typing import (
    Any,
    Optional,
)


class MessageCreate(BaseModel):
    receiver: EmailStr = Field(
        ..., example="The recipient email for this message."
    )
    content: str = Field(..., example="The message text content.", max_length=1024)
    message_type: str = Field(
        ..., example="Message type(e.g. 'text' or 'media')", max_length=10
    )
    media: Optional[str] = Field(
        None,
        example="A relative URL to the local file storage.",
        max_length=120
    )


class MessageCreateRoom(BaseModel):


    room: str = Field(
        ..., example="A unique room name(e.g. 'nerds'). Case Sensitive.", max_length=10
    )
    content: str = Field(..., example="The message text content.", max_length=1024)
    message_type: str = Field(
        ..., example="Message type(e.g. 'text' or 'media')", max_length=10
    )
    media: Optional[str] = Field(
        None, example="A dictionary that contains media url, type...", max_length=120
    )


class GetAllMessageResults(BaseModel):

    status_code: int = Field(..., example=200)
    result: list[dict[str, Any]]


class DeleteChatMessages(BaseModel):
    contact: EmailStr = Field(
        ...,
        example="The recipient email for the sent messages to be deleted.",
    )