import json
import os
from datetime import datetime, timezone
from typing import Any

from utils.atomic_writer import atomic_write_json

APPOINTMENTS_FILE = "appointments.json"
LEADS_FILE = "leads.json"


def _read(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _write(path: str, records: list[dict]) -> None:
    from utils.atomic_writer import atomic_write_json
    atomic_write_json(path, records)


def save_appointment(data: dict[str, Any]) -> dict:
    records = _read(APPOINTMENTS_FILE)
    entry = {
        "id": len(records) + 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **data,
    }
    records.append(entry)
    _write(APPOINTMENTS_FILE, records)
    return entry


def list_appointments() -> list[dict]:
    return _read(APPOINTMENTS_FILE)


def save_lead(data: dict[str, Any]) -> dict:
    records = _read(LEADS_FILE)
    entry = {
        "id": len(records) + 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **data,
    }
    records.append(entry)
    _write(LEADS_FILE, records)
    return entry


def list_leads() -> list[dict]:
    return _read(LEADS_FILE)
