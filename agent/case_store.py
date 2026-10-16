
import json
from pathlib import Path
from threading import Lock

CASES_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "cases.json"
)

_lock = Lock()


def save_case(case: dict) -> None:
    """Persist a complete triage result in the cases JSON file."""
    CASES_FILE.parent.mkdir(parents=True, exist_ok=True)

    with _lock:
        cases = []

        if CASES_FILE.exists():
            content = CASES_FILE.read_text(encoding="utf-8").strip()
            if content:
                cases = json.loads(content)

        if not isinstance(cases, list):
            raise ValueError("Case storage must contain a JSON list.")

        case_id = case.get("case_id")
        if not case_id:
            raise ValueError("Case must have a case_id.")

        # Update an existing case instead of creating a duplicate.
        cases = [
            existing for existing in cases
            if existing.get("case_id") != case_id
        ]
        cases.append(case)

        temp_file = CASES_FILE.with_suffix(".tmp")
        temp_file.write_text(
            json.dumps(cases, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        temp_file.replace(CASES_FILE)


def load_cases() -> list[dict]:
    """Return all persisted cases."""
    if not CASES_FILE.exists():
        return []

    with _lock:
        content = CASES_FILE.read_text(encoding="utf-8").strip()

    if not content:
        return []

    cases = json.loads(content)
    if not isinstance(cases, list):
        raise ValueError("Case storage must contain a JSON list.")

    return cases
