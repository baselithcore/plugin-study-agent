"""Persistence layer for the Study Assistant Plugin."""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, AsyncIterator
from urllib.parse import quote_plus

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from core.config import get_storage_config
from core.context import resolve_plugin_tenant_key
from core.observability.logging import get_logger

logger = get_logger(__name__)
_storage_config = get_storage_config()
_POOL: AsyncConnectionPool | None = None

_PLUGIN_NAME = "study-agent"


def _tenant() -> str:
    """Resolve the current caller's storage scope for this plugin.

    Declared ``tenancy: personal`` in manifest.yaml — each authenticated user
    gets their own private subjects/documents/flashcards/sessions/podcasts,
    even on a deployment shared with other users. See
    core.context.resolve_plugin_tenant_key and the multi-tenancy docs.
    """
    return resolve_plugin_tenant_key(_PLUGIN_NAME, "personal")


def get_conninfo() -> str:
    """Build connection string reusing core credentials."""
    user = quote_plus(_storage_config.db_user or "")
    password = (
        quote_plus(_storage_config.db_password) if _storage_config.db_password else ""
    )
    password_fragment = f":{password}" if password else ""
    host = _storage_config.db_host or "localhost"
    port = _storage_config.db_port or 5432
    dbname = _storage_config.db_name

    return f"postgresql://{user}{password_fragment}@{host}:{port}/{dbname}"


async def init_pool():
    """Initialize the database connection pool."""
    global _POOL
    if _POOL is None:
        try:
            if _storage_config.postgres_enabled:
                _POOL = AsyncConnectionPool(
                    conninfo=_storage_config.conninfo,
                    min_size=1,
                    max_size=5,
                    timeout=30.0,
                    kwargs={"autocommit": True},
                    open=False,
                )
                await _POOL.open()
                logger.info("Study Agent Plugin: DB pool initialized")
            else:
                logger.warning("PostgreSQL disabled, persistence will not work.")
        except Exception as e:
            logger.error(f"Failed to initialize study pool: {e}")
            raise


async def close_pool():
    """Close the database connection pool."""
    global _POOL
    if _POOL is not None:
        await _POOL.close()
        _POOL = None
        logger.info("Study Agent Plugin: DB pool closed")


@asynccontextmanager
async def get_connection() -> AsyncIterator[AsyncConnection[object]]:
    """Yields a connection from the pool."""
    if _POOL is None:
        await init_pool()

    if _POOL is None:
        raise RuntimeError("Failed to initialize database pool")

    async with _POOL.connection() as conn:
        yield conn


async def ensure_schema():
    """Create study agent schemas."""
    if not _storage_config.postgres_enabled:
        return

    try:
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                # 1. Subjects table
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS study_subjects (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        deconstructed_data JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
                await cur.execute("""
                    ALTER TABLE study_subjects ADD COLUMN IF NOT EXISTS deconstructed_data JSONB;
                """)
                await cur.execute("""
                    ALTER TABLE study_subjects ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';
                """)
                await cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_study_subjects_tenant ON study_subjects(tenant_id);
                """)
                # 1.5. Folders table
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS study_folders (
                        id SERIAL PRIMARY KEY,
                        subject_id INTEGER REFERENCES study_subjects(id) ON DELETE CASCADE,
                        name TEXT NOT NULL,
                        parent_id INTEGER REFERENCES study_folders(id) ON DELETE CASCADE,
                        tenant_id TEXT NOT NULL DEFAULT 'default',
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
                await cur.execute("""
                    ALTER TABLE study_folders ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';
                """)
                await cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_study_folders_tenant ON study_folders(tenant_id);
                """)
                # 2. Documents/materials table
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS study_documents (
                        id SERIAL PRIMARY KEY,
                        subject_id INTEGER REFERENCES study_subjects(id) ON DELETE CASCADE,
                        folder_id INTEGER REFERENCES study_folders(id) ON DELETE SET NULL,
                        name TEXT NOT NULL,
                        file_path TEXT,
                        file_type TEXT,
                        raw_text TEXT,
                        tenant_id TEXT NOT NULL DEFAULT 'default',
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
                await cur.execute("""
                    ALTER TABLE study_documents ADD COLUMN IF NOT EXISTS folder_id INTEGER REFERENCES study_folders(id) ON DELETE SET NULL;
                """)
                await cur.execute("""
                    ALTER TABLE study_documents ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';
                """)
                await cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_study_documents_tenant ON study_documents(tenant_id);
                """)
                # 3. Flashcards table with SM2 parameters
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS study_flashcards (
                        id SERIAL PRIMARY KEY,
                        subject_id INTEGER REFERENCES study_subjects(id) ON DELETE CASCADE,
                        question TEXT NOT NULL,
                        answer TEXT NOT NULL,
                        ease_factor DOUBLE PRECISION DEFAULT 2.5,
                        interval_days INTEGER DEFAULT 0,
                        repetitions INTEGER DEFAULT 0,
                        next_review TIMESTAMPTZ DEFAULT NOW(),
                        tenant_id TEXT NOT NULL DEFAULT 'default',
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
                await cur.execute("""
                    ALTER TABLE study_flashcards ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';
                """)
                await cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_study_flashcards_tenant ON study_flashcards(tenant_id);
                """)
                # 4. Sessions table (oral simulation or exercise helping)
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS study_sessions (
                        id SERIAL PRIMARY KEY,
                        subject_id INTEGER REFERENCES study_subjects(id) ON DELETE CASCADE,
                        professor_name TEXT NOT NULL,
                        strictness TEXT NOT NULL,
                        difficulty_level INTEGER NOT NULL,
                        score DOUBLE PRECISION,
                        status TEXT DEFAULT 'active',
                        transcript JSONB DEFAULT '[]'::jsonb,
                        current_topic TEXT,
                        tenant_id TEXT NOT NULL DEFAULT 'default',
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
                await cur.execute("""
                    ALTER TABLE study_sessions ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';
                """)
                await cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_study_sessions_tenant ON study_sessions(tenant_id);
                """)
                # 5. Podcasts table
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS study_podcasts (
                        id SERIAL PRIMARY KEY,
                        subject_id INTEGER REFERENCES study_subjects(id) ON DELETE CASCADE,
                        title TEXT NOT NULL,
                        topic TEXT NOT NULL,
                        professor_voice TEXT NOT NULL,
                        professor_name TEXT DEFAULT 'Professore',
                        depth_level TEXT NOT NULL,
                        tenant_id TEXT NOT NULL DEFAULT 'default',
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
                await cur.execute("""
                    ALTER TABLE study_podcasts ADD COLUMN IF NOT EXISTS professor_name TEXT DEFAULT 'Professore';
                """)
                await cur.execute("""
                    ALTER TABLE study_podcasts ADD COLUMN IF NOT EXISTS tenant_id TEXT NOT NULL DEFAULT 'default';
                """)
                await cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_study_podcasts_tenant ON study_podcasts(tenant_id);
                """)
                # 6. Podcast episodes table
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS study_podcast_episodes (
                        id SERIAL PRIMARY KEY,
                        podcast_id INTEGER REFERENCES study_podcasts(id) ON DELETE CASCADE,
                        episode_number INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        script_text TEXT NOT NULL,
                        audio_filename TEXT NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
        logger.info("Study Agent Plugin: Schemas verified and ensured")
    except Exception as e:
        logger.error(f"Study Agent Plugin: Schema initialization failed: {e}")
        raise


class StudyDAO:
    """Data Access Object for all study agent tables."""

    @staticmethod
    async def create_subject(name: str, description: str | None) -> int:
        """Create a new studying course."""
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO study_subjects (name, description, tenant_id) VALUES (%s, %s, %s) RETURNING id",
                    (name, description, _tenant()),
                )
                row = await cur.fetchone()
                return row[0] if row else -1

    @staticmethod
    async def get_subjects() -> list[dict[str, Any]]:
        """Retrieve all courses owned by the current tenant."""
        async with get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    "SELECT id, name, description, deconstructed_data, created_at FROM study_subjects WHERE tenant_id = %s ORDER BY name",
                    (_tenant(),),
                )
                return await cur.fetchall()

    @staticmethod
    async def delete_subject(subject_id: int) -> bool:
        """Delete a course owned by the current tenant."""
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM study_subjects WHERE id = %s AND tenant_id = %s",
                    (subject_id, _tenant()),
                )
                return cur.rowcount > 0

    @staticmethod
    async def add_document(
        subject_id: int,
        name: str,
        file_path: str,
        file_type: str,
        raw_text: str,
        folder_id: int | None = None,
    ) -> int:
        """Upload/Save notes or slides material."""
        tenant_id = _tenant()
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO study_documents (subject_id, folder_id, name, file_path, file_type, raw_text, tenant_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                    """,
                    (
                        subject_id,
                        folder_id,
                        name,
                        file_path,
                        file_type,
                        raw_text,
                        tenant_id,
                    ),
                )
                row = await cur.fetchone()
                doc_id = row[0] if row else -1
                if doc_id != -1:
                    await cur.execute(
                        "UPDATE study_subjects SET deconstructed_data = NULL WHERE id = %s AND tenant_id = %s",
                        (subject_id, tenant_id),
                    )
                return doc_id

    @staticmethod
    async def get_documents(subject_id: int) -> list[dict[str, Any]]:
        """List documents in a subject owned by the current tenant."""
        async with get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    "SELECT id, subject_id, folder_id, name, file_path, file_type, created_at FROM study_documents WHERE subject_id = %s AND tenant_id = %s",
                    (subject_id, _tenant()),
                )
                return await cur.fetchall()

    @staticmethod
    async def get_document(doc_id: int) -> dict[str, Any] | None:
        """Get document contents, scoped to the current tenant."""
        async with get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    "SELECT id, subject_id, name, file_path, file_type, raw_text, created_at FROM study_documents WHERE id = %s AND tenant_id = %s",
                    (doc_id, _tenant()),
                )
                return await cur.fetchone()

    @staticmethod
    async def delete_document(doc_id: int) -> bool:
        """Delete document and invalidate deconstructed cache."""
        tenant_id = _tenant()
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT subject_id FROM study_documents WHERE id = %s AND tenant_id = %s",
                    (doc_id, tenant_id),
                )
                row = await cur.fetchone()
                if row:
                    subject_id = row[0]
                    await cur.execute(
                        "DELETE FROM study_documents WHERE id = %s AND tenant_id = %s",
                        (doc_id, tenant_id),
                    )
                    await cur.execute(
                        "UPDATE study_subjects SET deconstructed_data = NULL WHERE id = %s AND tenant_id = %s",
                        (subject_id, tenant_id),
                    )
                    return cur.rowcount > 0
                return False

    @staticmethod
    async def create_folder(
        subject_id: int, name: str, parent_id: int | None = None
    ) -> int:
        """Create a new folder."""
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO study_folders (subject_id, name, parent_id, tenant_id) VALUES (%s, %s, %s, %s) RETURNING id",
                    (subject_id, name, parent_id, _tenant()),
                )
                row = await cur.fetchone()
                return row[0] if row else -1

    @staticmethod
    async def get_folders(subject_id: int) -> list[dict[str, Any]]:
        """Get all folders for a subject owned by the current tenant."""
        async with get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    "SELECT id, subject_id, name, parent_id, created_at FROM study_folders WHERE subject_id = %s AND tenant_id = %s ORDER BY name",
                    (subject_id, _tenant()),
                )
                return await cur.fetchall()

    @staticmethod
    async def delete_folder(folder_id: int) -> bool:
        """Delete a folder and cascade (handled by DB cascade constraint)."""
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM study_folders WHERE id = %s AND tenant_id = %s",
                    (folder_id, _tenant()),
                )
                return cur.rowcount > 0

    @staticmethod
    async def rename_folder(folder_id: int, name: str) -> bool:
        """Rename a folder."""
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE study_folders SET name = %s WHERE id = %s AND tenant_id = %s",
                    (name, folder_id, _tenant()),
                )
                return cur.rowcount > 0

    @staticmethod
    async def rename_document(doc_id: int, name: str) -> bool:
        """Rename a document."""
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE study_documents SET name = %s WHERE id = %s AND tenant_id = %s",
                    (name, doc_id, _tenant()),
                )
                return cur.rowcount > 0

    @staticmethod
    async def move_document(doc_id: int, folder_id: int | None) -> bool:
        """Move a document to a new folder (or root if None)."""
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE study_documents SET folder_id = %s WHERE id = %s AND tenant_id = %s",
                    (folder_id, doc_id, _tenant()),
                )
                return cur.rowcount > 0

    @staticmethod
    async def move_folder(folder_id: int, parent_id: int | None) -> bool:
        """Move a folder to a new parent folder (or root if None)."""
        tenant_id = _tenant()
        # Prevent moving a folder into its own descendants or itself
        if parent_id is not None:
            if folder_id == parent_id:
                return False
            # Check cycle: traverse parents of parent_id
            curr_parent = parent_id
            async with get_connection() as conn:
                async with conn.cursor() as cur:
                    while curr_parent is not None:
                        await cur.execute(
                            "SELECT parent_id FROM study_folders WHERE id = %s AND tenant_id = %s",
                            (curr_parent, tenant_id),
                        )
                        row = await cur.fetchone()
                        if row:
                            curr_parent = row[0]
                            if curr_parent == folder_id:
                                return False  # Cycle detected!
                        else:
                            break

        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE study_folders SET parent_id = %s WHERE id = %s AND tenant_id = %s",
                    (parent_id, folder_id, tenant_id),
                )
                return cur.rowcount > 0

    @staticmethod
    async def update_deconstructed_data(subject_id: int, data: dict[str, Any]) -> None:
        """Save cached deconstructed data."""
        import json

        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE study_subjects SET deconstructed_data = %s WHERE id = %s AND tenant_id = %s",
                    (json.dumps(data), subject_id, _tenant()),
                )

    @staticmethod
    async def create_flashcards(subject_id: int, cards: list[tuple[str, str]]) -> None:
        """Insert flashcards in batch."""
        tenant_id = _tenant()
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                async with conn.transaction():
                    for q, a in cards:
                        await cur.execute(
                            "INSERT INTO study_flashcards (subject_id, question, answer, tenant_id) VALUES (%s, %s, %s, %s)",
                            (subject_id, q, a, tenant_id),
                        )

    @staticmethod
    async def get_flashcards(
        subject_id: int, due_only: bool = False
    ) -> list[dict[str, Any]]:
        """Retrieve flashcards for a subject owned by the current tenant."""
        query = "SELECT id, subject_id, question, answer, ease_factor, interval_days, repetitions, next_review FROM study_flashcards WHERE subject_id = %s AND tenant_id = %s"
        params = [subject_id, _tenant()]
        if due_only:
            query += " AND next_review <= NOW()"

        async with get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, params)
                return await cur.fetchall()

    @staticmethod
    async def get_flashcard_count_stats(subject_id: int) -> dict[str, int]:
        """Get due, new, and total flashcard counts."""
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT COUNT(*), COUNT(CASE WHEN next_review <= NOW() THEN 1 END), COUNT(CASE WHEN repetitions = 0 THEN 1 END) FROM study_flashcards WHERE subject_id = %s AND tenant_id = %s",
                    (subject_id, _tenant()),
                )
                row = await cur.fetchone()
                if row:
                    return {"total": row[0], "due": row[1], "new": row[2]}
                return {"total": 0, "due": 0, "new": 0}

    @staticmethod
    async def update_flashcard_sm2(card_id: int, rating: int) -> dict[str, Any]:
        """Update flashcard using SuperMemo-2 Spaced Repetition Algorithm."""
        tenant_id = _tenant()
        async with get_connection() as conn:
            async with conn.transaction(), conn.cursor(row_factory=dict_row) as cur:
                # FOR UPDATE locks the row for the duration of the transaction so a
                # concurrent review of the same card (double-click, two open tabs)
                # blocks instead of racing on this read-modify-write.
                await cur.execute(
                    "SELECT id, ease_factor, interval_days, repetitions FROM study_flashcards WHERE id = %s AND tenant_id = %s FOR UPDATE",
                    (card_id, tenant_id),
                )
                card = await cur.fetchone()
                if not card:
                    raise ValueError(f"Flashcard {card_id} not found")

                ef = card["ease_factor"]
                interval = card["interval_days"]
                repetitions = card["repetitions"]

                # SuperMemo-2 logic
                if rating >= 3:
                    if repetitions == 0:
                        interval = 1
                    elif repetitions == 1:
                        interval = 6
                    else:
                        interval = round(interval * ef)
                    repetitions += 1
                else:
                    repetitions = 0
                    interval = 1

                # Ease Factor adjustments
                ef = ef + (0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02))
                if ef < 1.3:
                    ef = 1.3

                next_review = datetime.now() + timedelta(days=interval)

                await cur.execute(
                    """
                    UPDATE study_flashcards
                    SET ease_factor = %s, interval_days = %s, repetitions = %s, next_review = %s
                    WHERE id = %s AND tenant_id = %s
                    """,
                    (ef, interval, repetitions, next_review, card_id, tenant_id),
                )

                return {
                    "id": card_id,
                    "ease_factor": ef,
                    "interval_days": interval,
                    "repetitions": repetitions,
                    "next_review": next_review,
                }

    @staticmethod
    async def create_session(
        subject_id: int, professor_name: str, strictness: str, difficulty_level: int
    ) -> int:
        """Create a new oral simulation session."""
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO study_sessions (subject_id, professor_name, strictness, difficulty_level, transcript, tenant_id)
                    VALUES (%s, %s, %s, %s, '[]'::jsonb, %s) RETURNING id
                    """,
                    (
                        subject_id,
                        professor_name,
                        strictness,
                        difficulty_level,
                        _tenant(),
                    ),
                )
                row = await cur.fetchone()
                return row[0] if row else -1

    @staticmethod
    async def get_session(session_id: int) -> dict[str, Any] | None:
        """Retrieve oral session status and transcript, scoped to the current tenant."""
        async with get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT s.id, s.subject_id, s.professor_name, s.strictness, s.difficulty_level,
                           s.score, s.status, s.transcript, s.current_topic, s.created_at, sub.name as subject_name
                    FROM study_sessions s
                    JOIN study_subjects sub ON s.subject_id = sub.id
                    WHERE s.id = %s AND s.tenant_id = %s
                    """,
                    (session_id, _tenant()),
                )
                return await cur.fetchone()

    @staticmethod
    async def update_session(
        session_id: int,
        score: float | None,
        status: str,
        transcript: list[dict[str, Any]],
        current_topic: str | None,
    ) -> bool:
        """Update interrogation state."""
        import json

        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE study_sessions
                    SET score = %s, status = %s, transcript = %s, current_topic = %s
                    WHERE id = %s AND tenant_id = %s
                    """,
                    (
                        score,
                        status,
                        json.dumps(transcript),
                        current_topic,
                        session_id,
                        _tenant(),
                    ),
                )
                return cur.rowcount > 0

    @staticmethod
    async def get_sessions(subject_id: int) -> list[dict[str, Any]]:
        """Get all sessions for a course owned by the current tenant."""
        async with get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    "SELECT id, professor_name, strictness, difficulty_level, score, status, current_topic, created_at FROM study_sessions WHERE subject_id = %s AND tenant_id = %s ORDER BY created_at DESC",
                    (subject_id, _tenant()),
                )
                return await cur.fetchall()

    @staticmethod
    async def create_podcast(
        subject_id: int,
        title: str,
        topic: str,
        professor_voice: str,
        professor_name: str,
        depth_level: str,
    ) -> int:
        """Create a new podcast entry."""
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO study_podcasts (subject_id, title, topic, professor_voice, professor_name, depth_level, tenant_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                    """,
                    (
                        subject_id,
                        title,
                        topic,
                        professor_voice,
                        professor_name,
                        depth_level,
                        _tenant(),
                    ),
                )
                row = await cur.fetchone()
                return row[0] if row else -1

    @staticmethod
    async def create_podcast_episode(
        podcast_id: int,
        episode_number: int,
        title: str,
        script_text: str,
        audio_filename: str,
    ) -> int:
        """Create a new podcast episode entry.

        podcast_id is scoped implicitly: the FK only resolves to a real row
        when it belongs to the current tenant (see get_podcasts/delete_podcast),
        and the episodes table has no independent tenant_id of its own.
        """
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO study_podcast_episodes (podcast_id, episode_number, title, script_text, audio_filename)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                    """,
                    (podcast_id, episode_number, title, script_text, audio_filename),
                )
                row = await cur.fetchone()
                return row[0] if row else -1

    @staticmethod
    async def get_podcasts(subject_id: int) -> list[dict[str, Any]]:
        """Get all podcasts generated for a subject owned by the current tenant."""
        async with get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    "SELECT id, subject_id, title, topic, professor_voice, professor_name, depth_level, created_at FROM study_podcasts WHERE subject_id = %s AND tenant_id = %s ORDER BY created_at DESC",
                    (subject_id, _tenant()),
                )
                return await cur.fetchall()

    @staticmethod
    async def get_podcast_episodes(podcast_id: int) -> list[dict[str, Any]]:
        """Get all episodes for a generated podcast owned by the current tenant."""
        async with get_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT e.id, e.podcast_id, e.episode_number, e.title, e.script_text, e.audio_filename, e.created_at
                    FROM study_podcast_episodes e
                    JOIN study_podcasts p ON e.podcast_id = p.id
                    WHERE e.podcast_id = %s AND p.tenant_id = %s
                    ORDER BY e.episode_number ASC
                    """,
                    (podcast_id, _tenant()),
                )
                return await cur.fetchall()

    @staticmethod
    async def delete_podcast(podcast_id: int) -> bool:
        """Delete a podcast owned by the current tenant (cascades to episodes)."""
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM study_podcasts WHERE id = %s AND tenant_id = %s",
                    (podcast_id, _tenant()),
                )
                return cur.rowcount > 0
