import sys
import os
from unittest.mock import patch
import pytest

# Append workspace root so tools.py can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from tools import organize_downloads_folder
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False


def test_organize_downloads_default(tmp_path):
    """R5: Verify organize_downloads_folder() runs on downloads directory."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    downloads_dir = tmp_path / "Downloads"
    downloads_dir.mkdir()
    
    with patch("os.path.expanduser", return_value=str(tmp_path)):
        result = organize_downloads_folder()
        assert isinstance(result, str)
        assert "Organized Downloads folder" in result


def test_organize_downloads_return_type(tmp_path):
    """R5: Verify return value is a status message string."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    downloads_dir = tmp_path / "Downloads"
    downloads_dir.mkdir()
    
    with patch("os.path.expanduser", return_value=str(tmp_path)):
        result = organize_downloads_folder()
        assert type(result) is str


def test_organize_downloads_subfolder_creation(tmp_path):
    """R5: Verify organizer creates standard subfolders if needed."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    downloads_dir = tmp_path / "Downloads"
    downloads_dir.mkdir()
    
    # Create test files
    (downloads_dir / "photo.jpg").write_text("fake image")
    (downloads_dir / "report.pdf").write_text("fake doc")
    (downloads_dir / "song.mp3").write_text("fake audio")
    
    with patch("os.path.expanduser", return_value=str(tmp_path)):
        result = organize_downloads_folder()
        assert isinstance(result, str)
        assert (downloads_dir / "Images").exists()
        assert (downloads_dir / "Documents").exists()
        assert (downloads_dir / "Audio").exists()


def test_organize_downloads_file_sorting(tmp_path):
    """R5: Verify files are categorized into appropriate extension folders."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    downloads_dir = tmp_path / "Downloads"
    downloads_dir.mkdir()
    
    # Create test files
    (downloads_dir / "image.png").write_text("image content")
    (downloads_dir / "script.py").write_text("python code")
    (downloads_dir / "archive.zip").write_text("zip data")
    
    with patch("os.path.expanduser", return_value=str(tmp_path)):
        result = organize_downloads_folder()
        assert "Moved 3 files" in result
        assert (downloads_dir / "Images" / "image.png").exists()
        assert (downloads_dir / "Code" / "script.py").exists()
        assert (downloads_dir / "Archives" / "archive.zip").exists()


def test_organize_downloads_repeat_run(tmp_path):
    """R5: Verify running organizer multiple times is idempotent."""
    assert TOOLS_AVAILABLE, "tools.py must be importable"
    downloads_dir = tmp_path / "Downloads"
    downloads_dir.mkdir()
    
    (downloads_dir / "doc.txt").write_text("some text")
    
    with patch("os.path.expanduser", return_value=str(tmp_path)):
        res1 = organize_downloads_folder()
        assert "Moved 1 files" in res1
        
        res2 = organize_downloads_folder()
        assert "Moved 0 files" in res2
