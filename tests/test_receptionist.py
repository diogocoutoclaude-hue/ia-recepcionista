"""Integration tests for receptionist.py — requires GROQ_API_KEY in environment."""

import os
import json
import pytest
import tempfile

# Skip entire module if no API key
pytestmark = pytest.mark.skipif(
    not os.environ.get("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set — skipping integration tests",
)

# Redirect storage files to temp dir so tests don't pollute real data
_tmp = tempfile.mkdtemp()
import storage as _storage_module
_storage_module.APPOINTMENTS_FILE = os.path.join(_tmp, "int_appointments.json")
_storage_module.LEADS_FILE        = os.path.join(_tmp, "int_leads.json")

import storage
import receptionist


@pytest.fixture(autouse=True)
def clean_storage():
    for path in [storage.APPOINTMENTS_FILE, storage.LEADS_FILE]:
        if os.path.exists(path):
            os.remove(path)
    yield


# ── Helpers ───────────────────────────────────────────────────────────────

def user(text: str) -> dict:
    return {"role": "user", "content": text}


# ── Tests ─────────────────────────────────────────────────────────────────

def test_faq_response():
    """Ask about opening hours — should get a non-empty text response."""
    reply = receptionist.chat([user("What are your opening hours?")])
    assert isinstance(reply, str)
    assert len(reply) > 10


def test_book_appointment_tool_called():
    """Complete booking request — appointment should be saved to JSON."""
    reply = receptionist.chat([
        user("I'd like to book an appointment. My name is John Smith, "
             "I'd like to come in on 2025-08-15 at 10:00 AM for a teeth cleaning.")
    ])
    assert isinstance(reply, str)
    appointments = storage.list_appointments()
    assert len(appointments) >= 1
    names = [a.get("name", "").lower() for a in appointments]
    assert any("john" in n for n in names), f"Expected 'john' in names, got {names}"


def test_lead_capture_tool_called():
    """Caller wants follow-up — lead should be saved."""
    reply = receptionist.chat([
        user("I'd like someone to contact me. My name is Sarah Jones, "
             "email sarah@example.com. I'm interested in teeth whitening.")
    ])
    assert isinstance(reply, str)
    leads = storage.list_leads()
    assert len(leads) >= 1
    inquiries = [l.get("inquiry", "").lower() for l in leads]
    assert any("whiten" in i for i in inquiries), f"Expected whitening in inquiries, got {inquiries}"


def test_human_escalation():
    """Caller asks to speak to a person — reply should contain contact info."""
    from config import ESCALATION_CONTACT
    reply = receptionist.chat([user("I need to speak to a real person please.")])
    assert isinstance(reply, str)
    # Reply should mention a phone number or email
    has_contact = (
        ESCALATION_CONTACT["phone"] in reply
        or ESCALATION_CONTACT["email"] in reply
        or any(word in reply.lower() for word in ["phone", "email", "contact", "team", "reach"])
    )
    assert has_contact, f"Expected contact info in reply, got: {reply}"


def test_full_conversation():
    """Multi-turn: greet → FAQ → book."""
    msgs = [
        user("Hi there!"),
    ]
    reply1 = receptionist.chat(msgs)
    assert len(reply1) > 5

    msgs += [
        {"role": "assistant", "content": reply1},
        user("What services do you offer?"),
    ]
    reply2 = receptionist.chat(msgs)
    assert len(reply2) > 10

    msgs += [
        {"role": "assistant", "content": reply2},
        user("Great! Book me in. Name is Tom Brown, date 2025-09-10, time 3:00 PM, reason is a general check-up."),
    ]
    reply3 = receptionist.chat(msgs)
    assert len(reply3) > 5
    appointments = storage.list_appointments()
    assert len(appointments) >= 1
