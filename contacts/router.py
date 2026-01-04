from fastapi import (
    APIRouter,
    Depends,
)
from pydantic import (
    BaseModel,
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
from app.contacts.crud import (
    create_new_contact,
    create_new_contact_by_nickname,
    delete_contact_user,
    get_message_requests,
    get_user_contacts,
    search_user_contacts,
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

router = APIRouter(prefix="/api/v1")


class ContactCreate(BaseModel):
    email: str = None  
    nickname: str = None  
    
    class Config:
        extra = "forbid"


class ContactDelete(BaseModel):
    email: EmailStr


@router.post(
    "/contact",
    response_model=ResponseSchema,
    status_code=201,
    name="contacts:add-contact",
    responses={
        201: {
            "model": ResponseSchema,
            "description": "Contact has been added successfully!",
        },
        400: {
            "model": ResponseSchema,
            "description": "User not registered or already in contact list!",
        },
    },
)
async def add_contact(
    request: ContactCreate,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    if request.nickname:
        results = await create_new_contact_by_nickname(
            contact_nickname=request.nickname,
            user_id=currentUser.id,
            session=session,
        )
    elif request.email:
        results = await create_new_contact(
            contact_email=request.email,
            user_id=currentUser.id,
            session=session,
        )
    else:
        results = {
            "status_code": 400,
            "message": "Please provide either email or nickname!",
        }
    return results


@router.get(
    "/contacts",
    status_code=200,
    name="contacts:get-contacts",
    responses={
        200: {
            "description": "Return a list of user's contacts.",
        },
    },
)
async def get_contacts(
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    results = await get_user_contacts(
        user_id=currentUser.id,
        session=session,
    )
    return results


@router.get(
    "/contacts/search",
    status_code=200,
    name="contacts:search-contacts",
    responses={
        200: {
            "description": "Return a list of contacts matching search.",
        },
    },
)
async def search_contacts(
    search: str = "",
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    results = await search_user_contacts(
        search=search,
        user_id=currentUser.id,
        session=session,
    )
    return results


@router.delete(
    "/contact/delete",
    response_model=ResponseSchema,
    status_code=200,
    name="contacts:delete-contact",
    responses={
        200: {
            "model": ResponseSchema,
            "description": "Contact has been deleted successfully!",
        },
        400: {
            "model": ResponseSchema,
            "description": "Contact not found or can't be deleted!",
        },
    },
)
async def delete_contact(
    request: ContactDelete,
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    results = await delete_contact_user(
        contact_email=request.email,
        user_id=currentUser.id,
        session=session,
    )
    return results


@router.get(
    "/message-requests",
    status_code=200,
    name="contacts:message-requests",
    responses={
        200: {
            "description": "Return a list of users who sent messages but aren't contacts.",
        },
    },
)
async def get_message_requests_endpoint(
    currentUser: UserObjectSchema = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    results = await get_message_requests(
        user_id=currentUser.id,
        session=session,
    )
    return results
