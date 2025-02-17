import pytest
from pathlib import Path
from ai_companion.settings import Settings

def test_db_path_creation():
    settings = Settings()
    db_path = Path(settings.SHORT_TERM_MEMORY_DB_PATH)
    assert db_path.exists(), f"Database path {db_path} should exist"
    assert db_path.parent.is_dir(), "Parent directory should be created"
    assert db_path.suffix == ".db", "Should have .db extension"

def test_windows_path_format():
    settings = Settings()
    path = settings.SHORT_TERM_MEMORY_DB_PATH
    assert not path.startswith("/app"), "Should use Windows-compatible path"
    assert "\\" in path or ":" in path, "Should follow Windows path conventions" 