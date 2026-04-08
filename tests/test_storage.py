"""Unit tests for storage.py — no API key required."""

import json
import os
import pytest

# Redirect storage files to a temp directory during tests
import tempfile

_tmp = tempfile.mkdtemp()

# Patch file paths before importing storage
import storage as _storage_module

_storage_module.APPOINTMENTS_FILE = os.path.join(_tmp, "test_appointments.json")
_storage_module.LEADS_FILE        = os.path.join(_tmp, "test_leads.json")

import storage  # re-import to pick up patched paths (same object, already patched)


@pytest.fixture(autouse=True)
def clean_files():
    """Remove test JSON files before each test."""
    for path in [storage.APPOINTMENTS_FILE, storage.LEADS_FILE]:
        if os.path.exists(path):
            os.remove(path)
    yield


# ── Appointments ──────────────────────────────────────────────────────────

def test_file_auto_created_appointments():
    assert not os.path.exists(storage.APPOINTMENTS_FILE)
    result = storage.list_appointments()
    assert result == []


def test_save_and_load_appointment():
    data = {"name": "Alice", "date": "2025-06-01", "time": "10:00 AM", "reason": "Check-up"}
    entry = storage.save_appointment(data)

    assert entry["id"] == 1
    assert entry["name"] == "Alice"
    assert "created_at" in entry

    loaded = storage.list_appointments()
    assert len(loaded) == 1
    assert loaded[0]["name"] == "Alice"
    assert loaded[0]["date"] == "2025-06-01"


def test_multiple_appointments_incrementing_ids():
    storage.save_appointment({"name": "Bob",   "date": "2025-06-02", "time": "09:00 AM", "reason": "Cleaning"})
    storage.save_appointment({"name": "Carol", "date": "2025-06-03", "time": "11:00 AM", "reason": "Filling"})

    records = storage.list_appointments()
    assert len(records) == 2
    assert records[0]["id"] == 1
    assert records[1]["id"] == 2


# ── Leads ─────────────────────────────────────────────────────────────────

def test_file_auto_created_leads():
    assert not os.path.exists(storage.LEADS_FILE)
    result = storage.list_leads()
    assert result == []


def test_save_and_load_lead():
    data = {"name": "Dave", "email": "dave@example.com", "phone": "+1555000", "inquiry": "Whitening"}
    entry = storage.save_lead(data)

    assert entry["id"] == 1
    assert entry["email"] == "dave@example.com"
    assert "created_at" in entry

    loaded = storage.list_leads()
    assert len(loaded) == 1
    assert loaded[0]["inquiry"] == "Whitening"


def test_save_lead_without_optional_fields():
    data = {"name": "Eve", "inquiry": "General info"}
    entry = storage.save_lead(data)
    assert entry["name"] == "Eve"
    assert entry.get("email") is None


def test_multiple_leads():
    storage.save_lead({"name": "Frank", "inquiry": "Pricing"})
    storage.save_lead({"name": "Grace", "inquiry": "Hours"})

    records = storage.list_leads()
    assert len(records) == 2
    assert records[1]["name"] == "Grace"


# ── JSON integrity ────────────────────────────────────────────────────────

def test_appointments_persisted_as_valid_json():
    storage.save_appointment({"name": "Hank", "date": "2025-07-01", "time": "2:00 PM", "reason": "Crown"})
    with open(storage.APPOINTMENTS_FILE, "r") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert data[0]["name"] == "Hank"
