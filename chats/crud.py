import datetime
import logging
import os
import uuid
from pathlib import Path
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)
from sqlalchemy.sql import (
    text,
)
from typing import (
    Any,
    Union,
)

from app.auth.crud import (
    find_existed_user,
)
from app.chats.schemas import (
    MessageCreate,
    MessageCreateRoom,
)

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
SENT_FILES_DIR = UPLOAD_DIR / "sent-files"


SENT_FILES_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'}
DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'}
ARCHIVE_EXTENSIONS = {'.zip', '.rar', '.7z', '.tar', '.gz'}
CODE_EXTENSIONS = {'.py', '.js', '.ts', '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.md'}

ALL_ALLOWED_EXTENSIONS = (
    IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS | VIDEO_EXTENSIONS | 
    AUDIO_EXTENSIONS | ARCHIVE_EXTENSIONS | CODE_EXTENSIONS
)


def get_file_category(extension: str) -> str:
    ext = extension.lower()
    if ext in IMAGE_EXTENSIONS:
        return "image"
    elif ext in DOCUMENT_EXTENSIONS:
        return "document"
    elif ext in VIDEO_EXTENSIONS:
        return "video"
    elif ext in AUDIO_EXTENSIONS:
        return "audio"
    elif ext in ARCHIVE_EXTENSIONS:
        return "archive"
    elif ext in CODE_EXTENSIONS:
        return "code"
    else:
        return "file"


def save_chat_file(user_id: int, file_content: bytes, original_filename: str = None) -> dict:
    if original_filename:
        ext = Path(original_filename).suffix.lower()
        if not ext:
            ext = '.bin'
    else:
        ext = '.png'  
    

    uuid_val = f"{uuid.uuid4()}{ext}"
    
    user_dir = SENT_FILES_DIR / "chat" / "files" / "user" / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    

    file_path = user_dir / uuid_val
    with open(file_path, "wb") as f:
        f.write(file_content)
    

    file_size = len(file_content)
    category = get_file_category(ext)
    

    return {
        "url": f"/api/v1/chat/files/user/{user_id}/{uuid_val}",
        "filename": original_filename or uuid_val,
        "extension": ext,
        "category": category,
        "size": file_size
    }


async def send_new_message(
    sender_id: int,
    request: Union[MessageCreate, MessageCreateRoom, Any],
    bin_photo: bytes,
    room_id: int,
    session: AsyncSession,
) -> Union[dict[str, Any], str]:

    if not request.content and not bin_photo:
        return {
            "status_code": 400,
            "message": "You can't send an empty message!",
        }


    if hasattr(request, 'receiver') and request.receiver:
        receiver = await find_existed_user(request.receiver, session)
        if not receiver:
            return {
                "status_code": 400,
                "message": "Receiver not found!",
            }
        receiver_id = receiver["id"]
        room_value = None
    else:

        receiver_id = sender_id
        room_value = request.room if hasattr(request, 'room') else None


    media_url = ""
    file_info = None
    if bin_photo:
        try:

            original_filename = None
            if hasattr(request, 'filename') and request.filename:
                original_filename = request.filename
            
            file_info = save_chat_file(sender_id, bin_photo, original_filename)
            media_url = file_info["url"]
            logger.info(f"File saved: {media_url} (category: {file_info['category']}, size: {file_info['size']})")
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return {
                "status_code": 500,
                "message": "Failed to save file!",
            }
    elif hasattr(request, 'media') and request.media:
        media_url = request.media

    query = """
        INSERT INTO chat.messages (
            sender,
            receiver,
            content,
            message_type,
            status,
            room,
            media,
            creation_date,
            modified_date
        )
        VALUES (
            :sender,
            :receiver,
            :content,
            :message_type,
            0,
            :room,
            :media,
            :creation_date,
            :modified_date
        )
    """
    now = datetime.datetime.utcnow()
    values = {
        "sender": sender_id,
        "receiver": receiver_id,
        "content": request.content,
        "message_type": request.message_type,
        "room": room_value,
        "media": media_url,
        "creation_date": now,
        "modified_date": now,
    }

    await session.execute(text(query), values)
    logger.info(f"Message sent from {sender_id} to {receiver_id}")

    if file_info:
        return file_info
    
    return {
        "status_code": 201,
        "message": "Message has been delivered successfully!",
    }


async def get_sender_receiver_messages(
    currentUser: Any, receiver_email: EmailStr, session: AsyncSession
) -> dict[str, Any]:

    receiver = await find_existed_user(receiver_email, session)
    if not receiver:
        return {
            "status_code": 400,
            "message": "User not found!",
        }


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
        FROM
            chat.messages m
        LEFT JOIN
            chat.users u
        ON
            m.sender = u.id
        WHERE
            (m.sender = :sender_id AND m.receiver = :receiver_id)
            OR
            (m.sender = :receiver_id AND m.receiver = :sender_id)
        ORDER BY
            m.creation_date ASC
    """

    sender_id = currentUser["id"] if isinstance(currentUser, dict) else currentUser.id
    values = {
        "sender_id": sender_id,
        "receiver_id": receiver["id"],
    }

    result = await session.execute(text(query), values)
    messages = result.fetchall()

    return {
        "status_code": 200,
        "result": [dict(row._mapping) for row in messages],
    }


async def get_chats_user(
    user_id: int, search: str, session: AsyncSession
) -> dict[str, Any]:

    if not search or len(search) == 0:

        query = """
            SELECT DISTINCT
                u.id,
                u.nickname,
                u.email,
                u.phone_number,
                u.user_role
            FROM
                chat.users u
            WHERE
                u.id IN (
                    SELECT DISTINCT receiver FROM chat.messages WHERE sender = :user_id
                    UNION
                    SELECT DISTINCT sender FROM chat.messages WHERE receiver = :user_id
                )
        """
        values = {"user_id": user_id}
    else:
        
        query = """
            SELECT DISTINCT
                u.id,
                u.nickname,
                u.email,
                u.phone_number,
                u.user_role
            FROM
                chat.users u
            WHERE
                u.id IN (
                    SELECT DISTINCT receiver FROM chat.messages WHERE sender = :user_id
                    UNION
                    SELECT DISTINCT sender FROM chat.messages WHERE receiver = :user_id
                )
                AND (
                    u.nickname LIKE :search
                    OR u.email LIKE :search
                )
        """
        values = {"user_id": user_id, "search": f"%{search}%"}

    result = await session.execute(text(query), values)
    contacts = result.fetchall()

    return {
        "status_code": 200,
        "result": [dict(row._mapping) for row in contacts],
    }


async def delete_chat_messages(
    user_id: int, contact_email: EmailStr, session: AsyncSession
) -> dict[str, Any]:

    contact = await find_existed_user(contact_email, session)
    if not contact:
        return {
            "status_code": 400,
            "message": "Contact not found!",
        }


    query = """
        DELETE FROM chat.messages
        WHERE sender = :user_id AND receiver = :contact_id
    """
    values = {"user_id": user_id, "contact_id": contact["id"]}
    await session.execute(text(query), values)

    logger.info(f"Deleted messages from user {user_id} to contact {contact['id']}")

    return {
        "status_code": 200,
        "message": "Messages have been deleted successfully!",
    }


async def delete_room_messages(
    user_id: int, room_id: int, session: AsyncSession
) -> dict[str, Any]:

    query = """
        DELETE FROM chat.messages
        WHERE sender = :user_id AND room = :room_id
    """
    values = {"user_id": user_id, "room_id": str(room_id)}
    await session.execute(text(query), values)

    logger.info(f"Deleted messages from user {user_id} in room {room_id}")

    return {
        "status_code": 200,
        "message": "Your messages have been deleted from this room!",
    }


async def mark_messages_as_read(
    sender_id: int, receiver_id: int, session: AsyncSession
) -> None:

    query = """
        UPDATE chat.messages
        SET status = 1, modified_date = :modified_date
        WHERE sender = :sender_id AND receiver = :receiver_id AND status = 0
    """
    values = {
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "modified_date": datetime.datetime.utcnow(),
    }
    await session.execute(text(query), values)