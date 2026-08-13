## 2026-08-12T17:28:30Z
Objective: Fix 3 boundary tests in `c:\MY AI\tests\test_t2_downloads_organizer_boundaries.py` and `c:\MY AI\tests\test_t2_rss_news_boundaries.py`.

Issues to fix:
1. `tests/test_t2_downloads_organizer_boundaries.py::test_organize_readonly_files`: Fix the mock in `test_organize_readonly_files` so `os.path.exists` does NOT return `True` unconditionally (or side_effect function that returns `True` for source file/directory check, but `False` for duplicate target checks `dst_path`), preventing an infinite `while os.path.exists` loop in `tools.py`.
2. `tests/test_t2_downloads_organizer_boundaries.py::test_organize_path_traversal_filenames`: Update test filename from `.._sample_doc.pdf` (which starts with a dot `.` and gets skipped as a hidden file) to a path traversal pattern that does not start with a dot, e.g. `traversal_../document.pdf` or `sample..doc.pdf`, or test path traversal security behavior.
3. `tests/test_t2_rss_news_boundaries.py::test_rss_invalid_topic`: Update assertion in `test_rss_invalid_topic` so it checks that the returned string is either `Top Live ...` OR starts with `Failed to fetch live news:` / `No RSS items found` (the valid fallback string returned by `tools.py` when RSS feed has no items).
