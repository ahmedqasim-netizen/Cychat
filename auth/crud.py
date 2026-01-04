import datetime
from fastapi.encoders import (
    jsonable_encoder,
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
)
from pydantic import (
    EmailStr,
)
from sqlalchemy.engine import (
    Result,
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

from app.auth.schemas import (
    UserCreate,
    UserLoginSchema,
)
from app.users.schemas import (
    UserObjectSchema,
)
from app.utils.constants import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.utils.crypt_util import (
    get_password_hash,
    verify_password,
)
from app.utils.jwt_util import (
    create_access_token,
    timedelta,
)


async def create_user(user: UserCreate, session: AsyncSession) -> Result:
    query = """
        INSERT INTO chat.users (
          nickname,
          email,
          password,
          phone_number,
          user_role,
          creation_date,
          modified_date
        )
        VALUES (
          :nickname,
          :email,
          :password,
          :phone_number,
          'user',
          :creation_date,
          :modified_date
        )
    """
    now = datetime.datetime.utcnow()
    values = {
        "nickname": user.nickname,
        "email": user.email,
        "password": user.password,
        "phone_number": user.phone_number,
        "creation_date": now,
        "modified_date": now,
    }
    return await session.execute(text(query), values)


async def find_existed_user(
    email: EmailStr, session: AsyncSession
):
    query = "SELECT * FROM chat.users WHERE email = :email"
    values = {"email": email}
    result = await session.execute(text(query), values)
    user = result.fetchone()
    if user:
        return user._asdict()
    return None


async def find_existed_user_id(
    id_: int, session: AsyncSession
) -> dict[str, Any]:
    query = "SELECT * FROM chat.users WHERE id = :id"
    values = {"id": id_}
    result = await session.execute(text(query), values)
    user = result.fetchone()
    if user:
        return user._asdict()
    return None


async def get_users_with_black_listed_token(
    token: str, session: AsyncSession
) -> dict[str, Any]:
    query = """
        SELECT
          *
        FROM
          chat.access_tokens
        WHERE
          token = :token
        AND
          token_status = 0
    """
    values = {"token": token}
    result = await session.execute(text(query), values)
    token_row = result.fetchone()
    return token_row


async def login_user(
    form_data: OAuth2PasswordRequestForm, session: AsyncSession
) -> dict[str, Any]:
    user_obj = await find_existed_user(form_data.username, session)
    if not user_obj:
        return {"status_code": 400, "message": "User not found!"}
    user = UserLoginSchema(email=user_obj["email"], password=user_obj["password"])
    is_valid = verify_password(form_data.password, user.password)
    if not is_valid:
        return {"status_code": 401, "message": "Invalid Credentials!"}

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": form_data.username},
        expires_delta=access_token_expires,
    )
    query = """
        INSERT INTO
            chat.access_tokens (
                [user],
                token,
                creation_date,
                modified_date,
                token_status
            )
        VALUES
            (
                :user_id,
                :token,
                :creation_date,
                :modified_date,
                1
            )
    """
    now = datetime.datetime.utcnow()
    values = {
        "user_id": user_obj["id"],
        "token": access_token["access_token"],
        "creation_date": now,
        "modified_date": now,
    }
    await session.execute(text(query), values)

    return access_token


async def register_user(
    user: UserCreate, session: AsyncSession
) -> dict[str, Any]:

    fetched_user = await find_existed_user(user.email, session)
    if fetched_user:
        return {"status_code": 400, "message": "User already signed up!"}


    user.password = get_password_hash(user.password)
    await create_user(user, session)
    user_row = await find_existed_user(user.email, session)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user_row["email"]},
        expires_delta=access_token_expires,
    )

    results = {
        "user": UserObjectSchema(**user_row),
        "token": access_token,
        "status_code": 201,
        "message": "Welcome! Proceed to the login page...",
    }
    return results