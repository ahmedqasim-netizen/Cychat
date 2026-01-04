import datetime
import logging
from pydantic import (
    EmailStr,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)
from sqlalchemy.sql import (
    text,
)
from typing import (
    Any,
)

from app.auth.crud import (
    find_existed_user,
)
from app.chats import (
    crud as chats_crud,
)
from app.chats.schemas import (
    MessageCreateRoom,
)

logger = logging.getLogger(__name__)


async def find_existed_room(room_name: str, session: AsyncSession):

    query = "SELECT * FROM chat.rooms WHERE room_name = :room_name"
    values = {"room_name": room_name}
    result = await session.execute(text(query), values)
    return result.fetchone()


async def find_existed_user_in_room(
    user_id: int, room_id: int, session: AsyncSession
):

    query = """
        SELECT * FROM chat.room_members
        WHERE room = :room_id AND member = :user_id
    """
    values = {"room_id": room_id, "user_id": user_id}
    result = await session.execute(text(query), values)
    return result.fetchone()


async def find_admin_in_room(
    user_id: int, room_id: int, session: AsyncSession
):

    return await find_existed_user_in_room(user_id, room_id, session)


async def create_room(room_name: str, description: str, session: AsyncSession):

    query = """
        INSERT INTO chat.rooms (room_name, description, creation_date, modified_date)
        VALUES (:room_name, :description, :creation_date, :modified_date)
    """
    now = datetime.datetime.utcnow()
    values = {
        "room_name": room_name,
        "description": description,
        "creation_date": now,
        "modified_date": now,
    }
    return await session.execute(text(query), values)


async def join_room(
    user_id: int, room_id: int, session: AsyncSession, is_admin: bool = False
):

    query = """
        INSERT INTO chat.room_members (room, member, creation_date, modified_date)
        VALUES (:room, :member, :creation_date, :modified_date)
    """
    now = datetime.datetime.utcnow()
    values = {
        "room": room_id,
        "member": user_id,
        "creation_date": now,
        "modified_date": now,
    }
    return await session.execute(text(query), values)


async def delete_room_user(user_id: int, room_id: int, session: AsyncSession):

    query = "DELETE FROM chat.room_members WHERE room = :room AND member = :member"
    values = {"room": room_id, "member": user_id}
    return await session.execute(text(query), values)


async def ban_room_user(user_id: int, room_id: int, session: AsyncSession):

    return await delete_room_user(user_id, room_id, session)


async def unban_room_user(user_id: int, room_id: int, session: AsyncSession):

    pass


async def update_room_invite_link(
    room_name: str, invite_link: str, session: AsyncSession
):

    logger.warning("invite_link column not in current schema")
    return None


async def create_assign_new_room(
    user_id: int, room_obj, session: AsyncSession
) -> dict[str, Any]:
    room_obj.room_name = room_obj.room_name.lower()
    if not room_obj.room_name:
        return {"status_code": 400, "message": "Make sure the room name is not empty!"}

    room = await find_existed_room(room_obj.room_name, session)
    
    if not room:
        if room_obj.join == 0:
            await create_room(room_obj.room_name, room_obj.description, session)
            logger.info(f"Creating room `{room_obj.room_name}`.")
            room = await find_existed_room(room_obj.room_name, session)
            await join_room(user_id, room.id, session, True)
            return {"status_code": 200, "message": f"You have joined room {room_obj.room_name}!"}
        else:
            return {"status_code": 400, "message": "Room not found!"}
    else:
        user = await find_existed_user_in_room(user_id, room.id, session)
        if user and room_obj.join == 1:
            return {"status_code": 400, "message": f"You have already joined room {room_obj.room_name}!"}
        elif not user and room_obj.join == 1:
            await join_room(user_id, room.id, session)
            return {"status_code": 200, "message": f"You have joined room {room_obj.room_name}!"}
        else:
            return {"status_code": 400, "message": "This room already exists. Join it, perhaps?"}


async def get_room_conversations(
    room_name: str, sender_id: int, session: AsyncSession
) -> dict[str, Any]:
    room = await find_existed_room(room_name, session)
    if not room:
        return {"status_code": 400, "message": "Room not found!"}

    user = await find_existed_user_in_room(sender_id, room.id, session)
    if not user:
        return {"status_code": 400, "message": "You are not a member of this room!"}

    # Added message_type to support E2E decryption on frontend
    query = """
        SELECT
            m.id AS msg_id,
            m.content,
            IIF(m.sender = :sender_id, 'sent', 'received') AS type,
            m.message_type,
            m.media,
            m.creation_date,
            u.id,
            u.nickname,
            u.email,
            u.phone_number
        FROM chat.messages m
        LEFT JOIN chat.users u ON m.sender = u.id
        WHERE m.room = :room_name
        ORDER BY m.creation_date ASC
    """
    values = {"room_name": room.room_name, "sender_id": sender_id}
    result = await session.execute(text(query), values)
    messages = result.fetchall()
    return {"status_code": 200, "result": [dict(row._mapping) for row in messages]}


async def send_new_room_message(
    sender_id: int,
    request: MessageCreateRoom,
    bin_photo: bytes,
    session: AsyncSession,
) -> dict[str, Any]:
    if not request.content and not bin_photo:
        return {"status_code": 400, "message": "You can't send an empty message!"}

    room = await find_existed_room(request.room, session)
    if not room:
        return {"status_code": 400, "message": "Room not found!"}

    user = await find_existed_user_in_room(sender_id, room.id, session)
    if not user:
        return {"status_code": 400, "message": "You can't send a message to a room you have not joined yet."}


    results = await chats_crud.send_new_message(
        sender_id, request, bin_photo, room.id, session
    )
    return results


async def leave_room_user(user_id: int, room_name: str, session: AsyncSession) -> dict[str, Any]:
    if not room_name:
        return {"status_code": 400, "message": "Make sure the room name is not empty!"}

    room = await find_existed_room(room_name, session)
    if not room:
        return {"status_code": 400, "message": "You can't leave a non existing room"}

    user = await find_existed_user_in_room(user_id, room.id, session)
    if user:
        await delete_room_user(user_id, room.id, session)
        return {"status_code": 200, "message": f"You have left room {room_name}!"}
    else:
        return {"status_code": 200, "message": f"You are not a member of room {room_name}!"}


async def delete_room_user_chat(
    user_id: int, room_name: str, session: AsyncSession
) -> dict[str, Any]:
    if not room_name:
        return {"status_code": 400, "message": "Make sure the room name is not empty!"}

    room = await find_existed_room(room_name, session)
    if not room:
        return {"status_code": 400, "message": "You can't delete messages in a non existing room!"}

    user = await find_existed_user_in_room(user_id, room.id, session)
    if user:
        results = await chats_crud.delete_room_messages(user_id, room.id, session)
        return results
    else:
        return {"status_code": 200, "message": f"You are not a member of room {room_name}!"}


async def search_rooms(search: str, user_id: int, session: AsyncSession) -> dict[str, Any]:
    if not search:
        query = """
            SELECT rm.*, r.*
            FROM chat.room_members rm
            LEFT JOIN chat.rooms r ON rm.room = r.id
            WHERE rm.member = :user_id
        """
        values = {"user_id": user_id}
    else:
        query = """
            SELECT rm.*, r.*
            FROM chat.room_members rm
            LEFT JOIN chat.rooms r ON rm.room = r.id
            WHERE rm.member = :user_id AND r.room_name LIKE :search
        """
        values = {"user_id": user_id, "search": f"%{search.lower()}%"}

    result = await session.execute(text(query), values)
    rooms = result.fetchall()
    return {"status_code": 200, "result": [dict(row._mapping) for row in rooms]}


async def get_rooms_user(user_id: int, session: AsyncSession) -> dict[str, Any]:
    query = """
        SELECT rm.*, r.*
        FROM chat.room_members rm
        LEFT JOIN chat.rooms r ON rm.room = r.id
        WHERE rm.member = :user_id
    """
    values = {"user_id": user_id}
    result = await session.execute(text(query), values)
    rooms = result.fetchall()
    return {"status_code": 200, "result": [dict(row._mapping) for row in rooms]}


async def ban_user_from_room(
    admin_id: int, user_email: EmailStr, room_name: str, session: AsyncSession
) -> dict[str, Any]:
    room_name = room_name.lower()
    if not room_name:
        return {"status_code": 400, "message": "Make sure the room name is not empty!"}

    room_obj = await find_existed_room(room_name, session)
    if not room_obj:
        return {"status_code": 400, "message": "Room doesn't exist!"}

    admin = await find_admin_in_room(admin_id, room_obj.id, session)
    if not admin:
        return {"status_code": 400, "message": "You are not a member of this room!"}

    user_profile = await find_existed_user(user_email, session)
    if not user_profile:
        return {"status_code": 400, "message": "User not found!"}

    room = await find_existed_user_in_room(user_profile["id"], room_obj.id, session)
    if not room:
        return {"status_code": 400, "message": f"{user_profile['nickname']} is not a member of this room."}
    elif room.member == admin_id:
        return {"status_code": 400, "message": "You can't ban yourself!"}
    else:
        await delete_room_user_chat(room.member, room_name, session)
        await ban_room_user(room.member, room_obj.id, session)
        return {"status_code": 200, "message": f"{user_profile['nickname']} has been banned from this room."}


async def invite_user_to_room(
    user_email: EmailStr,
    room_name: str,
    invite_link: str,
    session: AsyncSession,
) -> dict[str, Any]:
    room_name = room_name.lower()
    if not room_name:
        return {"status_code": 400, "message": "Make sure the room name is not empty!"}

    room_obj = await find_existed_room(room_name, session)
    if not room_obj:
        return {"status_code": 400, "message": "Room doesn't exist!"}

    user_profile = await find_existed_user(user_email, session)
    if not user_profile:
        return {"status_code": 400, "message": "User not registered!"}

    room = await find_existed_user_in_room(user_profile["id"], room_obj.id, session)
    if not room:
        await join_room(user_profile["id"], room_obj.id, session)
        return {"status_code": 200, "message": f"User has joined room {room_obj.room_name}!"}
    else:
        return {"status_code": 400, "message": f"User has already joined room {room_name}!"}




async def get_room_encrypted_key(
    user_id: int, room_name: str, session: AsyncSession
) -> dict[str, Any]:

    room = await find_existed_room(room_name, session)
    if not room:
        return {"status_code": 400, "message": "Room not found!"}

    membership = await find_existed_user_in_room(user_id, room.id, session)
    if not membership:
        return {"status_code": 400, "message": "You are not a member of this room!"}

    query = """
        SELECT rm.encrypted_room_key, rm.key_provider, u.public_key as provider_public_key
        FROM chat.room_members rm
        LEFT JOIN chat.users u ON rm.key_provider = u.id
        WHERE rm.room = :room_id AND rm.member = :user_id
    """
    values = {"room_id": room.id, "user_id": user_id}
    result = await session.execute(text(query), values)
    row = result.fetchone()
    
    if row and row.encrypted_room_key:
        return {
            "status_code": 200,
            "encrypted_room_key": row.encrypted_room_key,
            "key_provider_id": row.key_provider,
            "key_provider_public_key": row.provider_public_key
        }
    else:
        return {
            "status_code": 200,
            "encrypted_room_key": None,
            "message": "No room key available yet"
        }


async def set_room_encrypted_key(
    user_id: int, room_name: str, encrypted_key: str, key_provider_id: int, session: AsyncSession
) -> dict[str, Any]:
    room = await find_existed_room(room_name, session)
    if not room:
        return {"status_code": 400, "message": "Room not found!"}

    membership = await find_existed_user_in_room(user_id, room.id, session)
    if not membership:
        return {"status_code": 400, "message": "User is not a member of this room!"}

    query = """
        UPDATE chat.room_members
        SET encrypted_room_key = :encrypted_key, 
            key_provider = :key_provider_id,
            modified_date = :modified_date
        WHERE room = :room_id AND member = :user_id
    """
    now = datetime.datetime.utcnow()
    values = {
        "encrypted_key": encrypted_key,
        "key_provider_id": key_provider_id,
        "room_id": room.id,
        "user_id": user_id,
        "modified_date": now
    }
    await session.execute(text(query), values)
    return {"status_code": 200, "message": "Room key updated successfully"}


async def get_room_members_for_key_distribution(
    room_name: str, session: AsyncSession
) -> dict[str, Any]:
    """Get all room members with their public keys for key distribution."""
    room = await find_existed_room(room_name, session)
    if not room:
        return {"status_code": 400, "message": "Room not found!"}

    query = """
        SELECT rm.member, u.nickname, u.email, u.public_key, rm.encrypted_room_key
        FROM chat.room_members rm
        LEFT JOIN chat.users u ON rm.member = u.id
        WHERE rm.room = :room_id
    """
    values = {"room_id": room.id}
    result = await session.execute(text(query), values)
    members = result.fetchall()
    
    return {
        "status_code": 200,
        "room_id": room.id,
        "room_name": room.room_name,
        "members": [
            {
                "id": m.member,
                "nickname": m.nickname,
                "email": m.email,
                "public_key": m.public_key,
                "has_room_key": m.encrypted_room_key is not None
            }
            for m in members
        ]
    }


async def distribute_room_key_to_member(
    provider_id: int,
    room_name: str,
    target_user_id: int,
    encrypted_key: str,
    session: AsyncSession
) -> dict[str, Any]:
    room = await find_existed_room(room_name, session)
    if not room:
        return {"status_code": 400, "message": "Room not found!"}


    provider_membership = await find_existed_user_in_room(provider_id, room.id, session)
    if not provider_membership:
        return {"status_code": 400, "message": "You are not a member of this room!"}


    target_membership = await find_existed_user_in_room(target_user_id, room.id, session)
    if not target_membership:
        return {"status_code": 400, "message": "Target user is not a member of this room!"}

    return await set_room_encrypted_key(target_user_id, room_name, encrypted_key, provider_id, session)


async def create_invite_link(
    room_name: str, invite_link: str, session: AsyncSession
) -> dict[str, Any]:

    room_name = room_name.lower()
    if not room_name:
        return {"status_code": 400, "message": "Make sure the room name is not empty!"}
    if not invite_link:
        return {"status_code": 400, "message": "Make sure the invite link is not empty!"}

    room_obj = await find_existed_room(room_name, session)
    if not room_obj:
        return {"status_code": 400, "message": "Room doesn't exist!"}


    logger.warning("invite_link functionality requires schema extension")
    return {"status_code": 200, "message": "Room link feature requires schema extension."}


async def unban_user_from_room(
    admin_id: int, user_email: EmailStr, room_name: str, session: AsyncSession
) -> dict[str, Any]:

    room_name = room_name.lower()
    if not room_name:
        return {"status_code": 400, "message": "Make sure the room name is not empty!"}

    room_obj = await find_existed_room(room_name, session)
    if not room_obj:
        return {"status_code": 400, "message": "Room doesn't exist!"}

    admin = await find_admin_in_room(admin_id, room_obj.id, session)
    if not admin:
        return {"status_code": 400, "message": "You are not a member of this room!"}

    user_profile = await find_existed_user(user_email, session)
    if not user_profile:
        return {"status_code": 400, "message": "User not found!"}


    room = await find_existed_user_in_room(user_profile["id"], room_obj.id, session)
    if room:
        return {"status_code": 400, "message": f"{user_profile['nickname']} is already a member of this room."}
    
    await join_room(user_profile["id"], room_obj.id, session)
    return {"status_code": 200, "message": f"{user_profile['nickname']} has been unbanned from this room."}