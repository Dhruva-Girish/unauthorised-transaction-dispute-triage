"""
dispute_cli.py — Command-Line Interface for System Operations (Unit 1.C)
Provides CLI subcommands for single triage, batch processing, case inspection, and health audits.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.case_repository import case_repo


def cmd_triage(args):
    """Execute real-time dispute triage from the command line."""
    from Person_2.agents.triage_agent import process_complaint
    print(f"\n[CLI] Submitting dispute for TX: {args.tx_id}...")
    result = process_complaint(args.complaint, args.tx_id)
    case_repo.save_case(result)

    print("\n" + "=" * 60)
    print("  DISPUTE TRIAGE RESULT")
    print("=" * 60)
    print(f"  Case ID:          {result.get('case_id')}")
    print(f"  Category:         {result.get('complaint_category')}")
    print(f"  Priority:         {result.get('priority')}")
    print(f"  Risk Level:       {result.get('risk_level')}")
    print(f"  Human Review:     {result.get('requires_human_review')}")
    print(f"  Recommended Action: {result.get('recommended_action')}")
    if result.get("evidence_summary"):
        print("  Evidence:")
        for ev in result["evidence_summary"]:
            print(f"    - {ev}")
    print("=" * 60 + "\n")


def cmd_inspect(args):
    """Inspect stored case details by case_id."""
    case = case_repo.get_case(args.case_id)
    if not case:
        print(f"[CLI Error] Case '{args.case_id}' not found in database.")
        sys.exit(1)
    print(json.dumps(case, indent=2))


def cmd_list(args):
    """List persisted cases with optional status filter."""
    cases = case_repo.list_cases(status=args.status, limit=args.limit)
    print(f"\nShowing {len(cases)} case(s):")
    for c in cases:
        print(f"  - {c['case_id']} | TX: {c['transaction_id']} | {c['complaint_category']} | Status: {c['status']} | Priority: {c['priority']}")


def cmd_batch(args):
    """Execute batch inference on CSV transaction records."""
    import pandas as pd
    from Person_1.serving.batch_inference import score_batch

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[CLI Error] Input file '{args.input}' not found.")
        sys.exit(1)

    df = pd.read_csv(input_path)
    res = score_batch(df, output_path=args.output)
    print("[CLI] Batch Scoring Completed:")
    print(json.dumps(res, indent=2))


def cmd_health(args):
    """Audit system dependencies and model registry status."""
    from Person_1.models.registry import get_model_metadata
    print("\n[CLI System Health Audit]")
    meta = get_model_metadata()
    print("  ML Model:       HEALTHY", meta)
    cases = case_repo.list_cases(limit=1)
    print("  Database:       HEALTHY (cases table responsive)")
    print("  Status:         OPERATIONAL\n")


def main():
    parser = argparse.ArgumentParser(description="Card Dispute Triage CLI Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # triage
    p_triage = subparsers.add_parser("triage", help="Submit a dispute for automated triage")
    p_triage.add_argument("--complaint", "-c", required=True, help="Customer dispute text")
    p_triage.add_argument("--tx-id", "-t", required=True, help="Target transaction ID")
    p_triage.set_defaults(func=cmd_triage)

    # inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect a specific case by case_id")
    p_inspect.add_argument("--case-id", "-i", required=True, help="Case ID to inspect")
    p_inspect.set_defaults(func=cmd_inspect)

    # list
    p_list = subparsers.add_parser("list", help="List persisted cases")
    p_list.add_argument("--status", "-s", default=None, help="Filter by status")
    p_list.add_argument("--limit", "-l", type=int, default=20, help="Maximum records")
    p_list.set_defaults(func=cmd_list)

    # batch
    p_batch = subparsers.add_parser("batch", help="Batch score CSV transactions")
    p_batch.add_argument("--input", required=True, help="Input CSV file path")
    p_batch.add_argument("--output", default="batch_scored.csv", help="Output file path")
    p_batch.set_defaults(func=cmd_batch)

    # health
    p_health = subparsers.add_parser("health", help="Check system and model health")
    p_health.set_defaults(func=cmd_health)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
