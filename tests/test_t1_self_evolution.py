import os
import sys
import shutil
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools import modify_system_code, reboot_system, AVAILABLE_TOOLS, GROQ_TOOLS


def test_modify_system_code_ast_validation():
    """Verify modify_system_code blocks invalid Python syntax using AST validation."""
    test_file = "scratch_test_invalid.py"
    invalid_code = "def broken_func(: return 42"

    res = modify_system_code(test_file, invalid_code)
    assert "[SyntaxError Aborted]" in res
    assert not os.path.exists(test_file)


def test_modify_system_code_success_and_backup():
    """Verify modify_system_code validates syntax, creates backups, and overwrites files correctly."""
    test_file = "scratch_test_valid.py"
    valid_code = "def valid_func():\n    return 42\n"

    try:
        # Initial file write
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("# initial content\n")

        updated_code = "def updated_func():\n    return 100\n"
        res = modify_system_code(test_file, updated_code)

        assert "[Success]" in res
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert content == updated_code

        # Verify backup was created in memory/backups
        backup_dir = os.path.join(os.getcwd(), "memory", "backups")
        assert os.path.exists(backup_dir)
        backups = [b for b in os.listdir(backup_dir) if "scratch_test_valid.py" in b]
        assert len(backups) > 0

    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def test_tools_registration():
    """Verify modify_system_code and reboot_system are registered in AVAILABLE_TOOLS and GROQ_TOOLS."""
    assert "modify_system_code" in AVAILABLE_TOOLS
    assert "reboot_system" in AVAILABLE_TOOLS

    groq_tool_names = [t["function"]["name"] for t in GROQ_TOOLS]
    assert "modify_system_code" in groq_tool_names
    assert "reboot_system" in groq_tool_names
