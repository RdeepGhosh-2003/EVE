import os
import sys
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.insert(0, r"c:\MY AI")
import tools

class EmpiricalM1StressTests(unittest.TestCase):

    # ==========================================
    # 1. R4 (manage_system_performance) Tests
    # ==========================================

    def test_r4_invalid_actions(self):
        """Test manage_system_performance with invalid/unknown actions and non-string types."""
        invalid_actions = ["foobar", "invalid_action_123", "", None, "UNKNOWN"]
        for act in invalid_actions:
            res = tools.manage_system_performance(action=act)
            self.assertIsInstance(res, str)
            self.assertTrue(res.startswith("System Status:"), f"Failed for action '{act}': {res}")

    def test_r4_non_string_action(self):
        """Test manage_system_performance when action is non-string (int/bool/obj)."""
        # If action=123 is passed, current code does 123.lower() which raises AttributeError
        res = tools.manage_system_performance(action=123)
        self.assertIsInstance(res, str)
        print(f"\n[R4 Non-String Action 123 Result]: {res}")

    def test_r4_kill_non_existent_process(self):
        """Test kill action with non-existent PID, name, None, and empty string."""
        cases = [
            ("99999999", "No matching process found for target '99999999'."),
            ("non_existent_proc_xyz_123456", "No matching process found for target 'non_existent_proc_xyz_123456'."),
            ("", "Please specify a process name or PID to terminate."),
            (None, "Please specify a process name or PID to terminate.")
        ]
        for target, expected_substring in cases:
            res = tools.manage_system_performance(action="kill", target=target)
            self.assertIsInstance(res, str)
            self.assertIn(expected_substring, res)

    def test_r4_cleanup_busy_temp_dir(self):
        """Test clean action when temp dir contains locked/busy files."""
        temp_dir = tempfile.gettempdir()
        test_file_unlocked = os.path.join(temp_dir, "eve_test_unlocked.tmp")
        test_file_locked = os.path.join(temp_dir, "eve_test_locked.tmp")

        try:
            with open(test_file_unlocked, "w") as f:
                f.write("unlocked data")

            locked_fh = open(test_file_locked, "w")
            locked_fh.write("locked data")
            locked_fh.flush()

            res = tools.manage_system_performance(action="clean")
            self.assertIsInstance(res, str)
            self.assertIn("Performance optimized.", res)
            self.assertFalse(os.path.exists(test_file_unlocked), "Unlocked temp file was not deleted!")
        finally:
            try:
                locked_fh.close()
                if os.path.exists(test_file_locked):
                    os.remove(test_file_locked)
            except Exception:
                pass

    def test_r4_wmi_temp_fallback(self):
        """Test manage_system_performance when WMI PowerShell query fails or returns empty/invalid output."""
        with patch("subprocess.check_output", side_effect=Exception("WMI query failed")):
            res = tools.manage_system_performance(action="check")
            self.assertIsInstance(res, str)
            self.assertTrue(res.startswith("System Status:"))
            self.assertNotIn("CPU Temp", res)

    # ==========================================
    # 2. R5 (organize_downloads_folder) Tests
    # ==========================================

    def test_r5_empty_directory(self):
        """Test organize_downloads_folder on an empty Downloads directory."""
        mock_home = tempfile.mkdtemp(prefix="eve_home_empty_")
        mock_dl = os.path.join(mock_home, "Downloads")
        os.makedirs(mock_dl, exist_ok=True)
        try:
            with patch("os.path.expanduser", return_value=mock_home):
                res = tools.organize_downloads_folder()
                self.assertIn("Moved 0 files", res)
        finally:
            shutil.rmtree(mock_home, ignore_errors=True)

    def test_r5_filename_collisions(self):
        """Test organize_downloads_folder when target file already exists in category folder."""
        mock_home = tempfile.mkdtemp(prefix="eve_home_collision_")
        mock_dl = os.path.join(mock_home, "Downloads")
        doc_dir = os.path.join(mock_dl, "Documents")
        os.makedirs(doc_dir, exist_ok=True)
        try:
            # Target files in Documents
            with open(os.path.join(doc_dir, "report.pdf"), "w") as f:
                f.write("existing doc")
            with open(os.path.join(doc_dir, "report_1.pdf"), "w") as f:
                f.write("existing doc 1")

            # Incoming file in Downloads
            incoming_file = os.path.join(mock_dl, "report.pdf")
            with open(incoming_file, "w") as f:
                f.write("new doc")

            with patch("os.path.expanduser", return_value=mock_home):
                res = tools.organize_downloads_folder()
                self.assertIn("Moved 1 files", res)
                self.assertTrue(os.path.exists(os.path.join(doc_dir, "report_2.pdf")), "Collision suffix increment failed!")
        finally:
            shutil.rmtree(mock_home, ignore_errors=True)

    def test_r5_incomplete_downloads_and_hidden_files(self):
        """Test incomplete downloads (.crdownload, .tmp, .part) and hidden (.dot) files are ignored."""
        mock_home = tempfile.mkdtemp(prefix="eve_home_incomplete_")
        mock_dl = os.path.join(mock_home, "Downloads")
        os.makedirs(mock_dl, exist_ok=True)
        try:
            # Files to ignore
            ignored_files = [
                "download.crdownload",
                "setup.tmp",
                "video.part",
                "data.download",
                "torrent.p2p",
                ".ds_store",
                ".gitignore",
                ".hidden_doc.pdf"
            ]
            for fname in ignored_files:
                with open(os.path.join(mock_dl, fname), "w") as f:
                    f.write("temp content")

            # File to move
            with open(os.path.join(mock_dl, "valid_image.png"), "w") as f:
                f.write("png image content")

            with patch("os.path.expanduser", return_value=mock_home):
                res = tools.organize_downloads_folder()
                self.assertIn("Moved 1 files", res)

                # Verify ignored files still in root
                for fname in ignored_files:
                    self.assertTrue(os.path.exists(os.path.join(mock_dl, fname)), f"File {fname} was moved when it should be ignored!")

                # Verify valid file moved
                self.assertTrue(os.path.exists(os.path.join(mock_dl, "Images", "valid_image.png")))
        finally:
            shutil.rmtree(mock_home, ignore_errors=True)

    def test_r5_permission_error_locked_file(self):
        """Test organize_downloads_folder when one file raises PermissionError during shutil.move."""
        mock_home = tempfile.mkdtemp(prefix="eve_home_locked_")
        mock_dl = os.path.join(mock_home, "Downloads")
        os.makedirs(mock_dl, exist_ok=True)
        try:
            # Create two valid files
            f1 = os.path.join(mock_dl, "aaa_doc1.pdf")
            f2 = os.path.join(mock_dl, "zzz_doc2.pdf")
            with open(f1, "w") as f:
                f.write("doc 1")
            with open(f2, "w") as f:
                f.write("doc 2")

            # Mock shutil.move to raise PermissionError on aaa_doc1.pdf
            real_move = shutil.move
            def mock_move(src, dst):
                if "aaa_doc1.pdf" in src:
                    raise PermissionError("Access denied on aaa_doc1.pdf")
                return real_move(src, dst)

            with patch("os.path.expanduser", return_value=mock_home), \
                 patch("shutil.move", side_effect=mock_move):
                res = tools.organize_downloads_folder()
                print(f"\n[Permission Error Test Output]: {res}")
                doc2_moved = os.path.exists(os.path.join(mock_dl, "Documents", "zzz_doc2.pdf"))
                print(f"[Permission Error Test - zzz_doc2.pdf moved?]: {doc2_moved}")
        finally:
            shutil.rmtree(mock_home, ignore_errors=True)

    # ==========================================
    # 3. Registry & Schema Tests
    # ==========================================

    def test_registry_schema_parity(self):
        """Verify AVAILABLE_TOOLS and GROQ_TOOLS schemas match 1-to-1."""
        available_keys = set(tools.AVAILABLE_TOOLS.keys())
        groq_names = {t["function"]["name"] for t in tools.GROQ_TOOLS}

        self.assertEqual(len(available_keys), 18, f"Expected 18 AVAILABLE_TOOLS, found {len(available_keys)}")
        self.assertEqual(len(groq_names), 18, f"Expected 18 GROQ_TOOLS, found {len(groq_names)}")
        self.assertEqual(available_keys, groq_names, f"Mismatch between AVAILABLE_TOOLS and GROQ_TOOLS: {available_keys ^ groq_names}")

    def test_execute_tool_dispatch(self):
        """Verify execute_tool handles standard, missing, unknown, and invalid tool calls."""
        # Standard tool execution
        res_time = tools.execute_tool("get_current_time")
        self.assertIn("The current date and time is", res_time)

        # Tool with arguments
        res_news = tools.execute_tool("fetch_live_news", {"topic": "ai"})
        self.assertTrue(isinstance(res_news, str))

        # Unknown tool name
        res_unknown = tools.execute_tool("unknown_tool_xyz")
        self.assertEqual(res_unknown, "Unknown tool 'unknown_tool_xyz'")

        # Tool execution with unexpected/invalid keyword argument
        res_bad_arg = tools.execute_tool("get_current_time", {"unexpected_arg": "val"})
        self.assertTrue(res_bad_arg.startswith("Error executing tool 'get_current_time':"))

if __name__ == "__main__":
    unittest.main()
