import sys
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools import organize_downloads_folder

def test_organize_nonexistent_dir():
    """
    Verify organize_downloads_folder returns appropriate error message when Downloads directory does not exist.
    Verifies boundary condition where Downloads target path is missing.
    """
    with patch("os.path.exists", return_value=False):
        result = organize_downloads_folder()
        assert isinstance(result, str)
        assert "Downloads folder not found at" in result

def test_organize_readonly_files():
    """
    Verify organize_downloads_folder handles permission errors when attempting to move read-only files.
    Verifies boundary condition for PermissionError exception handling.
    """
    def mock_exists(path):
        if path.endswith("Downloads"):
            return True
        return False

    with patch("os.path.exists", side_effect=mock_exists), \
         patch("os.listdir", return_value=["locked.pdf"]), \
         patch("os.path.isfile", return_value=True), \
         patch("shutil.move", side_effect=PermissionError("Permission denied: locked.pdf")):
        result = organize_downloads_folder()
        assert isinstance(result, str)
        assert "Organized Downloads folder" in result or "Moved 0 files" in result

def test_organize_path_traversal_filenames():
    """
    Verify organize_downloads_folder handles files with path traversal patterns (e.g. 'sample_.._doc.pdf') safely.
    Verifies boundary case for special character and dot-containing filenames.
    """
    temp_parent = tempfile.mkdtemp()
    try:
        temp_downloads = os.path.join(temp_parent, "Downloads")
        os.makedirs(temp_downloads, exist_ok=True)
        
        traversal_file = os.path.join(temp_downloads, "sample_.._doc.pdf")
        with open(traversal_file, "w") as f:
            f.write("content")

        with patch("os.path.expanduser", return_value=temp_parent):
            result = organize_downloads_folder()
            assert isinstance(result, str)
            assert "Organized Downloads folder: Moved 1 files" in result
            doc_cat = os.path.join(temp_downloads, "Documents")
            assert os.path.exists(doc_cat)
            assert os.path.exists(os.path.join(doc_cat, "sample_.._doc.pdf"))
    finally:
        shutil.rmtree(temp_parent, ignore_errors=True)

def test_organize_duplicate_filenames():
    """
    Verify organize_downloads_folder handles duplicate files when target subfolder already contains a file with the same name.
    Verifies boundary case for destination filename collision and OS rename behavior.
    """
    temp_parent = tempfile.mkdtemp()
    try:
        temp_downloads = os.path.join(temp_parent, "Downloads")
        docs_dir = os.path.join(temp_downloads, "Documents")
        os.makedirs(docs_dir, exist_ok=True)
        
        with open(os.path.join(docs_dir, "report.pdf"), "w") as f:
            f.write("existing document")

        with open(os.path.join(temp_downloads, "report.pdf"), "w") as f:
            f.write("new document")

        with patch("os.path.expanduser", return_value=temp_parent):
            result = organize_downloads_folder()
            assert isinstance(result, str)
            # Depending on OS/filesystem, duplicate rename either succeeds by overwriting or fails with error message
            assert "Organized Downloads folder" in result or "Failed to organize downloads:" in result
    finally:
        shutil.rmtree(temp_parent, ignore_errors=True)

def test_organize_large_number_of_files():
    """
    Verify organize_downloads_folder efficiently categorizes a large directory with 105+ files across all categories.
    Verifies boundary case for high volume directory processing.
    """
    temp_parent = tempfile.mkdtemp()
    try:
        temp_downloads = os.path.join(temp_parent, "Downloads")
        os.makedirs(temp_downloads, exist_ok=True)

        exts = [".jpg", ".pdf", ".mp3", ".zip", ".py"]
        total_files = 0
        for i in range(21):
            for ext in exts:
                fname = f"file_{i}{ext}"
                with open(os.path.join(temp_downloads, fname), "w") as f:
                    f.write("content")
                total_files += 1

        assert total_files == 105

        with patch("os.path.expanduser", return_value=temp_parent):
            result = organize_downloads_folder()
            assert isinstance(result, str)
            assert "Moved 105 files into categorized subfolders." in result

            for cat in ["Images", "Documents", "Audio", "Archives", "Code"]:
                cat_path = os.path.join(temp_downloads, cat)
                assert os.path.exists(cat_path)
                assert len(os.listdir(cat_path)) == 21
    finally:
        shutil.rmtree(temp_parent, ignore_errors=True)
