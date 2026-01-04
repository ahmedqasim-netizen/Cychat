import mimetypes
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
from pydantic import (
    EmailStr,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)
from typing import (
    Union,
)

from app.auth.schemas import (
    ResponseSchema,
)
from app.chats.crud import (
    delete_chat_messages,
    get_chats_user,
    get_sender_receiver_messages,
    send_new_message,
)
from app.chats.schemas import (
    DeleteChatMessages,
    GetAllMessageResults,
    MessageCreate,
)
from app.users.schemas import (
    UserObjectSchema,
)
from app.utils.dependencies import (
    get_db_autocommit_session,
)
from app.utils.jwt_util import (
    get_current_active_user,
)


UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
SENT_FILES_DIR = UPLOAD_DIR / "sent-files"
SENT_IMAGES_DIR = UPLOAD_DIR / "sent-images"  


SENT_FILES_DIR.mkdir(parents=True, exist_ok=True)
SENT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


MIME_TYPES = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.bmp': 'image/bmp',
    '.svg': 'image/svg+xml',
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xls': 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.ppt': 'application/vnd.ms-powerpoint',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.txt': 'text/plain',
    '.rtf': 'application/rtf',
    '.odt': 'application/vnd.oasis.opendocument.text',
    '.mp4': 'video/mp4',
    '.avi': 'video/x-msvideo',
    '.mov': 'video/quicktime',
    '.wmv': 'video/x-ms-wmv',
    '.flv': 'video/x-flv',
    '.webm': 'video/webm',
    '.mkv': 'video/x-matroska',
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.ogg': 'audio/ogg',
    '.flac': 'audio/flac',
    '.aac': 'audio/aac',
    '.m4a': 'audio/mp4',
    '.zip': 'application/zip',
    '.rar': 'application/vnd.rar',
    '.7z': 'application/x-7z-compressed',
    '.tar': 'application/x-tar',
    '.gz': 'application/gzip',
    '.py': 'text/x-python',
    '.js': 'text/javascript',
    '.ts': 'text/typescript',
    '.html': 'text/html',
    '.css': 'text/css',
    '.json': 'application/json',
    '.xml': 'application/xml',
    '.yaml': 'text/yaml',
    '.yml': 'text/yaml',
    '.md': 'text/markdown',
}


def get_mime_type(filename: str) -> str:

    ext = Path(filename).suffix.lower()
    if ext in MIME_TYPES:
        return MIME_TYPES[ext]

    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'

router = APIRouter(prefix="/api/v1")


@router.post(
    "/message",
    response_model=ResponseSchema,
    status_code=201,
    name="chats:send-message",
    responses={
        201: {
            "model": ResponseSchema,
            "description": "Message has been delivered successfully!",
        },
        401: {
            "model": ResponseSchema,
            "description": "Empty message, non existing receiver!",
        },
    },
)
async def send_message(
    request: MessageCreate,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):
    results = await send_new_message(
        currentUser.id, request, None, None, session
    )
    return results


@router.get(
    "/conversation",
    response_model=Union[ResponseSchema, GetAllMessageResults],
    status_code=200,
    name="chats:get-all-conversations",
    responses={
        200: {
            "model": GetAllMessageResults,
            "description": "Return a list of messages between two parties.",
        },
    },
)
async def get_conversation(
    receiver: EmailStr,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    results = await get_sender_receiver_messages(
        currentUser, receiver, session
    )
    return results


@router.get(
    "/contacts/chat/search",
    status_code=200,
    name="chats:get-user-chat-list",
)
async def get_chats_user_list(
    search: str,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    results = await get_chats_user(currentUser.id, search, session)
    return results


@router.get(
    "/contacts/chat/search/{search}",
    status_code=200,
    name="chats:get-user-chat-list-path",
)
async def get_chats_user_search_list(
    search: str,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    results = await get_chats_user(currentUser.id, search, session)
    return results


@router.delete(
    "/user/chat",
    status_code=200,
    name="room:delete-room-chat",
    responses={
        200: {
            "model": ResponseSchema,
            "description": "Return a message that indicates a user"
            " has successfully deleted their messages.",
        },
        400: {
            "model": ResponseSchema,
            "description": "Return a message that indicates if a user"
            " can't delete messages already deleted.",
        },
    },
)
async def delete_user_chat(
    contact: DeleteChatMessages,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):
    """
    The delete_user_chat endpoint.
    """
    results = await delete_chat_messages(
        currentUser.id, contact.contact, session
    )
    return results


@router.get("/chat/files/user/{user_id}/{filename}")
async def get_sent_user_chat_file(user_id: int, filename: str):

    try:
        file_path = SENT_FILES_DIR / "chat" / "files" / "user" / str(user_id) / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        mime_type = get_mime_type(filename)
        
        return FileResponse(
            path=str(file_path),
            media_type=mime_type,
            filename=filename
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        return {"status_code": 400, "message": "Something went wrong!"}


@router.get("/chat/images/user/{user_id}/{uuid_val}")
async def get_sent_user_chat_images(user_id: int, uuid_val: str):

    try:

        file_path = SENT_FILES_DIR / "chat" / "files" / "user" / str(user_id) / uuid_val
        if not file_path.exists():

            file_path = SENT_IMAGES_DIR / "chat" / "images" / "user" / str(user_id) / uuid_val
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        mime_type = get_mime_type(uuid_val)
        
        return FileResponse(
            path=str(file_path),
            media_type=mime_type,
            filename=uuid_val
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        return {"status_code": 400, "message": "Something went wrong!"}