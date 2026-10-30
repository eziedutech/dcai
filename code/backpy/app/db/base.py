"""Engine, session and column types shared by all tables."""

from collections.abc import Iterator
from datetime import UTC, datetime
from functools import lru_cache

from sqlalchemy import DateTime, Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.types import TypeDecorator


def utcnow() -> datetime:
    return datetime.now(UTC)


class UTCDateTime(TypeDecorator):
    """Timezone-aware UTC on every backend. SQLite drops tzinfo, so it is restored here."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("naive datetime")
        return value.astimezone(UTC)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class Base(DeclarativeBase):
    pass


def make_engine(url: str) -> Engine:
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    # Without a connect timeout an unreachable database makes requests hang forever instead
    # of failing with a clear error (found when the dev container had stopped).
    connect_args = {"connect_timeout": 5} if url.startswith("postgresql") else {}
    kwargs: dict = {"pool_pre_ping": True, "connect_args": connect_args}
    if url.startswith("postgresql"):
        # Device-wide screen reading bursts many messages at once, and every live SSE stream
        # (phone and dashboard) holds a connection for its whole life. The default 5+10 pool
        # is exhausted under that load (QueuePool timeout), which hangs the dashboard and
        # starves the background Guide/nudge work, so the level is stored but no insight or
        # nudge is produced. Give the pool real headroom (well under Postgres max_connections).
        kwargs["pool_size"] = 20
        kwargs["max_overflow"] = 40
        kwargs["pool_recycle"] = 1800
    engine = create_engine(url, **kwargs)
    if engine.dialect.name == "sqlite":
        # SQLite ignores foreign keys unless asked, and cascading deletes depend on them.
        @event.listens_for(engine, "connect")
        def _fk_on(dbapi_conn, _record):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

    return engine


@lru_cache
def session_factory(url: str) -> sessionmaker[Session]:
    return sessionmaker(bind=make_engine(url), expire_on_commit=False)


def session_scope(url: str) -> Iterator[Session]:
    with session_factory(url)() as session:
        yield session
