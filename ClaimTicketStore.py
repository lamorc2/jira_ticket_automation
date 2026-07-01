import sqlite3
from pathlib import Path


class ClaimTicketStore:
    def __init__(self, db_path: str = "jira_analyzer.sqlite3") -> None:
        self.db_path = Path(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ticket_claims (
                    issue_key TEXT PRIMARY KEY,
                    status TEXT NOT NULL DEFAULT 'processing',
                    claimed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    finished_at TEXT,
                    error TEXT
                )
                """
            )
    def claim_ticket(self, issue_key: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO ticket_claims (issue_key, status)
                VALUES (?, 'processing')
                """,
                (issue_key,),
            )

        return cursor.rowcount == 1

    def mark_completed(self, issue_key: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE ticket_claims
                SET status = 'completed',
                    finished_at = CURRENT_TIMESTAMP,
                    error = NULL
                WHERE issue_key = ?
                """,
                (issue_key,),
            )

    def mark_failed(self, issue_key: str, error: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE ticket_claims
                SET status = 'failed',
                    finished_at = CURRENT_TIMESTAMP,
                    error = ?
                WHERE issue_key = ?
                """,
                (error[:1000], issue_key),
            )
    def get_claim(self, issue_key: str) -> dict[str, str | None] | None:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT issue_key, status, claimed_at, finished_at, error
                FROM ticket_claims
                WHERE issue_key = ?
                """,
                (issue_key,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return {
            "issue_key": row[0],
            "status": row[1],
            "claimed_at": row[2],
            "finished_at": row[3],
            "error": row[4],
        }


    def reset_failed_claim(self, issue_key: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                DELETE FROM ticket_claims
                WHERE issue_key = ?
                  AND status = 'failed'
                """,
                (issue_key,),
            )

        return cursor.rowcount == 1





    