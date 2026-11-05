"""
Unit tests for Dispute CLI subcommands in Person 3.
"""
import sys
from pathlib import Path
import pytest
import subprocess

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
P3_PATH = Path(__file__).resolve().parent.parent
if str(P3_PATH) not in sys.path:
    sys.path.insert(0, str(P3_PATH))

CLI_PATH = P3_PATH / "cli" / "dispute_cli.py"

def test_cli_health():
    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "health"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "healthy" in result.stdout.lower() or "status" in result.stdout.lower()

def test_cli_list():
    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "list", "--limit", "5"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "case" in result.stdout.lower() or "showing" in result.stdout.lower()

def test_cli_triage():
    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "triage", "--complaint", "Unauthorized credit card charge of $75", "--tx-id", "TX1001"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "triage result" in result.stdout.lower() or "case_id" in result.stdout.lower() or "category" in result.stdout.lower()
