import datetime
import logging
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


async def find_user_by_nickname(nickname: str, session: AsyncSession):

    query = "SELECT * FROM chat.users WHERE nickname = :nickname"
    values = {"nickname": nickname}
    result = await session.execute(text(query), values)
    user = result.fetchone()
    if user:
        return user._asdict()
    return None

logger = logging.getLogger(__name__)


async def create_new_contact_by_nickname(
    contact_nickname: str, user_id: int, session: AsyncSession
) -> dict[str, Any]:

    contact = await find_user_by_nickname(nickname=contact_nickname, session=session)
    if not contact:
        return {
            "status_code": 400,
            "message": "User not found!",
        }
    elif contact["id"] == user_id:
        return {
            "status_code": 400,
            "message": "You can't add yourself!",
        }


    query = """
        SELECT
          *
        FROM
          chat.contacts
        WHERE
          [user] = :user_id
        AND
          contact = :contact_id
    """
    values = {"user_id": user_id, "contact_id": contact["id"]}
    result = await session.execute(text(query), values)
    found_contact = result.fetchone()

    if found_contact:
        return {
            "status_code": 400,
            "message": f"{contact['nickname']} already exists in your contact list!",
        }


    query = """
        INSERT INTO chat.contacts (
          [user],
          contact,
          creation_date,
          modified_date
        )
        VALUES (
          :user_id,
          :contact_id,
          :creation_date,
          :modified_date
        )
    """
    now = datetime.datetime.utcnow()
    values = {
        "user_id": user_id,
        "contact_id": contact["id"],
        "creation_date": now,
        "modified_date": now,
    }

    await session.execute(text(query), values)
    results = {
        "status_code": 201,
        "message": f"{contact['nickname']} has been added to your contact list!",
    }
    return results


async def create_new_contact(
    contact_email: str, user_id: int, session: AsyncSession
) -> dict[str, Any]:

    contact = await find_existed_user(email=contact_email, session=session)
    if not contact:
        return {
            "status_code": 400,
            "message": "User not registered!",
        }
    elif contact["id"] == user_id:
        return {
            "status_code": 400,
            "message": "You can't add yourself!",
        }

    query = """
        SELECT
          *
        FROM
          chat.contacts
        WHERE
          [user] = :user_id
        AND
          contact = :contact_id
    """
    values = {"user_id": user_id, "contact_id": contact["id"]}
    result = await session.execute(text(query), values)
    found_contact = result.fetchone()

    if found_contact:
        return {
            "status_code": 400,
            "message": f"{contact['nickname']} already exists in your contact list!",
        }


    query = """
        INSERT INTO chat.contacts (
          [user],
          contact,
          creation_date,
          modified_date
        )
        VALUES (
          :user_id,
          :contact_id,
          :creation_date,
          :modified_date
        )
    """
    now = datetime.datetime.utcnow()
    values = {
        "user_id": user_id,
        "contact_id": contact["id"],
        "creation_date": now,
        "modified_date": now,
    }

    await session.execute(text(query), values)
    results = {
        "status_code": 201,
        "message": f"{contact['nickname']} has been added to your contact list!",
    }
    return results


async def delete_contact_user(
    contact_email: str, user_id: int, session: AsyncSession
) -> dict[str, Any]:

    contact = await find_existed_user(email=contact_email, session=session)
    if not contact:
        return {
            "status_code": 400,
            "message": "You can't delete a non existing user!",
        }
    elif contact["id"] == user_id:
        return {
            "status_code": 400,
            "message": "You can't delete yourself!",
        }

    query = """
        SELECT
          *
        FROM
          chat.contacts
        WHERE
          [user] = :user_id
        AND
          contact = :contact_id
    """
    values = {"user_id": user_id, "contact_id": contact["id"]}
    result = await session.execute(text(query), values)
    contacts = result.fetchall()

    if not contacts:
        return {
            "status_code": 400,
            "message": "There is no contact to delete!",
        }
    else:
        query = """
            DELETE
            FROM
              chat.contacts
            WHERE
              [user] = :user_id
            AND
              contact = :contact_id
        """
        values = {"user_id": user_id, "contact_id": contact["id"]}
        await session.execute(text(query), values)

        results = {
            "status_code": 200,
            "message": f"{contact['nickname']} has been deleted from your contact list!",
        }
    return results


async def get_contacts(session: AsyncSession) -> dict[str, Any]:

    query = """
        SELECT
          c.*,
          u.*
        FROM
          chat.contacts c
        LEFT JOIN
          chat.users u
        ON
          c.[user] = u.id
        GROUP BY
          c.id, c.[user], c.contact, c.creation_date, c.modified_date,
          u.id, u.nickname, u.email, u.password, u.phone_number, u.user_role, u.creation_date, u.modified_date
    """
    result = await session.execute(text(query))
    contacts = result.fetchall()
    results = {
        "status_code": 200,
        "result": [dict(row._mapping) for row in contacts],
    }
    return results


async def find_existed_user_contact(user_id: int, session: AsyncSession):

    query = "SELECT * FROM chat.contacts WHERE [user] = :user_id"
    values = {"user_id": user_id}
    result = await session.execute(text(query), values)
    return result.fetchone()


async def get_user_contacts(user_id: int, session: AsyncSession) -> dict[str, Any]:

    user = await find_existed_user_contact(user_id, session)
    if user:
        query = """
            SELECT
              c.id AS contact_record_id,
              c.creation_date AS contact_added_date,
              u.id,
              u.nickname,
              u.email,
              u.phone_number,
              u.user_role
            FROM
              chat.contacts c
            LEFT JOIN
              chat.users u
            ON
              c.contact = u.id
            WHERE
              c.[user] = :user_id
        """
        values = {"user_id": user_id}

        result = await session.execute(text(query), values)
        contacts = result.fetchall()
        results = {
            "status_code": 200,
            "result": [dict(row._mapping) for row in contacts],
        }
        return results
    return {"status_code": 200, "result": []}


async def search_user_contacts(
    search: str, user_id: int, session: AsyncSession
) -> dict[str, Any]:

    user = await find_existed_user_contact(user_id, session)
    
    if not search or len(search) == 0:
        query = """
            SELECT
              c.id AS contact_record_id,
              c.creation_date AS contact_added_date,
              u.id,
              u.nickname,
              u.email,
              u.phone_number,
              u.user_role
            FROM
              chat.contacts c
            LEFT JOIN
              chat.users u
            ON
              c.contact = u.id
            WHERE
              c.[user] = :user_id
        """
        values = {"user_id": user_id}
        result = await session.execute(text(query), values)
        return_results = result.fetchall()
        results = {
            "status_code": 200,
            "result": [dict(row._mapping) for row in return_results],
        }
        return results

    elif user and search:

        query = """
            SELECT
              c.id AS contact_record_id,
              c.creation_date AS contact_added_date,
              u.id,
              u.nickname,
              u.email,
              u.phone_number,
              u.user_role
            FROM
              chat.contacts c
            LEFT JOIN
              chat.users u
            ON
              c.contact = u.id
            WHERE
              c.[user] = :user_id
            AND
              (
                u.nickname LIKE :search
                OR u.email LIKE :search
              )
        """
        values = {"user_id": user_id, "search": f"%{search}%"}
        result = await session.execute(text(query), values)
        return_results = result.fetchall()
        results = {
            "status_code": 200,
            "result": [dict(row._mapping) for row in return_results],
        }
        return results
    
    return {"status_code": 200, "result": []}


async def get_message_requests(user_id: int, session: AsyncSession) -> dict[str, Any]:

    query = """
        SELECT DISTINCT
            u.id,
            u.nickname,
            u.email,
            u.phone_number,
            u.user_role,
            (
                SELECT COUNT(*) 
                FROM chat.messages m2 
                WHERE m2.sender = u.id AND m2.receiver = :user_id
            ) AS unread_count,
            (
                SELECT TOP 1 m3.creation_date 
                FROM chat.messages m3 
                WHERE m3.sender = u.id AND m3.receiver = :user_id
                ORDER BY m3.creation_date DESC
            ) AS last_message_date
        FROM
            chat.messages m
        INNER JOIN
            chat.users u ON m.sender = u.id
        WHERE
            m.receiver = :user_id
            AND m.sender != :user_id
            AND m.sender NOT IN (
                SELECT contact FROM chat.contacts WHERE [user] = :user_id
            )
        ORDER BY
            last_message_date DESC
    """
    values = {"user_id": user_id}
    result = await session.execute(text(query), values)
    requests = result.fetchall()
    
    return {
        "status_code": 200,
        "result": [dict(row._mapping) for row in requests],
    }