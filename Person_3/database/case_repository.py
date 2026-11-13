"""
case_repository.py — Case Store Repository with SQLite & JSON Dual Persistence (Unit 1.C)
Provides ACID transaction integrity, indexing, filtering, and JSON fallback compatibility.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .connection import get_db_connection

ROOT = Path(__file__).resolve().parent.parent
CASES_JSON_FILE = ROOT / "database" / "cases.json"


class CaseRepository:
    """Repository handling CRUD operations and queries for dispute cases."""

    def __init__(self) -> None:
        self._seed_from_json_if_empty()

    def _seed_from_json_if_empty(self) -> None:
        """Seed SQLite DB with existing cases from JSON if available and DB is empty."""
        try:
            with get_db_connection() as conn:
                count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
                if count == 0 and CASES_JSON_FILE.exists():
                    raw = CASES_JSON_FILE.read_text(encoding="utf-8").strip()
                    if raw:
                        items = json.loads(raw)
                        for item in items:
                            self.save_case(item)
        except Exception:
            pass

    def save_case(self, case: dict[str, Any]) -> None:
        """Upsert a case into SQLite and sync with JSON backup."""
        now = datetime.now(timezone.utc).isoformat()
        case_id = case.get("case_id")
        if not case_id:
            raise ValueError("Case must contain a 'case_id'.")

        evidence_json = json.dumps(case.get("evidence_summary", []), ensure_ascii=False)
        metadata_json = json.dumps(case.get("execution_metadata", {}), ensure_ascii=False)

        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO cases (
                    case_id, transaction_id, complaint_category, fraud_probability,
                    risk_level, priority, evidence_summary, recommended_action,
                    requires_human_review, status, error, metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(case_id) DO UPDATE SET
                    status = excluded.status,
                    priority = excluded.priority,
                    risk_level = excluded.risk_level,
                    recommended_action = excluded.recommended_action,
                    evidence_summary = excluded.evidence_summary,
                    requires_human_review = excluded.requires_human_review,
                    error = excluded.error,
                    metadata = excluded.metadata,
                    updated_at = excluded.updated_at
                """,
                (
                    case_id,
                    case.get("transaction_id", "UNKNOWN"),
                    case.get("complaint_category", "unknown"),
                    case.get("fraud_probability"),
                    case.get("risk_level", "unavailable"),
                    case.get("priority", "review_required"),
                    evidence_json,
                    case.get("recommended_action", ""),
                    1 if case.get("requires_human_review", True) else 0,
                    case.get("status", "under_review"),
                    case.get("error"),
                    metadata_json,
                    case.get("created_at", now),
                    now,
                ),
            )
            conn.commit()

        # Update JSON file backup for legacy compatibility
        self._sync_json_backup(case)

    def _sync_json_backup(self, case: dict[str, Any]) -> None:
        try:
            cases = []
            if CASES_JSON_FILE.exists():
                txt = CASES_JSON_FILE.read_text(encoding="utf-8").strip()
                if txt:
                    cases = json.loads(txt)
            cases = [c for c in cases if c.get("case_id") != case.get("case_id")]
            cases.append(case)
            CASES_JSON_FILE.write_text(json.dumps(cases, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def get_case(self, case_id: str) -> dict[str, Any] | None:
        """Retrieve single case by case_id."""
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
            if not row:
                return None
            return self._row_to_dict(row)

    def list_cases(
        self,
        status: str | None = None,
        category: str | None = None,
        priority: str | None = None,
        risk_level: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List cases with optional multi-field filtering."""
        query = "SELECT * FROM cases WHERE 1=1"
        params: list[Any] = []

        if status and status != "All":
            query += " AND status = ?"
            params.append(status)
        if category and category != "All":
            query += " AND complaint_category = ?"
            params.append(category)
        if priority and priority != "All":
            query += " AND priority = ?"
            params.append(priority)
        if risk_level and risk_level != "All":
            query += " AND risk_level = ?"
            params.append(risk_level)

        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        with get_db_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_dict(r) for r in rows]

    @staticmethod
    def _row_to_dict(row) -> dict[str, Any]:
        d = dict(row)
        try:
            d["evidence_summary"] = json.loads(d.get("evidence_summary") or "[]")
        except Exception:
            d["evidence_summary"] = []
        try:
            d["metadata"] = json.loads(d.get("metadata") or "{}")
        except Exception:
            d["metadata"] = {}
        d["requires_human_review"] = bool(d.get("requires_human_review", 1))
        return d


# Singleton instance
case_repo = CaseRepository()
