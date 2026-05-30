"""Post-retrieval and pre-retrieval filter functions for search."""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def filter_by_properties(results, include_props=None, exclude_props=None):
    if not include_props and not exclude_props:
        return results, 0
    filtered = []
    for result in results:
        fm = result.get("frontmatter", {})
        if include_props:
            if not any(
                str(fm.get(f["prop"], "")).lower() == str(f["value"]).lower()
                for f in include_props if f.get("prop") and f.get("value")
            ):
                continue
        if exclude_props:
            if any(
                str(fm.get(f["prop"], "")).lower() == str(f["value"]).lower()
                for f in exclude_props if f.get("prop") and f.get("value")
            ):
                continue
        filtered.append(result)
    return filtered, len(results) - len(filtered)


def filter_by_tags(results, include_tags=None, exclude_tags=None):
    if not include_tags and not exclude_tags:
        return results, 0
    filtered = []
    for result in results:
        tags = result.get("frontmatter", {}).get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        tags = [t.lstrip("#").lower() for t in tags]
        if include_tags:
            if not any(t.lstrip("#").lower() in tags for t in include_tags):
                continue
        if exclude_tags:
            if any(t.lstrip("#").lower() in tags for t in exclude_tags):
                continue
        filtered.append(result)
    return filtered, len(results) - len(filtered)


def filter_by_paths(results, include_paths=None, exclude_paths=None):
    if not include_paths and not exclude_paths:
        return results, 0
    filtered = []
    for result in results:
        p = result.get("file_path", "")
        if include_paths and not any(pat in p for pat in include_paths):
            continue
        if exclude_paths and any(pat in p for pat in exclude_paths):
            continue
        filtered.append(result)
    return filtered, len(results) - len(filtered)


def filter_by_files(results, include_files=None, exclude_files=None):
    if not include_files and not exclude_files:
        return results, 0
    filtered = []
    for result in results:
        name = Path(result.get("file_path", "")).name
        if include_files and not any(pat in name for pat in include_files):
            continue
        if exclude_files and any(pat in name for pat in exclude_files):
            continue
        filtered.append(result)
    return filtered, len(results) - len(filtered)


def build_file_filter(vault_path: Path, include_paths: list, include_files: list) -> Optional[list[str]]:
    """Pre-filter vault files by path/filename before semantic search.

    Only handles the simple path/file include case — the common fast-path.
    Property/tag pre-filtering requires reading every file and is left to
    post-retrieval filters.
    """
    if not include_paths and not include_files:
        return None

    matched = []
    for f in vault_path.rglob("*.md"):
        rel = str(f.relative_to(vault_path))
        if include_paths and not any(p in rel for p in include_paths):
            continue
        if include_files and not any(p in f.name for p in include_files):
            continue
        matched.append(rel)

    logger.info(f"File filter: {len(matched)} files matched")
    return matched
