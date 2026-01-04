from sqlalchemy import (
    exc,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)
from starlette.requests import (
    Request,
)
from typing import (
    AsyncGenerator,
)


async def get_db_transactional_session(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:
    session: AsyncSession = (
        request.app.state.db_transactional_session_factory()
    )

    try: 
        yield session
    except exc.DBAPIError:
        await session.rollback()
    finally:
        await session.commit()
        await session.close()


async def get_db_autocommit_session(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:

    session: AsyncSession = request.app.state.db_autocommit_session_factory()

    try:  
        yield session
    except exc.DBAPIError:
        await session.rollback()
    finally:
        await session.close()


async def get_db_autocommit_session_socket() -> AsyncGenerator[
    AsyncSession, None
]:

    from app.utils.engine import get_autocommit_session_factory

    session_factory = get_autocommit_session_factory()
    if session_factory is None:
        raise RuntimeError("Database not initialized. Please wait for startup to complete.")
    
    session: AsyncSession = session_factory()

    try:  
        yield session
    except exc.DBAPIError:
        await session.rollback()
    finally:
        await session.close()