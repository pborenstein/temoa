"""Tests for gleaning status management and extraction"""
import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from temoa.gleanings import (
    GleaningStatusManager,
    parse_frontmatter_status
)
from temoa.scripts.extract_gleanings import GleaningsExtractor


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def status_manager(temp_storage_dir):
    """Create a status manager for tests"""
    return GleaningStatusManager(temp_storage_dir)


def test_status_manager_init(temp_storage_dir):
    """Test status manager initialization"""
    manager = GleaningStatusManager(temp_storage_dir)
    assert manager.storage_dir == temp_storage_dir
    assert manager.status_file == temp_storage_dir / "gleaning_status.json"


def test_get_status_default(status_manager):
    """Test get_status returns 'active' for unknown gleaning"""
    status = status_manager.get_status("unknown123")
    assert status == "active"


def test_mark_status_inactive(status_manager):
    """Test marking a gleaning as inactive"""
    gleaning_id = "test123"
    record = status_manager.mark_status(
        gleaning_id,
        "inactive",
        "Test reason"
    )

    assert record["status"] == "inactive"
    assert record["reason"] == "Test reason"
    assert "marked_at" in record
    assert "history" in record
    assert len(record["history"]) == 1

    # Verify it was saved
    status = status_manager.get_status(gleaning_id)
    assert status == "inactive"


def test_mark_status_active(status_manager):
    """Test marking a gleaning as active"""
    gleaning_id = "test456"
    record = status_manager.mark_status(gleaning_id, "active")

    assert record["status"] == "active"
    assert "reason" not in record
    assert "marked_at" in record


def test_mark_status_preserves_history(status_manager):
    """Test that status changes preserve history"""
    gleaning_id = "test789"

    # First change: inactive
    status_manager.mark_status(gleaning_id, "inactive", "First reason")

    # Second change: active
    record = status_manager.mark_status(gleaning_id, "active", "Changed my mind")

    assert record["status"] == "active"
    assert len(record["history"]) == 2
    assert record["history"][0]["status"] == "inactive"
    assert record["history"][1]["status"] == "active"


def test_get_gleaning_record(status_manager):
    """Test getting full gleaning record"""
    gleaning_id = "test000"
    status_manager.mark_status(gleaning_id, "inactive", "Test")

    record = status_manager.get_gleaning_record(gleaning_id)

    assert record is not None
    assert record["status"] == "inactive"
    assert record["reason"] == "Test"


def test_get_gleaning_record_not_found(status_manager):
    """Test getting record for non-existent gleaning"""
    record = status_manager.get_gleaning_record("nonexistent")
    assert record is None


def test_list_gleanings_all(status_manager):
    """Test listing all gleanings"""
    status_manager.mark_status("g1", "active")
    status_manager.mark_status("g2", "inactive")
    status_manager.mark_status("g3", "inactive")

    all_gleanings = status_manager.list_gleanings(status_filter=None)

    assert len(all_gleanings) == 3
    assert "g1" in all_gleanings
    assert "g2" in all_gleanings
    assert "g3" in all_gleanings


def test_list_gleanings_by_status(status_manager):
    """Test listing gleanings filtered by status"""
    status_manager.mark_status("g1", "active")
    status_manager.mark_status("g2", "inactive")
    status_manager.mark_status("g3", "inactive")

    inactive_gleanings = status_manager.list_gleanings(status_filter="inactive")

    assert len(inactive_gleanings) == 2
    assert "g1" not in inactive_gleanings
    assert "g2" in inactive_gleanings
    assert "g3" in inactive_gleanings


def test_list_gleanings_empty(status_manager):
    """Test listing gleanings when none exist"""
    gleanings = status_manager.list_gleanings()
    assert len(gleanings) == 0


def test_parse_frontmatter_status_active():
    """Test parsing active status from frontmatter"""
    content = """---
title: "Test"
status: active
---

# Test content
"""
    status = parse_frontmatter_status(content)
    assert status == "active"


def test_parse_frontmatter_status_inactive():
    """Test parsing inactive status from frontmatter"""
    content = """---
title: "Test"
status: inactive
---

# Test content
"""
    status = parse_frontmatter_status(content)
    assert status == "inactive"


def test_parse_frontmatter_status_missing():
    """Test parsing when status field is missing"""
    content = """---
title: "Test"
---

# Test content
"""
    status = parse_frontmatter_status(content)
    assert status is None


def test_parse_frontmatter_status_no_frontmatter():
    """Test parsing when no frontmatter exists"""
    content = """# Test content

No frontmatter here.
"""
    status = parse_frontmatter_status(content)
    assert status is None


def test_parse_frontmatter_status_invalid():
    """Test parsing when status value is invalid"""
    content = """---
title: "Test"
status: maybe
---

# Test content
"""
    status = parse_frontmatter_status(content)
    assert status is None


def test_status_file_persistence(temp_storage_dir):
    """Test that status is persisted across manager instances"""
    # Create first manager and mark a gleaning
    manager1 = GleaningStatusManager(temp_storage_dir)
    manager1.mark_status("persist123", "inactive", "Test persistence")

    # Create second manager and check status
    manager2 = GleaningStatusManager(temp_storage_dir)
    status = manager2.get_status("persist123")

    assert status == "inactive"

    record = manager2.get_gleaning_record("persist123")
    assert record["reason"] == "Test persistence"


def test_status_file_format(temp_storage_dir):
    """Test that status file has correct JSON format"""
    manager = GleaningStatusManager(temp_storage_dir)
    manager.mark_status("format123", "inactive", "Format test")

    # Read status file directly
    status_file = temp_storage_dir / "gleaning_status.json"
    with open(status_file, "r") as f:
        data = json.load(f)

    assert "format123" in data
    assert data["format123"]["status"] == "inactive"
    assert data["format123"]["reason"] == "Format test"
    assert "marked_at" in data["format123"]
    assert "history" in data["format123"]


@pytest.fixture
def temp_vault_with_duplicates(tmp_path):
    """Create a temporary vault with duplicate daily note paths (case variations)"""
    vault = tmp_path / "vault"
    vault.mkdir()

    # Create a Daily directory (capital D)
    daily_dir = vault / "Daily" / "2025"
    daily_dir.mkdir(parents=True)

    # Create a daily note
    daily_note = daily_dir / "2025-11-21.md"
    daily_note.write_text("""---
date: 2025-11-21
---

## Gleanings

- [Test Article](https://example.com/test) - A test article
""")

    return vault


def test_find_daily_notes_no_duplicates_on_case_insensitive_fs(temp_vault_with_duplicates):
    """Test that find_daily_notes doesn't return duplicates on case-insensitive filesystems"""
    extractor = GleaningsExtractor(temp_vault_with_duplicates)

    # Find daily notes (both "Daily/**/*.md" and "daily/**/*.md" patterns will match on macOS)
    daily_notes = extractor.find_daily_notes(incremental=False)

    # Should only find each file once, not twice
    assert len(daily_notes) == 1, f"Expected 1 note, found {len(daily_notes)}: {daily_notes}"

    # Verify it's the correct file
    assert daily_notes[0].name == "2025-11-21.md"


def test_extract_gleanings_no_duplicate_processing(temp_vault_with_duplicates):
    """Test that gleanings are not processed twice from the same file"""
    extractor = GleaningsExtractor(temp_vault_with_duplicates)

    # Extract all gleanings
    gleanings_dir = temp_vault_with_duplicates / "L" / "Gleanings"
    gleanings_dir.mkdir(parents=True)

    daily_notes = extractor.find_daily_notes(incremental=False)
    all_gleanings = []

    for note in daily_notes:
        gleanings = extractor.extract_from_note(note)
        all_gleanings.extend(gleanings)

    # Should only extract 1 gleaning (not 2 from processing the same file twice)
    assert len(all_gleanings) == 1, f"Expected 1 gleaning, found {len(all_gleanings)}"
    assert all_gleanings[0].title == "Test Article"
    assert all_gleanings[0].url == "https://example.com/test"
