import os
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.responses import (
    FileResponse,
)
from pathlib import Path
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.auth.schemas import (
    ResponseSchema,
)
from app.chats.schemas import (
    MessageCreateRoom,
)
from app.rooms.crud import (
    ban_user_from_room,
    create_assign_new_room,
    create_invite_link,
    delete_room_user_chat,
    get_room_conversations,
    get_rooms_user,
    invite_user_to_room,
    leave_room_user,
    search_rooms,
    send_new_room_message,
    get_room_encrypted_key,
    set_room_encrypted_key,
    get_room_members_for_key_distribution,
    distribute_room_key_to_member,
)
from app.rooms.schemas import (
    BanUserRoom,
    DeleteRoomConversation,
    InviteRoomLink,
    LeaveRoom,
    RoomCreate,
    RoomKeyRequest,
    RoomKeyUpdate,
    RoomKeyDistribute,
)
from app.users.schemas import (
    UserObjectSchema,
)
from app.utils.dependencies import (
    get_db_autocommit_session,
    get_db_transactional_session,
)
from app.utils.jwt_util import (
    get_current_active_user,
)


UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
SENT_IMAGES_DIR = UPLOAD_DIR / "sent-images"


SENT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/api/v1")


@router.post(
    "/room",
    status_code=200,
    name="room:create-join",
    responses={
        200: {
            "model": ResponseSchema,
            "description": "Return a message that indicates a user has joined the room.",
        },
        400: {
            "model": ResponseSchema,
            "description": "Return a message that indicates if a user has already joined a room.",
        },
    },
)
async def create_room(
    room: RoomCreate,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    results = await create_assign_new_room(currentUser.id, room, session)
    return results


@router.get("/room/conversation", name="room:get-conversations")
async def get_room_users_conversation(
    room: str,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_transactional_session),
):

    results = await get_room_conversations(room, currentUser.id, session)
    return results


@router.post("/room/message", name="room:send-text-message")
async def send_room_message(
    request: MessageCreateRoom,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    results = await send_new_room_message(
        currentUser.id, request, None, session
    )
    return results


@router.delete(
    "/room",
    status_code=200,
    name="room:leave-room",
    responses={
        200: {
            "model": ResponseSchema,
            "description": "Return a message that indicates a user left the room.",
        },
        400: {
            "model": ResponseSchema,
            "description": "Return a message that indicates if a user has not joined a room.",
        },
    },
)
async def leave_room(
    room: LeaveRoom,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):
    """
    Leave a room.
    """
    results = await leave_room_user(currentUser.id, room.room_name, session)
    return results


@router.delete(
    "/room/chat",
    status_code=200,
    name="room:delete-room-chat",
    responses={
        200: {
            "model": ResponseSchema,
            "description": "Return a message that indicates a user has successfully deleted their messages.",
        },
        400: {
            "model": ResponseSchema,
            "description": "Return a message that indicates if a user can't delete messages already deleted.",
        },
    },
)
async def delete_room_chat(
    room_name: DeleteRoomConversation,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    results = await delete_room_user_chat(
        currentUser.id, room_name.room_name, session
    )
    return results


@router.get("/rooms/search", status_code=200, name="rooms:search-for-room")
async def search_for_room(
    search: str,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    results = await search_rooms(search, currentUser.id, session)
    return results


@router.get("/rooms", status_code=200, name="rooms:get-rooms-for-user")
async def get_rooms_for_user(
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    results = await get_rooms_user(currentUser.id, session)
    return results


@router.get("/chat/images/room/{room_id}/{uuid_val}")
async def get_sent_room_chat_images(room_id: int, uuid_val: str):

    try:
        file_path = SENT_IMAGES_DIR / "chat" / "images" / "room" / str(room_id) / uuid_val
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        return FileResponse(
            path=str(file_path),
            media_type="image/png",
            filename=uuid_val
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        return {"status_code": 400, "message": "Something went wrong!"}


@router.delete(
    "/room/user/delete",
    status_code=200,
    name="room:ban-user-room",
    responses={
        200: {
            "model": ResponseSchema,
            "description": "Return a message that indicates a user has been banned from this room.",
        },
        400: {
            "model": ResponseSchema,
            "description": "Return a message that indicates if a user doesn't exist or not a member of this room.",
        },
    },
)
async def ban_a_user_from_a_room(
    room: BanUserRoom,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    results = await ban_user_from_room(
        currentUser.id, room.email, room.room_name, session
    )
    return results


@router.post(
    "/room/user/invite",
    status_code=200,
    name="room:invite-user-room",
    responses={
        200: {
            "model": ResponseSchema,
            "description": "Return a message that indicates a user has joined the room.",
        },
        400: {
            "model": ResponseSchema,
            "description": "Return a message that indicates if a user doesn't exist.",
        },
    },
)
async def invite_a_user_to_a_room(
    room: InviteRoomLink,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    results = await invite_user_to_room(
        currentUser.email, room.room_name, room.invite_link, session
    )
    return results


@router.post(
    "/room/invite/link",
    status_code=200,
    name="room:create-invite-link",
    responses={
        200: {
            "model": ResponseSchema,
            "description": "Return a message that indicates a link has been saved in the room.",
        },
        400: {
            "model": ResponseSchema,
            "description": "Return a message that indicates if something went wrong.",
        },
    },
)
async def create_an_invite_link(
    room: InviteRoomLink,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):


    results = await create_invite_link(
        room.room_name, room.invite_link, session
    )
    return results


def save_room_chat_image(room_id: int, uuid_val: str, file_content: bytes) -> str:

    room_dir = SENT_IMAGES_DIR / "chat" / "images" / "room" / str(room_id)
    room_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = room_dir / uuid_val
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return f"/chat/images/room/{room_id}/{uuid_val}"




@router.get(
    "/room/encryption/key",
    status_code=200,
    name="room:get-room-key",
    responses={
        200: {
            "description": "Returns the encrypted room key for the current user",
        },
        400: {
            "model": ResponseSchema,
            "description": "Room not found or user is not a member",
        },
    },
)
async def get_room_key(
    room_name: str,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_transactional_session),
):

    results = await get_room_encrypted_key(currentUser.id, room_name, session)
    return results


@router.put(
    "/room/encryption/key",
    status_code=200,
    name="room:set-room-key",
    responses={
        200: {
            "model": ResponseSchema,
            "description": "Room key updated successfully",
        },
        400: {
            "model": ResponseSchema,
            "description": "Room not found or user is not a member",
        },
    },
)
async def update_room_key(
    request: RoomKeyUpdate,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    results = await set_room_encrypted_key(
        currentUser.id, 
        request.room_name, 
        request.encrypted_room_key, 
        currentUser.id,  # Self is the key provider
        session
    )
    return results


@router.get(
    "/room/encryption/members",
    status_code=200,
    name="room:get-members-for-key-distribution",
    responses={
        200: {
            "description": "Returns list of room members with their public keys",
        },
        400: {
            "model": ResponseSchema,
            "description": "Room not found",
        },
    },
)
async def get_members_for_key_distribution(
    room_name: str,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_transactional_session),
):

    results = await get_room_members_for_key_distribution(room_name, session)
    return results


@router.post(
    "/room/encryption/distribute",
    status_code=200,
    name="room:distribute-room-key",
    responses={
        200: {
            "model": ResponseSchema,
            "description": "Room key distributed successfully",
        },
        400: {
            "model": ResponseSchema,
            "description": "Distribution failed",
        },
    },
)
async def distribute_key_to_member(
    request: RoomKeyDistribute,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    results = await distribute_room_key_to_member(
        currentUser.id,
        request.room_name,
        request.target_user_id,
        request.encrypted_room_key,
        session
    )
    return results