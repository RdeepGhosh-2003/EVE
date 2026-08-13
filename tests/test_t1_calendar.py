import sys
import os
import json
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools import check_schedule


def test_calendar_add_and_read(tmp_path, monkeypatch):
    """Verify check_schedule can add an event and read it back from memory/calendar.json."""
    memory_dir = tmp_path / "memory"
    monkeypatch.chdir(tmp_path)

    # 1. Add event
    add_res = check_schedule(date="2026-09-01", action="add", event_details="Team Strategy Meeting at 3 PM")
    assert "Scheduled event on 2026-09-01" in add_res

    # 2. Read event
    read_res = check_schedule(date="2026-09-01", action="read")
    assert "Team Strategy Meeting at 3 PM" in read_res

    # 3. Read non-existent date
    empty_res = check_schedule(date="2029-12-31", action="read")
    assert "No events scheduled" in empty_res


def test_calendar_delete(tmp_path, monkeypatch):
    """Verify check_schedule can remove events matching a keyword."""
    memory_dir = tmp_path / "memory"
    monkeypatch.chdir(tmp_path)

    check_schedule(date="2026-09-01", action="add", event_details="Project Launch Call")
    check_schedule(date="2026-09-01", action="add", event_details="Doctor Appointment")

    del_res = check_schedule(date="2026-09-01", action="delete", event_details="Doctor")
    assert "Removed 1 matching event" in del_res

    read_res = check_schedule(date="2026-09-01", action="read")
    assert "Project Launch Call" in read_res
    assert "Doctor Appointment" not in read_res
