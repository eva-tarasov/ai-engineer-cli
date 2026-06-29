import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

from ai_engineer_cli.agent.conversation_config import ConversationConfig
from ai_engineer_cli.agent.message import Message


class MessageStore:
    """
    JSON-based conversation storage.

    One file stores one conversation:
    - config
    - summary
    - facts
    - messages
    - branches
    """

    def __init__(
            self,
            conversation_id: str,
            db_path: str = ".agent_data/agent.sqlite3",
    ) -> None:
        self.conversation_id = conversation_id
        self.db_path = Path(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row

        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    config_json TEXT NOT NULL,
                    summary TEXT,
                    facts_json TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS branches (
                    conversation_id TEXT NOT NULL,
                    branch_id TEXT NOT NULL,
                    parent_branch_id TEXT,
                    checkpoint_message_index INTEGER,
                    PRIMARY KEY (conversation_id, branch_id)
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    branch_id TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(conversation_id, branch_id, position)
                )
                """
            )

    def _ensure_conversation_exists(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO conversations (
                    conversation_id,
                    config_json,
                    summary,
                    facts_json
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    self.conversation_id,
                    json.dumps(ConversationConfig().to_dict(), ensure_ascii=False),
                    None,
                    json.dumps({}, ensure_ascii=False),
                ),
            )

            connection.execute(
                """
                INSERT OR IGNORE INTO branches (
                    conversation_id,
                    branch_id,
                    parent_branch_id,
                    checkpoint_message_index
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    self.conversation_id,
                    "main",
                    None,
                    0,
                ),
            )

    def exists(self) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM conversations
                WHERE conversation_id = ?
                """,
                (self.conversation_id,),
            ).fetchone()

        return row is not None

    def load_config(self) -> ConversationConfig:
        self._ensure_conversation_exists()

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT config_json
                FROM conversations
                WHERE conversation_id = ?
                """,
                (self.conversation_id,),
            ).fetchone()

        if row is None:
            return ConversationConfig()

        return ConversationConfig.from_dict(json.loads(row["config_json"]))

    def save_config(self, config: ConversationConfig) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO conversations (
                    conversation_id,
                    config_json,
                    summary,
                    facts_json
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(conversation_id) DO UPDATE SET
                    config_json = excluded.config_json
                """,
                (
                    self.conversation_id,
                    json.dumps(config.to_dict(), ensure_ascii=False),
                    None,
                    json.dumps({}, ensure_ascii=False),
                ),
            )

            connection.execute(
                """
                INSERT OR IGNORE INTO branches (
                    conversation_id,
                    branch_id,
                    parent_branch_id,
                    checkpoint_message_index
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    self.conversation_id,
                    "main",
                    None,
                    0,
                ),
            )

    def load_messages(self) -> list[Message]:
        return self.load_branch_messages("main")

    def save_messages(self, messages: list[Message]) -> None:
        self.save_branch_messages("main", messages)

    def load_summary(self) -> str | None:
        self._ensure_conversation_exists()

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT summary
                FROM conversations
                WHERE conversation_id = ?
                """,
                (self.conversation_id,),
            ).fetchone()

        if row is None:
            return None

        return row["summary"] or None

    def save_summary(self, summary: str | None) -> None:
        self._ensure_conversation_exists()

        with self._connect() as connection:
            connection.execute(
                """
                UPDATE conversations
                SET summary = ?
                WHERE conversation_id = ?
                """,
                (
                    summary,
                    self.conversation_id,
                ),
            )

    def load_facts(self) -> dict[str, str]:
        self._ensure_conversation_exists()

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT facts_json
                FROM conversations
                WHERE conversation_id = ?
                """,
                (self.conversation_id,),
            ).fetchone()

        if row is None:
            return {}

        facts = json.loads(row["facts_json"])
        return facts if isinstance(facts, dict) else {}

    def save_facts(self, facts: dict[str, str]) -> None:
        self._ensure_conversation_exists()

        with self._connect() as connection:
            connection.execute(
                """
                UPDATE conversations
                SET facts_json = ?
                WHERE conversation_id = ?
                """,
                (
                    json.dumps(facts, ensure_ascii=False),
                    self.conversation_id,
                ),
            )

    def load_branch_messages(self, branch_id: str) -> list[Message]:
        self._ensure_conversation_exists()

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content
                FROM messages
                WHERE conversation_id = ?
                  AND branch_id = ?
                ORDER BY position ASC
                """,
                (
                    self.conversation_id,
                    branch_id,
                ),
            ).fetchall()

        return [
            Message(role=row["role"], content=row["content"])
            for row in rows
        ]

    def save_branch_messages(self, branch_id: str, messages: list[Message]) -> None:
        self._ensure_conversation_exists()

        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO branches (
                    conversation_id,
                    branch_id,
                    parent_branch_id,
                    checkpoint_message_index
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    self.conversation_id,
                    branch_id,
                    None,
                    0,
                ),
            )

            connection.execute(
                """
                DELETE FROM messages
                WHERE conversation_id = ?
                  AND branch_id = ?
                """,
                (
                    self.conversation_id,
                    branch_id,
                ),
            )

            for position, message in enumerate(messages):
                connection.execute(
                    """
                    INSERT INTO messages (
                        conversation_id,
                        branch_id,
                        position,
                        role,
                        content,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        self.conversation_id,
                        branch_id,
                        position,
                        message.role,
                        message.content,
                        now,
                    ),
                )

    def create_branch(
            self,
            branch_id: str,
            from_branch_id: str = "main",
    ) -> None:
        self._ensure_conversation_exists()

        with self._connect() as connection:
            existing_branch = connection.execute(
                """
                SELECT 1
                FROM branches
                WHERE conversation_id = ?
                  AND branch_id = ?
                """,
                (
                    self.conversation_id,
                    branch_id,
                ),
            ).fetchone()

            if existing_branch is not None:
                raise ValueError(f"Branch already exists: {branch_id}")

            source_branch = connection.execute(
                """
                SELECT 1
                FROM branches
                WHERE conversation_id = ?
                  AND branch_id = ?
                """,
                (
                    self.conversation_id,
                    from_branch_id,
                ),
            ).fetchone()

            if source_branch is None:
                raise ValueError(f"Source branch does not exist: {from_branch_id}")

            source_messages = connection.execute(
                """
                SELECT role, content
                FROM messages
                WHERE conversation_id = ?
                  AND branch_id = ?
                ORDER BY position ASC
                """,
                (
                    self.conversation_id,
                    from_branch_id,
                ),
            ).fetchall()

            connection.execute(
                """
                INSERT INTO branches (
                    conversation_id,
                    branch_id,
                    parent_branch_id,
                    checkpoint_message_index
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    self.conversation_id,
                    branch_id,
                    from_branch_id,
                    len(source_messages),
                ),
            )

            now = datetime.now(timezone.utc).isoformat()

            for position, row in enumerate(source_messages):
                connection.execute(
                    """
                    INSERT INTO messages (
                        conversation_id,
                        branch_id,
                        position,
                        role,
                        content,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        self.conversation_id,
                        branch_id,
                        position,
                        row["role"],
                        row["content"],
                        now,
                    ),
                )

    def list_branches(self) -> list[str]:
        self._ensure_conversation_exists()

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT branch_id
                FROM branches
                WHERE conversation_id = ?
                ORDER BY branch_id ASC
                """,
                (self.conversation_id,),
            ).fetchall()

        return [row["branch_id"] for row in rows]

    def clear(self) -> None:
        """
        Clear runtime state but preserve conversation config.
        """
        self._ensure_conversation_exists()

        with self._connect() as connection:
            connection.execute(
                """
                UPDATE conversations
                SET summary = ?,
                    facts_json = ?
                WHERE conversation_id = ?
                """,
                (
                    None,
                    json.dumps({}, ensure_ascii=False),
                    self.conversation_id,
                ),
            )

            connection.execute(
                """
                DELETE FROM messages
                WHERE conversation_id = ?
                """,
                (self.conversation_id,),
            )

            connection.execute(
                """
                DELETE FROM branches
                WHERE conversation_id = ?
                """,
                (self.conversation_id,),
            )

            connection.execute(
                """
                INSERT INTO branches (
                    conversation_id,
                    branch_id,
                    parent_branch_id,
                    checkpoint_message_index
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    self.conversation_id,
                    "main",
                    None,
                    0,
                ),
            )

    def delete(self) -> None:
        """
        Delete the whole conversation, including config, summary, facts, branches, and messages.
        """
        with self._connect() as connection:
            connection.execute(
                """
                DELETE FROM messages
                WHERE conversation_id = ?
                """,
                (self.conversation_id,),
            )

            connection.execute(
                """
                DELETE FROM branches
                WHERE conversation_id = ?
                """,
                (self.conversation_id,),
            )

            connection.execute(
                """
                DELETE FROM conversations
                WHERE conversation_id = ?
                """,
                (self.conversation_id,),
            )
