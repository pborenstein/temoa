"""
Gleaning status management module.

This module handles marking gleanings as active or inactive without modifying
the source of truth (daily notes). Status is stored in .temoa/gleaning_status.json
and applied to extracted gleaning files via frontmatter.

Principles:
- Daily notes are the source of truth (never modified)
- Status stored separately in .temoa/gleaning_status.json
- Extraction script preserves status across re-runs
- Search excludes inactive gleanings by default
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

GleaningStatus = Literal["active", "inactive"]


class GleaningStatusManager:
    """Manages gleaning status (active/inactive)."""

    def __init__(self, storage_dir: Path):
        """
        Initialize the status manager.

        Args:
            storage_dir: Path to .temoa directory (contains gleaning_status.json)
        """
        self.storage_dir = Path(storage_dir)
        self.status_file = self.storage_dir / "gleaning_status.json"
        self._ensure_storage_dir()

    def _ensure_storage_dir(self):
        """Ensure storage directory exists."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _load_status_data(self) -> dict:
        """Load status data from file."""
        if not self.status_file.exists():
            return {}

        with open(self.status_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_status_data(self, data: dict):
        """Save status data to file."""
        with open(self.status_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_status(self, gleaning_id: str) -> GleaningStatus:
        """
        Get status for a gleaning.

        Args:
            gleaning_id: MD5 hash identifier for the gleaning

        Returns:
            "active" or "inactive" (defaults to "active" if not found)
        """
        data = self._load_status_data()
        if gleaning_id not in data:
            return "active"
        return data[gleaning_id].get("status", "active")

    def mark_status(
        self,
        gleaning_id: str,
        status: GleaningStatus,
        reason: Optional[str] = None
    ) -> dict:
        """
        Mark a gleaning with a status.

        Args:
            gleaning_id: MD5 hash identifier for the gleaning
            status: "active" or "inactive"
            reason: Optional reason for the status change

        Returns:
            The status record that was saved
        """
        data = self._load_status_data()

        record = {
            "status": status,
            "marked_at": datetime.utcnow().isoformat() + "Z",
        }

        if reason:
            record["reason"] = reason

        # Preserve previous history if exists
        if gleaning_id in data and "history" in data[gleaning_id]:
            record["history"] = data[gleaning_id]["history"]
        else:
            record["history"] = []

        # Add current change to history
        record["history"].append({
            "status": status,
            "marked_at": record["marked_at"],
            "reason": reason,
        })

        data[gleaning_id] = record
        self._save_status_data(data)

        return record

    def get_gleaning_record(self, gleaning_id: str) -> Optional[dict]:
        """
        Get full status record for a gleaning.

        Args:
            gleaning_id: MD5 hash identifier for the gleaning

        Returns:
            Status record dict or None if not found
        """
        data = self._load_status_data()
        return data.get(gleaning_id)

    def list_gleanings(
        self,
        status_filter: Optional[GleaningStatus] = None
    ) -> dict[str, dict]:
        """
        List all gleanings, optionally filtered by status.

        Args:
            status_filter: If provided, only return gleanings with this status
                          If None, return all gleanings with explicit status

        Returns:
            Dict mapping gleaning_id → status record
        """
        data = self._load_status_data()

        if status_filter is None:
            return data

        return {
            gleaning_id: record
            for gleaning_id, record in data.items()
            if record.get("status") == status_filter
        }

    def find_gleaning_by_file(self, vault_path: Path, gleaning_file: Path) -> Optional[str]:
        """
        Extract gleaning ID from a gleaning file's frontmatter.

        Args:
            vault_path: Path to vault root
            gleaning_file: Path to gleaning markdown file

        Returns:
            Gleaning ID (MD5 hash) or None if not found
        """
        try:
            with open(gleaning_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse frontmatter
            if not content.startswith("---\n"):
                return None

            end_idx = content.find("\n---\n", 4)
            if end_idx == -1:
                return None

            frontmatter = content[4:end_idx]

            # Look for gleaning_id field
            for line in frontmatter.split("\n"):
                if line.startswith("gleaning_id:"):
                    return line.split(":", 1)[1].strip()

            return None

        except Exception:
            return None


def parse_frontmatter_status(content: str) -> Optional[GleaningStatus]:
    """
    Parse status from markdown file frontmatter.

    Args:
        content: Full markdown file content

    Returns:
        "active", "inactive", or None if no status found
    """
    if not content.startswith("---\n"):
        return None

    end_idx = content.find("\n---\n", 4)
    if end_idx == -1:
        return None

    frontmatter = content[4:end_idx]

    for line in frontmatter.split("\n"):
        if line.startswith("status:"):
            status = line.split(":", 1)[1].strip()
            if status in ("active", "inactive"):
                return status

    return None
