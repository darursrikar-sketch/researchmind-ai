import json
import sqlite3
import time
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path

from researchmind.config import DB_PATH
from researchmind.paper_loader import PaperMetadata
from researchmind.core.agent import PaperAnalysisResult


class Storage:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at REAL
                );

                CREATE TABLE IF NOT EXISTS papers (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    authors TEXT,
                    abstract TEXT,
                    published TEXT,
                    arxiv_id TEXT,
                    pdf_path TEXT,
                    num_pages INTEGER,
                    word_count INTEGER,
                    data_json TEXT,
                    created_at REAL,
                    user_id TEXT
                );

                CREATE TABLE IF NOT EXISTS analyses (
                    paper_id TEXT PRIMARY KEY,
                    paper_title TEXT NOT NULL,
                    model_used TEXT,
                    data_json TEXT,
                    timestamp REAL,
                    user_id TEXT,
                    FOREIGN KEY (paper_id) REFERENCES papers (id) ON DELETE CASCADE
                );
                """
            )
            # Automatic schema migration for existing databases
            cursor = conn.execute("PRAGMA table_info(papers)")
            columns = [row["name"] for row in cursor.fetchall()]
            if "user_id" not in columns:
                conn.execute("ALTER TABLE papers ADD COLUMN user_id TEXT")

            cursor = conn.execute("PRAGMA table_info(analyses)")
            columns = [row["name"] for row in cursor.fetchall()]
            if "user_id" not in columns:
                conn.execute("ALTER TABLE analyses ADD COLUMN user_id TEXT")

    # ==================== User Operations ====================

    def create_user(self, username: str, email: str, password_hash: str) -> Dict[str, Any]:
        user_id = str(uuid.uuid4())
        created_at = time.time()
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO users (id, username, email, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, username.strip(), email.strip().lower(), password_hash, created_at),
            )
        return {
            "id": user_id,
            "username": username.strip(),
            "email": email.strip().lower(),
            "created_at": created_at,
        }

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT id, username, email, password_hash, created_at FROM users WHERE id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def get_user_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        clean_id = identifier.strip().lower()
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                SELECT id, username, email, password_hash, created_at 
                FROM users 
                WHERE LOWER(email) = ? OR LOWER(username) = ?
                """,
                (clean_id, clean_id),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    # ==================== Paper Operations ====================

    def save_paper(self, paper: PaperMetadata, user_id: Optional[str] = None):
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO papers 
                (id, title, authors, abstract, published, arxiv_id, pdf_path, num_pages, word_count, data_json, created_at, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    paper.id,
                    paper.title,
                    json.dumps(paper.authors),
                    paper.abstract,
                    paper.published,
                    paper.arxiv_id,
                    paper.pdf_path,
                    paper.num_pages,
                    paper.word_count,
                    json.dumps(paper.to_dict()),
                    time.time(),
                    user_id,
                ),
            )

    def get_paper(self, paper_id: str, user_id: Optional[str] = None) -> Optional[PaperMetadata]:
        with self._get_conn() as conn:
            if user_id:
                cursor = conn.execute(
                    "SELECT data_json FROM papers WHERE id = ? AND (user_id = ? OR user_id IS NULL)",
                    (paper_id, user_id),
                )
            else:
                cursor = conn.execute("SELECT data_json FROM papers WHERE id = ?", (paper_id,))
            row = cursor.fetchone()
            if row and row["data_json"]:
                data = json.loads(row["data_json"])
                return PaperMetadata.from_dict(data)
        return None

    def list_papers(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            if user_id:
                cursor = conn.execute(
                    """
                    SELECT id, title, authors, published, arxiv_id, num_pages, word_count, created_at, user_id
                    FROM papers WHERE user_id = ? OR user_id IS NULL ORDER BY created_at DESC
                    """,
                    (user_id,),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT id, title, authors, published, arxiv_id, num_pages, word_count, created_at, user_id
                    FROM papers ORDER BY created_at DESC
                    """
                )
            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "id": row["id"],
                        "title": row["title"],
                        "authors": json.loads(row["authors"]) if row["authors"] else [],
                        "published": row["published"],
                        "arxiv_id": row["arxiv_id"],
                        "num_pages": row["num_pages"],
                        "word_count": row["word_count"],
                        "created_at": row["created_at"],
                        "user_id": row["user_id"],
                    }
                )
            return results

    def delete_paper(self, paper_id: str, user_id: Optional[str] = None):
        with self._get_conn() as conn:
            if user_id:
                conn.execute("DELETE FROM analyses WHERE paper_id = ? AND (user_id = ? OR user_id IS NULL)", (paper_id, user_id))
                conn.execute("DELETE FROM papers WHERE id = ? AND (user_id = ? OR user_id IS NULL)", (paper_id, user_id))
            else:
                conn.execute("DELETE FROM analyses WHERE paper_id = ?", (paper_id,))
                conn.execute("DELETE FROM papers WHERE id = ?", (paper_id,))

    def save_analysis(self, analysis: PaperAnalysisResult, user_id: Optional[str] = None):
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO analyses 
                (paper_id, paper_title, model_used, data_json, timestamp, user_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis.paper_id,
                    analysis.paper_title,
                    analysis.model_used,
                    json.dumps(analysis.to_dict()),
                    analysis.timestamp,
                    user_id,
                ),
            )

    def get_analysis(self, paper_id: str, user_id: Optional[str] = None) -> Optional[PaperAnalysisResult]:
        with self._get_conn() as conn:
            if user_id:
                cursor = conn.execute(
                    "SELECT data_json FROM analyses WHERE paper_id = ? AND (user_id = ? OR user_id IS NULL)",
                    (paper_id, user_id),
                )
            else:
                cursor = conn.execute("SELECT data_json FROM analyses WHERE paper_id = ?", (paper_id,))
            row = cursor.fetchone()
            if row and row["data_json"]:
                data = json.loads(row["data_json"])
                return PaperAnalysisResult.from_dict(data)
        return None

    def list_analyses(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            if user_id:
                cursor = conn.execute(
                    """
                    SELECT paper_id, paper_title, model_used, timestamp, user_id
                    FROM analyses WHERE user_id = ? OR user_id IS NULL ORDER BY timestamp DESC
                    """,
                    (user_id,),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT paper_id, paper_title, model_used, timestamp, user_id
                    FROM analyses ORDER BY timestamp DESC
                    """
                )
            return [dict(row) for row in cursor.fetchall()]


# Global storage instance
storage = Storage()
