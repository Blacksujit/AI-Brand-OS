from __future__ import annotations

import pytest

from database import Database


@pytest.mark.asyncio
async def test_db_verify_connection(db: Database) -> None:
    result = await db.verify_connection()
    assert result is True


@pytest.mark.asyncio
async def test_db_health_check(db: Database) -> None:
    health = await db.health_check()
    assert health["status"] == "healthy"
    assert health["response_ms"] >= 0
    assert health["pool_size"] is None or health["pool_size"] >= 0


@pytest.mark.asyncio
async def test_db_session_commit_rollback(db: Database) -> None:
    async with db.session() as session:
        from models.user import User

        user = User(
            email="test@example.com",
            password_hash="hash",
            display_name="Test User",
        )
        session.add(user)

    async with db.session() as session:
        from sqlalchemy import select

        from models.user import User

        result = await session.execute(select(User).where(User.email == "test@example.com"))
        found = result.scalar_one_or_none()
        assert found is not None
        assert found.display_name == "Test User"


@pytest.mark.asyncio
async def test_db_session_rollback_on_error(db: Database) -> None:
    with pytest.raises(ValueError, match="boom"):
        async with db.session() as session:
            from models.user import User

            session.add(
                User(
                    email="test@example.com",
                    password_hash="hash",
                    display_name="Test User",
                )
            )
            msg = "boom"
            raise ValueError(msg)


@pytest.mark.asyncio
async def test_db_close_twice(db: Database) -> None:
    await db.close()
    await db.close()
