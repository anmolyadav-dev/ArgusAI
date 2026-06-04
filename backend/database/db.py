"""
SQLite database models and connection management.
Uses SQLAlchemy async for non-blocking database operations.
"""

import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Integer, Float
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from backend.config import settings


# ============================================================
# SQLAlchemy Base
# ============================================================

class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# ============================================================
# Database Models
# ============================================================

class ScanRecord(Base):
    """Stores the full history of each scan."""
    __tablename__ = "scans"

    id = Column(String, primary_key=True)
    target = Column(String, nullable=False, index=True)
    objective = Column(Text, default="")
    status = Column(String, default="pending")

    # Store JSON blobs for flexibility
    plan_json = Column(Text, default="{}")        # Planner output
    results_json = Column(Text, default="[]")      # Tool results
    analysis_json = Column(Text, default="{}")     # Analysis output
    report_json = Column(Text, default="{}")       # Report output

    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    total_findings = Column(Integer, default=0)
    execution_time = Column(Float, default=0.0)


class ChatHistory(Base):
    """Stores chat messages linked to scans."""
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String, nullable=True, index=True)
    role = Column(String, nullable=False)   # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ============================================================
# Database Connection
# ============================================================

# Create async engine and session factory
engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get a new database session."""
    async with async_session() as session:
        return session


# ============================================================
# CRUD Operations
# ============================================================

async def save_scan(scan: ScanRecord):
    """Save or update a scan record."""
    async with async_session() as session:
        await session.merge(scan)
        await session.commit()


async def get_scan(scan_id: str) -> ScanRecord | None:
    """Get a scan by ID."""
    async with async_session() as session:
        return await session.get(ScanRecord, scan_id)


async def get_scans_for_target(target: str) -> list[ScanRecord]:
    """Get all scans for a specific target (for comparison)."""
    from sqlalchemy import select
    async with async_session() as session:
        result = await session.execute(
            select(ScanRecord)
            .where(ScanRecord.target == target)
            .order_by(ScanRecord.created_at.desc())
        )
        return list(result.scalars().all())


async def get_all_scans() -> list[ScanRecord]:
    """Get all scan records, newest first."""
    from sqlalchemy import select
    async with async_session() as session:
        result = await session.execute(
            select(ScanRecord).order_by(ScanRecord.created_at.desc())
        )
        return list(result.scalars().all())


async def save_chat_message(scan_id: str | None, role: str, content: str):
    """Save a chat message."""
    async with async_session() as session:
        msg = ChatHistory(scan_id=scan_id, role=role, content=content)
        session.add(msg)
        await session.commit()


async def get_chat_history(scan_id: str) -> list[ChatHistory]:
    """Get chat history for a specific scan."""
    from sqlalchemy import select
    async with async_session() as session:
        result = await session.execute(
            select(ChatHistory)
            .where(ChatHistory.scan_id == scan_id)
            .order_by(ChatHistory.created_at.asc())
        )
        return list(result.scalars().all())
