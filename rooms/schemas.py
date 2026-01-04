import datetime
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)
from typing import (
    Union,
)


class RoomCreate(BaseModel):

    join: int = Field(..., example=0, description="0 to create, 1 to join")
    room_name: str = Field(..., example="nerds", max_length=20)
    description: str = Field("", example="A room for nerds", max_length=60)


class RoomCreateResult(BaseModel):

    room_name: str
    members: list[str]
    conversation: list[str]
    active: str
    creation_date: datetime.datetime


class RoomGetALL(BaseModel):

    room_name: str
    members: list[dict[str, Union[str, datetime.datetime]]]
    messages: list[dict[str, Union[str, datetime.datetime]]]
    active: str
    creation_date: datetime.datetime


class LeaveRoom(BaseModel):

    room_name: str = Field(..., example="A room name to leave.")


class DeleteRoomConversation(BaseModel):

    room_name: str = Field(..., example="A room name to delete messages.")


class BanUserRoom(BaseModel):

    room_name: str = Field(..., example="A room name.")
    email: EmailStr = Field(..., example="A user email to ban.")


class InviteRoomLink(BaseModel):

    room_name: str = Field(..., example="A room name.")
    invite_link: str = Field(..., example="An absolute URL to join the room.")


# ============= E2E Encryption Schemas =============

class RoomKeyRequest(BaseModel):

    room_name: str = Field(..., example="general-chat")


class RoomKeyUpdate(BaseModel):

    room_name: str = Field(..., example="general-chat")
    encrypted_room_key: str = Field(..., example="Base64 encoded encrypted room key")


class RoomKeyDistribute(BaseModel):
    room_name: str = Field(..., example="general-chat")
    target_user_id: int = Field(..., example=123)
    encrypted_room_key: str = Field(..., example="Base64 encoded encrypted room key")