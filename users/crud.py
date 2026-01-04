import datetime
import os
import shutil
from pathlib import Path
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)
from sqlalchemy.sql import (
    text,
)

from app.auth.crud import (
    find_existed_user,
)
from app.users.models import (
    Users,
)
from app.users.schemas import (
    ResetPassword,
)
from app.utils.crypt_util import (
    get_password_hash,
    verify_password,
)


UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
PROFILE_IMAGES_DIR = UPLOAD_DIR / "profile-images"


PROFILE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


async def deactivate_user(currentUser: Users, session: AsyncSession):

    query = """
        UPDATE
          chat.users
        SET
          user_role = 'disabled',
          modified_date = :modified_date
        WHERE
          email = :email
    """
    values = {
        "email": currentUser.email,
        "modified_date": datetime.datetime.utcnow(),
    }

    return await session.execute(text(query), values)


async def set_black_list(token: str, session: AsyncSession):

    query = """
        UPDATE
          chat.access_tokens
        SET
          token_status = 0,
          modified_date = :modified_date
        WHERE
          token_status = 1
          AND token = :token
    """
    values = {
        "token": token,
        "modified_date": datetime.datetime.utcnow(),
    }

    return await session.execute(text(query), values)


async def update_user_info(currentUser: Users, session: AsyncSession):

    query = """
        UPDATE
          chat.users
        SET
          nickname = :nickname,
          phone_number = :phone_number,
          modified_date = :modified_date
        WHERE
          email = :email
    """
    values = {
        "nickname": currentUser.nickname,
        "phone_number": currentUser.phone_number,
        "email": currentUser.email,
        "modified_date": datetime.datetime.utcnow(),
    }

    return await session.execute(text(query), values)


async def update_chat_status(
    chat_status: str, currentUser: Users, session: AsyncSession
):

    return None


async def update_user_password(
    request: ResetPassword, currentUser: Users, session: AsyncSession
):

    user = await find_existed_user(currentUser.email, session)
    if not verify_password(request.old_password, user["password"]):
        results = {
            "status_code": 400,
            "message": "Your old password is not correct!",
        }
    elif verify_password(request.new_password, user["password"]):
        results = {
            "status_code": 400,
            "message": "Your new password can't be your old one!",
        }
    elif not request.new_password == request.confirm_password:
        results = {
            "status_code": 400,
            "message": "Please confirm your new password!",
        }
    else:
        query = """
            UPDATE
              chat.users
            SET
              password = :password,
              modified_date = :modified_date
            WHERE
              email = :email
        """
        values = {
            "password": get_password_hash(request.new_password),
            "email": currentUser.email,
            "modified_date": datetime.datetime.utcnow(),
        }
        await session.execute(text(query), values)
        results = {
            "status_code": 200,
            "message": "Your password has been reset successfully!",
        }
    return results


async def update_profile_picture(
    email: str, file_name: str, session: AsyncSession
):

    return None


def save_profile_image(user_id: int, file_content: bytes) -> str:

    user_dir = PROFILE_IMAGES_DIR / f"user/{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = user_dir / "profile.png"
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return f"user/{user_id}/profile.png"


def get_profile_image_path(user_id: int) -> Path:

    return PROFILE_IMAGES_DIR / f"user/{user_id}/profile.png"


def delete_profile_image(user_id: int) -> bool:

    file_path = get_profile_image_path(user_id)
    if file_path.exists():
        file_path.unlink()
        return True
    return False


async def update_public_key(
    user_id: int, public_key: str, session: AsyncSession
):

    query = """
        UPDATE
          chat.users
        SET
          public_key = :public_key,
          modified_date = :modified_date
        WHERE
          id = :user_id
    """
    values = {
        "public_key": public_key,
        "user_id": user_id,
        "modified_date": datetime.datetime.utcnow(),
    }
    await session.execute(text(query), values)
    return {"status_code": 200, "message": "Public key updated successfully!"}


async def get_public_key(user_id: int, session: AsyncSession) -> dict:

    query = "SELECT id, nickname, public_key FROM chat.users WHERE id = :user_id"
    values = {"user_id": user_id}
    result = await session.execute(text(query), values)
    user = result.fetchone()
    
    if user:
        user_dict = user._asdict()
        return {
            "status_code": 200,
            "user_id": user_dict["id"],
            "nickname": user_dict["nickname"],
            "public_key": user_dict.get("public_key")
        }
    return {"status_code": 404, "message": "User not found"}


async def get_public_keys_batch(user_ids: list, session: AsyncSession) -> dict:

    if not user_ids:
        return {"status_code": 200, "keys": {}}
    
    placeholders = ", ".join([f":id_{i}" for i in range(len(user_ids))])
    query = f"""
        SELECT id, nickname, public_key 
        FROM chat.users 
        WHERE id IN ({placeholders})
    """
    values = {f"id_{i}": uid for i, uid in enumerate(user_ids)}
    result = await session.execute(text(query), values)
    users = result.fetchall()
    
    keys = {}
    for user in users:
        user_dict = user._asdict()
        keys[str(user_dict["id"])] = {
            "nickname": user_dict["nickname"],
            "public_key": user_dict.get("public_key")
        }
    
    return {"status_code": 200, "keys": keys}