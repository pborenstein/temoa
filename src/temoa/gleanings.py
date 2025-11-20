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


def scan_gleaning_files(
    vault_path: Path,
    status_manager: GleaningStatusManager,
    status_filter: Optional[GleaningStatus] = None
) -> list[dict]:
    """
    Scan all gleaning files in L/Gleanings/ directory.

    Args:
        vault_path: Path to vault root
        status_manager: Status manager to check gleaning statuses
        status_filter: Optional filter (only return gleanings with this status)

    Returns:
        List of gleaning dicts with metadata
    """
    gleanings_dir = vault_path / "L" / "Gleanings"

    if not gleanings_dir.exists():
        return []

    gleaning_files = list(gleanings_dir.glob("*.md"))
    gleanings_list = []

    for file_path in gleaning_files:
        try:
            # Read file to get frontmatter
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse frontmatter
            if not content.startswith("---\n"):
                continue

            end_idx = content.find("\n---\n", 4)
            if end_idx == -1:
                continue

            frontmatter = content[4:end_idx]

            # Extract fields from frontmatter
            gleaning_data = {}
            for line in frontmatter.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes from title if present
                    if key == "title" and value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]

                    gleaning_data[key] = value

            # Get gleaning_id (from frontmatter or filename)
            gleaning_id = gleaning_data.get("gleaning_id", file_path.stem)

            # Get status (from frontmatter or status manager)
            file_status = gleaning_data.get("status")
            if not file_status:
                file_status = status_manager.get_status(gleaning_id)

            # Filter by status if requested
            if status_filter and file_status != status_filter:
                continue

            # Build gleaning info
            gleaning_info = {
                "gleaning_id": gleaning_id,
                "title": gleaning_data.get("title", "Untitled"),
                "url": gleaning_data.get("url", ""),
                "domain": gleaning_data.get("domain", ""),
                "status": file_status,
                "created": gleaning_data.get("created", gleaning_data.get("date", "")),
                "type": gleaning_data.get("type", ""),
                "file_path": str(file_path.relative_to(vault_path))
            }

            gleanings_list.append(gleaning_info)

        except Exception:
            # Skip files that can't be read
            continue

    # Sort by created date (newest first)
    gleanings_list.sort(key=lambda x: x.get("created", ""), reverse=True)

    return gleanings_list
