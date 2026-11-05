"""
cases_router.py — REST API Endpoints for Case Management Queue (Unit 1.C)
Provides case querying, status updates, human review escalation, and filtering.
"""

from __future__ import annotations

import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.case_repository import case_repo

router = APIRouter(prefix="/api/v1", tags=["Case Management Queue"])


class CaseStatusUpdatePayload(BaseModel):
    status: str
    reviewer_notes: str | None = None


@router.get("/cases")
def list_dispute_cases(
    status: str | None = Query(None, description="Filter by status (under_review, escalated, resolved)"),
    category: str | None = Query(None, description="Filter by complaint category"),
    priority: str | None = Query(None, description="Filter by priority level"),
    risk_level: str | None = Query(None, description="Filter by risk level"),
    limit: int = Query(50, ge=1, le=200),
):
    """Retrieve persisted cases from database with multi-criteria filtering."""
    cases = case_repo.list_cases(
        status=status,
        category=category,
        priority=priority,
        risk_level=risk_level,
        limit=limit,
    )
    return {"total_returned": len(cases), "cases": cases}


@router.get("/cases/{case_id}")
def get_dispute_case(case_id: str):
    """Retrieve a single dispute case by case_id."""
    case = case_repo.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found in database.",
        )
    return case


@router.patch("/cases/{case_id}")
def update_dispute_case_status(case_id: str, payload: CaseStatusUpdatePayload):
    """Update case status following human review or investigator action."""
    case = case_repo.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found.",
        )

    # Validate status
    if payload.status not in ("new", "under_review", "escalated", "resolved"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{payload.status}'. Must be one of: new, under_review, escalated, resolved.",
        )

    case["status"] = payload.status
    if payload.reviewer_notes:
        meta = case.get("metadata", {})
        meta["reviewer_notes"] = payload.reviewer_notes
        case["metadata"] = meta

    case_repo.save_case(case)
    return {"message": "Case status updated successfully.", "case": case}
