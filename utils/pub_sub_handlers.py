from asyncio import (
    ensure_future,
)
from typing import Union
import base64
from fastapi.websockets import (
    WebSocket,
)
import json
import logging
import openai
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)
from starlette.websockets import (
    WebSocketState,
)
from typing import (
    NamedTuple,
    Optional,
)

from app.auth.crud import (
    find_existed_user_id,
)
from app.chats.crud import (
    send_new_message,
)
from app.rooms.crud import (
    ban_user_from_room,
    find_admin_in_room,
    find_existed_room,
    send_new_room_message,
    unban_user_from_room,
)
from app.users.crud import (
    update_chat_status,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RequestRoomObject(NamedTuple):
    room: str
    content: str
    message_type: str
    media: str
    filename: str = ""  


class RequestContactObject(NamedTuple):
    receiver: str
    content: str
    message_type: str
    media: str
    filename: str = ""  


def get_user_display_name(user) -> str:

    if isinstance(user, dict):
        return user.get('nickname') or user.get('first_name') or "User"
    if hasattr(user, 'nickname') and user.nickname:
        return user.nickname
    if hasattr(user, 'first_name') and user.first_name:
        return user.first_name
    return "User"


def user_to_dict(user) -> dict:

    if isinstance(user, dict):
        return user
    if hasattr(user, '_asdict'):
        return user._asdict()
    if hasattr(user, '__dict__'):
        return {k: v for k, v in user.__dict__.items() if not k.startswith('_')}
    if hasattr(user, 'dict'):
        return user.dict()
    return dict(user)


async def consumer_handler(
    connection,  
    topic: str,
    web_socket: WebSocket,
    sender_id: int,
    receiver_id: Optional[int],
    session: AsyncSession,
) -> None:
    try:
        user = await find_existed_user_id(sender_id, session)
        room = None
        admin = None
        

        display_name = get_user_display_name(user)
        user_dict = user_to_dict(user)
        
        if receiver_id:
            data = {
                "content": f"{display_name} is online!",
                "type": "online",
                "user": user_dict,
            }
        else:
            room = await find_existed_room(topic, session)
            admin = await find_admin_in_room(sender_id, room.id, session)
            data = {
                "content": f"{display_name} is online!",
                "room_name": topic,
                "type": "online",
                "user": user_dict,
            }
        await update_chat_status("online", user, session)
        await connection.publish(topic, json.dumps(data, default=str))

        while True:
            if web_socket.application_state == WebSocketState.CONNECTED:
                data = await web_socket.receive_text()
                message_data = json.loads(data)
                message_data["user"] = user_dict
                if room and not admin:
                    message_data["user"]["admin"] = 1
                if message_data.get("type", None) == "leave":
                    logger.warning(message_data)
                    logger.info("Disconnecting from Websocket")
                    await update_chat_status("offline", user, session)
                    data = {
                        "content": f"{display_name} went offline!",
                        "type": "offline",
                        "user": user_dict,
                    }
                    await connection.publish(
                        topic, json.dumps(data, default=str)
                    )
                    await web_socket.close()
                    break
                elif message_data.get("type", None) in ("media", "file"):
                    data = message_data.pop("content")
                    original_filename = message_data.get("filename", "")
                    
                    try:
                        bin_file = base64.b64decode(data)
                    except Exception as e:
                        logger.error(f"Failed to decode base64 file: {e}")
                        continue
                    
                    if receiver_id:
                        receiver = await find_existed_user_id(
                            receiver_id, session
                        )
                        request = RequestContactObject(
                            receiver["email"],
                            "",
                            message_data["type"],
                            "",
                            original_filename,
                        )
                        result = await send_new_message(
                            sender_id, request, bin_file, None, session
                        )

                        if isinstance(result, dict) and "url" in result:
                            message_data["media"] = result["url"]
                            message_data["fileInfo"] = {
                                "filename": result.get("filename", original_filename),
                                "extension": result.get("extension", ""),
                                "category": result.get("category", "file"),
                                "size": result.get("size", 0)
                            }
                        elif isinstance(result, str):

                            message_data["media"] = result
                        else:
                            logger.error(f"Failed to save file: {result}")
                            continue
                        message_data["content"] = ""
                        message_data.pop("preview", None)
                    else:
                        request = RequestRoomObject(
                            topic,
                            "",
                            message_data["type"],
                            "",
                            original_filename,
                        )
                        result = await send_new_room_message(
                            sender_id, request, bin_file, session
                        )

                        if isinstance(result, dict) and "url" in result:
                            message_data["media"] = result["url"]
                            message_data["fileInfo"] = {
                                "filename": result.get("filename", original_filename),
                                "extension": result.get("extension", ""),
                                "category": result.get("category", "file"),
                                "size": result.get("size", 0)
                            }
                        elif isinstance(result, str):

                            message_data["media"] = result
                        else:
                            logger.error(f"Failed to save file: {result}")
                            continue
                        message_data["content"] = ""
                        message_data.pop("preview", None)
                    await connection.publish(
                        topic, json.dumps(message_data, default=str)
                    )
                    del request
                elif message_data.get("type", None) == "ban":
                    ensure_future(
                        ban_user_from_room(
                            admin_id=sender_id,
                            user_email=message_data["receiver"],
                            room_name=message_data["room_name"],
                            session=session,
                        )
                    )
                    await connection.publish(
                        topic, json.dumps(message_data, default=str)
                    )
                elif message_data.get("type", None) == "unban":
                    ensure_future(
                        unban_user_from_room(
                            admin_id=sender_id,
                            user_email=message_data["receiver"],
                            room_name=message_data["room_name"],
                            session=session,
                        )
                    )
                    await connection.publish(
                        topic, json.dumps(message_data, default=str)
                    )
                else:
                    logger.info(
                        f"CONSUMER RECIEVED: {json.dumps(message_data, default=str)}"  # noqa: E501
                    )
                    await connection.publish(
                        topic, json.dumps(message_data, default=str)
                    )
                    if receiver_id:
                        receiver = await find_existed_user_id(
                            receiver_id, session
                        )
                        request = RequestContactObject(
                            receiver["email"],
                            message_data["content"],
                            message_data["type"],
                            "",
                        )
                        ensure_future(
                            send_new_message(
                                sender_id, request, None, None, session
                            )
                        )
                    else:
                        request = RequestRoomObject(
                            topic,
                            message_data["content"],
                            message_data["type"],
                            "",
                        )
                        ensure_future(
                            send_new_room_message(
                                sender_id, request, None, session
                            )
                        )
                    del request
            else:
                logger.warning(
                    f"Websocket state: {web_socket.application_state}."  # noqa: E501
                )
                break
    except Exception as ex:
        message = f"An exception of type {type(ex).__name__} occurred. Arguments:\n{ex.args!r}"  # noqa: E501
        logger.error(message)
        await connection.close()

        logger.warning("Disconnecting Websocket")


async def producer_handler(
    pub_sub,  
    topic: str,
    web_socket: WebSocket,
) -> None:
    await pub_sub.subscribe(topic)
    try:
        while True:
            if web_socket.application_state == WebSocketState.CONNECTED:
                message = await pub_sub.get_message(
                    ignore_subscribe_messages=True
                )
                if message:

                    data = message["data"]
                    logger.info(f"PRODUCER SENDING: {data}")
                    await web_socket.send_text(data)
            else:
                logger.warning(
                    f"Websocket state: {web_socket.application_state}."  # noqa: E501
                )
                break
    except Exception as ex:
        message = f"An exception of type {type(ex).__name__} occurred. Arguments:\n{ex.args!r}"  # noqa: E501
        logger.error(message)
        logger.warning("Disconnecting Websocket")