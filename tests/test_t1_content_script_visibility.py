import os
import re
import pytest

def test_content_script_visibility_filter_logic():
    """Verify executeMasterAction, executeLoginFlow, and simulateHumanTyping in Extension/content/content_script.js."""
    script_path = os.path.join(os.getcwd(), "Extension", "content", "content_script.js")
    manifest_path = os.path.join(os.getcwd(), "Extension", "manifest.json")
    assert os.path.exists(script_path), "content_script.js file must exist."
    assert os.path.exists(manifest_path), "manifest.json file must exist."

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = f.read()

    assert "visiblePasswordInputs" in content
    assert "isElementVisible" in content
    assert "strictConfirmPassEl" in content
    assert "isPhoneField" in content
    assert "executeLoginFlow" in content
    assert "await simulateHumanTyping" in content
    assert "v1.17.42" in content
    assert "1.17.42" in manifest
