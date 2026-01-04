import os
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.encoders import (
    jsonable_encoder,
)
from fastapi.responses import (
    FileResponse,
)
from pathlib import Path
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.auth.schemas import (
    UserSchema,
)
from app.users import (
    crud as user_crud,
)
from app.users.models import (
    Users,
)
from app.users.schemas import (
    PersonalInfo,
    ResetPassword,
    UpdatePublicKey,
    UpdateStatus,
    UserObjectSchema,
)
from app.utils import (
    jwt_util,
)
from app.utils.dependencies import (
    get_db_autocommit_session,
    get_db_transactional_session,
)


UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
PROFILE_IMAGES_DIR = UPLOAD_DIR / "profile-images"

router = APIRouter(prefix="/api/v1")


@router.get("/user/profile")
async def get_user_profile(
    currentUser: UserObjectSchema = Depends(jwt_util.get_current_active_user),
):

    return {
        "token": None,
        "user": {
            "id": currentUser.id,
            "nickname": currentUser.nickname,
            "email": currentUser.email,
            "phone_number": currentUser.phone_number,
            "user_role": currentUser.user_role,
        },
        "status_code": 200,
        "message": "Welcome to Brave Chat.",
    }


@router.put("/user/profile")
async def update_personal_information(
    personal_info: PersonalInfo,
    currentUser: UserObjectSchema = Depends(jwt_util.get_current_active_user),
    session: AsyncSession = Depends(get_db_transactional_session),
):
    currentUser = UserObjectSchema(**jsonable_encoder(currentUser))
    currentUser.nickname = personal_info.nickname
    currentUser.phone_number = personal_info.phone_number
    await user_crud.update_user_info(currentUser, session)
    return {
        "status_code": 200,
        "message": "Your personal information has been updated successfully!",
    }


@router.get("/user/logout")
async def logout(
    token: str = Depends(jwt_util.get_token_user),
    currentUser: Users = Depends(jwt_util.get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    await user_crud.set_black_list(token, session)
    return {"status": 200, "message": "Good Bye!"}


@router.put("/user")
async def update_user_status(
    request: UpdateStatus,
    currentUser=Depends(jwt_util.get_current_active_user),
    session: AsyncSession = Depends(get_db_transactional_session),
):

    await user_crud.update_chat_status(
        request.chat_status.lower(), currentUser, session
    )
    return {
        "status_code": 200,
        "message": "Status has been updated successfully!",
    }


@router.put("/user/reset-password")
async def reset_user_password(
    request: ResetPassword,
    currentUser=Depends(jwt_util.get_current_active_user),
    session: AsyncSession = Depends(get_db_transactional_session),
):

    result = await user_crud.update_user_password(
        request, currentUser, session
    )
    return result


@router.get("/user/profile-image/{name}")
async def get_profile_image(name: str):

    try:
        file_path = PROFILE_IMAGES_DIR / f"user/{name}/profile.png"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        return FileResponse(
            path=str(file_path),
            media_type="image/png",
            filename="profile.png"
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        return {"status_code": 400, "message": "Something went wrong!"}


@router.put("/user/profile-image")
async def upload_profile_image(
    file: UploadFile = File(...),
    currentUser: UserObjectSchema = Depends(jwt_util.get_current_active_user),
    session: AsyncSession = Depends(get_db_transactional_session),
):

    try:

        file_content = await file.read()
        
  
        file_name = user_crud.save_profile_image(currentUser.id, file_content)
        

        await user_crud.update_profile_picture(
            email=currentUser.email, file_name=file_name, session=session
        )
        return {
            "status_code": 200,
            "message": "Profile picture has been updated!",
        }

    except Exception:
        return {"status_code": 400, "message": "Something went wrong!"}


@router.get("/profile/user/{user_id}/profile.png")
async def get_profile_user_image(user_id: int):

    try:
        file_path = user_crud.get_profile_image_path(user_id)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        return FileResponse(
            path=str(file_path),
            media_type="image/png",
            filename="profile.png"
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        return {"status_code": 400, "message": "Something went wrong!"}




@router.put("/user/public-key")
async def update_public_key(
    request: UpdatePublicKey,
    currentUser: UserObjectSchema = Depends(jwt_util.get_current_active_user),
    session: AsyncSession = Depends(get_db_transactional_session),
):

    result = await user_crud.update_public_key(
        currentUser.id, request.public_key, session
    )
    return result


@router.get("/user/public-key")
async def get_my_public_key(
    currentUser: UserObjectSchema = Depends(jwt_util.get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    result = await user_crud.get_public_key(currentUser.id, session)
    return result


@router.get("/user/{user_id}/public-key")
async def get_user_public_key(
    user_id: int,
    currentUser: UserObjectSchema = Depends(jwt_util.get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    result = await user_crud.get_public_key(user_id, session)
    return result


@router.post("/users/public-keys")
async def get_users_public_keys(
    user_ids: list[int],
    currentUser: UserObjectSchema = Depends(jwt_util.get_current_active_user),
    session: AsyncSession = Depends(get_db_autocommit_session),
):

    result = await user_crud.get_public_keys_batch(user_ids, session)
    return result