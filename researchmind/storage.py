import json
import sqlite3
import time
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
                    created_at REAL
                );

                CREATE TABLE IF NOT EXISTS analyses (
                    paper_id TEXT PRIMARY KEY,
                    paper_title TEXT NOT NULL,
                    model_used TEXT,
                    data_json TEXT,
                    timestamp REAL,
                    FOREIGN KEY (paper_id) REFERENCES papers (id) ON DELETE CASCADE
                );
                """
            )

    def save_paper(self, paper: PaperMetadata):
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO papers 
                (id, title, authors, abstract, published, arxiv_id, pdf_path, num_pages, word_count, data_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                ),
            )

    def get_paper(self, paper_id: str) -> Optional[PaperMetadata]:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT data_json FROM papers WHERE id = ?", (paper_id,))
            row = cursor.fetchone()
            if row and row["data_json"]:
                data = json.loads(row["data_json"])
                return PaperMetadata.from_dict(data)
        return None

    def list_papers(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                SELECT id, title, authors, published, arxiv_id, num_pages, word_count, created_at
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
                    }
                )
            return results

    def delete_paper(self, paper_id: str):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM analyses WHERE paper_id = ?", (paper_id,))
            conn.execute("DELETE FROM papers WHERE id = ?", (paper_id,))

    def save_analysis(self, analysis: PaperAnalysisResult):
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO analyses 
                (paper_id, paper_title, model_used, data_json, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    analysis.paper_id,
                    analysis.paper_title,
                    analysis.model_used,
                    json.dumps(analysis.to_dict()),
                    analysis.timestamp,
                ),
            )

    def get_analysis(self, paper_id: str) -> Optional[PaperAnalysisResult]:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT data_json FROM analyses WHERE paper_id = ?", (paper_id,))
            row = cursor.fetchone()
            if row and row["data_json"]:
                data = json.loads(row["data_json"])
                return PaperAnalysisResult.from_dict(data)
        return None

    def list_analyses(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                SELECT paper_id, paper_title, model_used, timestamp
                FROM analyses ORDER BY timestamp DESC
                """
            )
            return [dict(row) for row in cursor.fetchall()]


# Global storage instance
storage = Storage()

