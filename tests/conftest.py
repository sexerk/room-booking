import pytest
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from starlette.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings

TEST_DATABASE_URL = str(settings.DATABASE_URL).replace("room_booking", "test_room_booking")
TEST_DATABASE_URL_SYNC = TEST_DATABASE_URL.replace("postgresql+asyncpg", "postgresql")


def _setup_test_db():
    conn = psycopg2.connect(
        host="db", port=5432,
        user="postgres", password="postgres",
        database="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'test_room_booking'")
    if not cur.fetchone():
        cur.execute("CREATE DATABASE test_room_booking")
    cur.close()
    conn.close()

    sync_engine = create_engine(TEST_DATABASE_URL_SYNC)
    Base.metadata.create_all(sync_engine)
    sync_engine.dispose()


def _teardown_test_db():
    sync_engine = create_engine(TEST_DATABASE_URL_SYNC)
    Base.metadata.drop_all(sync_engine)
    sync_engine.dispose()


_setup_test_db()

sync_engine = create_engine(TEST_DATABASE_URL_SYNC)
SyncTestingSessionLocal = sessionmaker(sync_engine, expire_on_commit=False)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()

app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def prepare_test_db():
    yield
    _teardown_test_db()


@pytest.fixture(autouse=True)
def mock_cache():
    with patch("app.cache.availability_cache.redis_client") as mock:
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=1)
        mock.clear_pattern = AsyncMock(return_value=0)
        mock.keys = AsyncMock(return_value=[])
        yield mock


@pytest.fixture(autouse=True)
def clean_tables(db_session):
    yield
    db_session.execute(text("TRUNCATE bookings, users, rooms RESTART IDENTITY CASCADE"))
    db_session.commit()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    with SyncTestingSessionLocal() as session:
        yield session
        session.rollback()


@pytest.fixture
def client() -> Generator:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user(db_session):
    from app.core.security import get_password_hash
    from app.models.user import User

    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpass123"),
        full_name="Test User",
        is_active=True,
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin(db_session):
    from app.core.security import get_password_hash
    from app.models.user import User

    admin = User(
        email="admin@example.com",
        username="admin",
        hashed_password=get_password_hash("adminpass123"),
        full_name="Admin User",
        is_active=True,
        is_admin=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def test_room(db_session):
    from app.models.room import Room

    room = Room(
        name="Test Room",
        description="Test Description",
        floor=1,
        capacity=10,
        price_per_hour=100.0,
        is_active=True
    )
    db_session.add(room)
    db_session.commit()
    db_session.refresh(room)
    return room