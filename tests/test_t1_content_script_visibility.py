import os
import re
import pytest

def test_content_script_visibility_filter_logic():
    """Verify executeMasterAction in Extension/content/content_script.js contains strict visible password filtering."""
    script_path = os.path.join(os.getcwd(), "Extension", "content", "content_script.js")
    assert os.path.exists(script_path), "content_script.js file must exist."

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "visiblePasswordInputs" in content
    assert "isElementVisible" in content
    assert "strictConfirmPassEl" in content
    assert "passwordInputCount >= 2" in content
    assert "v1.17.41" in content
