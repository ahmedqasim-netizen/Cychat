import logging
from asyncio import (
    current_task,
)
from fastapi import (
    FastAPI,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    create_async_engine,
)
from sqlalchemy.orm import (
    sessionmaker,
)

from app.config import (
    settings,
)

logger = logging.getLogger(__name__)


_db_autocommit_session_factory = None
_db_transactional_session_factory = None


def get_autocommit_session_factory():

    return _db_autocommit_session_factory


def get_transactional_session_factory():
    return _db_transactional_session_factory


async def init_engine_app(app: FastAPI) -> None:  # pragma: no cover

    from sqlalchemy import (
        text,
    )


    from app.auth.models import (  
        AccessTokens,
    )
    from app.chats.models import ( 
        Messages,
    )
    from app.contacts.models import (  
        Contacts,
    )
    from app.rooms.models import (  
        RoomMembers,
        Rooms,
    )
    from app.users.models import ( 
        Users,
    )
    from app.utils.mixins import (  
        Base,
    )

    logger.info(f"Connecting to database: {settings.DB_NAME}")
    logger.info(f"Database URL: {settings.db_url.split('@')[0]}@***")

    engine = create_async_engine(
        settings.db_url,
        pool_pre_ping=True,
        pool_size=30,
        max_overflow=30,
        echo_pool=True,
        future=True,
        echo=settings.DEBUG == "info",  
        pool_recycle=3600,
    )  

    async with engine.begin() as conn:
        
        try:
            result = await conn.execute(text("SELECT DB_NAME() AS current_db"))
            row = result.fetchone()
            logger.info(f"Connected to database: {row[0]}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise


        try:
            result = await conn.execute(
                text("SELECT * FROM sys.schemas WHERE name = 'chat'")
            )
            schema = result.fetchone()
            if schema:
                logger.info("Schema 'chat' found in database")
            else:
                logger.warning("Schema 'chat' not found - creating it...")
                await conn.execute(text("EXEC('CREATE SCHEMA chat')"))
        except Exception as e:
            logger.warning(f"Schema check failed: {e}")


        tables_to_check = ['users', 'access_tokens', 'contacts', 'rooms', 'room_members', 'messages']
        for table in tables_to_check:
            try:
                result = await conn.execute(
                    text(f"""
                        SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_SCHEMA = 'chat' AND TABLE_NAME = '{table}'
                    """)
                )
                exists = result.scalar()
                if exists:
                    logger.info(f"Table chat.{table} exists")
                else:
                    logger.warning(f"Table chat.{table} NOT FOUND - may need to run SQL creation script")
            except Exception as e:
                logger.warning(f"Could not check table {table}: {e}")


    autocommit_engine = engine.execution_options(isolation_level="AUTOCOMMIT")
    autocommit_session_factory = async_scoped_session(
        sessionmaker(
            autocommit_engine,
            expire_on_commit=False,
            class_=AsyncSession,
        ),
        scopefunc=current_task,
    )
    transactional_session_factory = async_scoped_session(
        sessionmaker(
            engine,
            expire_on_commit=False,
            class_=AsyncSession,
        ),
        scopefunc=current_task,
    )

    app.state.db_engine = engine
    app.state.db_transactional_session_factory = transactional_session_factory
    app.state.db_autocommit_session_factory = autocommit_session_factory
    
    global _db_autocommit_session_factory, _db_transactional_session_factory
    _db_autocommit_session_factory = autocommit_session_factory
    _db_transactional_session_factory = transactional_session_factory
    
    logger.info("Database engine initialized successfully")