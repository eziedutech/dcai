"""The privacy claims that the schema itself must enforce (spec sections 9 and 10)."""

import uuid

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import DatabaseError

from app.db.base import Base

# Column names that would mean conversation text is being stored.
_TEXT_LIKE = {"text", "content", "message", "messages", "body", "transcript", "raw", "excerpt"}


def test_no_table_has_a_conversation_text_column(db_url):
    insp = inspect(create_engine(db_url))
    found = [
        (table, col["name"])
        for table in insp.get_table_names()
        for col in insp.get_columns(table)
        if col["name"] in _TEXT_LIKE or col["name"].endswith("_text")
    ]
    assert found == []


def test_only_evidence_excerpt_holds_ciphertext(db_url):
    insp = inspect(create_engine(db_url))
    binary = [
        (t, c["name"])
        for t in insp.get_table_names()
        for c in insp.get_columns(t)
        if "BLOB" in str(c["type"]).upper() or "BYTEA" in str(c["type"]).upper()
    ]
    assert binary == [("evidence_excerpt", "ciphertext")]
    cols = {c["name"] for c in insp.get_columns("evidence_excerpt")}
    assert "expires_at" in cols


def test_migration_matches_models(db_url):
    insp = inspect(create_engine(db_url))
    migrated = set(insp.get_table_names()) - {"alembic_version"}
    assert migrated == set(Base.metadata.tables)
    for name, table in Base.metadata.tables.items():
        assert {c["name"] for c in insp.get_columns(name)} == {c.name for c in table.columns}


def test_consent_record_refuses_update_but_allows_erasure(db_url):
    engine = create_engine(db_url)
    gid, cid, rid = (uuid.uuid4().hex for _ in range(3))
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO guardian (id, email, name, language, password_hash, created_at) "
                "VALUES (:g, 'x@example.com', 'X', 'id', 'h', '2026-10-26 00:00:00')"
            ),
            {"g": gid},
        )
        conn.execute(
            text(
                "INSERT INTO child_profile (id, guardian_id, nickname, age_range, created_at) "
                "VALUES (:c, :g, 'Kit', '10-12', '2026-10-26 00:00:00')"
            ),
            {"c": cid, "g": gid},
        )
        conn.execute(
            text(
                "INSERT INTO consent_record (id, guardian_id, child_id, text_version, action, "
                "scopes, age_range, created_at) VALUES (:r, :g, :c, 'v', 'grant', "
                "'[\"percakapan\"]', '10-12', '2026-10-26 00:00:00')"
            ),
            {"r": rid, "g": gid, "c": cid},
        )

    with pytest.raises(DatabaseError, match="append-only"), engine.begin() as conn:
        conn.execute(text("UPDATE consent_record SET action = 'revoke'"))

    with engine.begin() as conn:
        assert conn.execute(text("SELECT action FROM consent_record")).scalar_one() == "grant"
        conn.execute(text("DELETE FROM consent_record"))
        assert conn.execute(text("SELECT COUNT(*) FROM consent_record")).scalar_one() == 0


def test_unreachable_database_fails_fast_instead_of_hanging():
    import time

    from sqlalchemy.exc import OperationalError

    from app.db.base import make_engine

    # A non-routable address: without a connect timeout this would wait indefinitely.
    engine = make_engine("postgresql://u:p@10.255.255.1:5432/x")
    started = time.monotonic()
    with pytest.raises(OperationalError):
        engine.connect()
    assert time.monotonic() - started < 10
