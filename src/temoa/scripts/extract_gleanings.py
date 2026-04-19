#!/usr/bin/env python3
"""
Gleanings Extraction Script

Extracts gleanings from daily notes and creates individual notes in L/Gleanings/.

Usage:
    python scripts/extract_gleanings.py --vault-path /path/to/vault [--dry-run]
"""

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse
from html.parser import HTMLParser
import urllib.error

# Add src to path so we can import gleanings module
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from temoa.gleanings import GleaningStatusManager, GleaningStatus
from temoa.normalizers import NormalizerRegistry


class TitleParser(HTMLParser):
    """Simple HTML parser to extract <title> and <meta description> tags."""

    def __init__(self):
        super().__init__()
        self.title = None
        self.description = None
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == 'title':
            self.in_title = True
        elif tag == 'meta':
            attrs_dict = dict(attrs)
            name = attrs_dict.get('name', '').lower()
            prop = attrs_dict.get('property', '').lower()
            content = attrs_dict.get('content', '').strip()
            if content and self.description is None:
                if name == 'description' or prop == 'og:description':
                    self.description = content

    def handle_data(self, data):
        if self.in_title:
            self.title = data.strip()
            self.in_title = False


def fetch_github_title_and_description(url: str, timeout: int = 5) -> tuple[Optional[str], Optional[str]]:
    """
    Fetch title and description for a github.com/user/repo URL via the GitHub API.

    Returns (title, description) where title is 'user/repo' and description is
    the repo description from the API, or (None, None) on failure.
    """
    path = urlparse(url).path.strip("/")
    parts = [p for p in path.split("/") if p]
    if len(parts) < 2:
        return None, None

    api_url = f"https://api.github.com/repos/{parts[0]}/{parts[1]}"
    try:
        request = urllib.request.Request(
            api_url,
            headers={"User-Agent": "temoa/0.1", "Accept": "application/vnd.github+json"}
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.load(response)
            title = data.get("full_name") or f"{parts[0]}/{parts[1]}"
            description = data.get("description") or ""
            return title, description
    except Exception:
        return None, None


def fetch_youtube_title(url: str, timeout: int = 5) -> Optional[str]:
    """
    Fetch video title for a youtube.com URL via the oEmbed API.

    Returns the video title, or None on failure.
    """
    oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
    try:
        request = urllib.request.Request(
            oembed_url,
            headers={"User-Agent": "temoa/0.1"}
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.load(response)
            return data.get("title") or None
    except Exception:
        return None


def _fetch_html_title_and_description(url: str, timeout: int = 5) -> tuple[Optional[str], Optional[str]]:
    """Fetch title and meta description from a URL's HTML. Returns (title, description)."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content = response.read(65536).decode('utf-8', errors='ignore')
            parser = TitleParser()
            parser.feed(content)
            return parser.title or None, parser.description or None
    except Exception:
        return None, None


def fetch_title_from_url(url: str, timeout: int = 5) -> Optional[str]:
    """
    Fetch page title from URL.

    For github.com/user/repo URLs, uses the GitHub API.
    For youtube.com URLs, uses the oEmbed API.
    For everything else, reads up to 64KB of HTML to find the <title> tag.

    Returns the page title, or None if fetch fails.
    """
    parsed = urlparse(url)
    if "github.com" in parsed.netloc:
        title, _ = fetch_github_title_and_description(url, timeout=timeout)
        return title

    if "youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc:
        return fetch_youtube_title(url, timeout=timeout)

    title, _ = _fetch_html_title_and_description(url, timeout=timeout)
    return title


def fetch_description_from_url(url: str, timeout: int = 5) -> Optional[str]:
    """
    Fetch a description for a URL using the best available method.

    - github.com: repo description from GitHub API
    - youtube.com/youtu.be: None (no description in oEmbed)
    - everything else: <meta name="description"> or <meta property="og:description">

    Returns the description string, or None if unavailable.
    """
    parsed = urlparse(url)
    if "github.com" in parsed.netloc:
        _, description = fetch_github_title_and_description(url, timeout=timeout)
        return description or None

    if "youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc:
        return None

    _, description = _fetch_html_title_and_description(url, timeout=timeout)
    return description


class Gleaning:
    """Represents a single gleaning."""

    def __init__(
        self,
        title: str,
        url: str,
        description: str,
        date: str,
        source_file: str,
        gleaning_id: Optional[str] = None,
        status: GleaningStatus = "active",
        reason: Optional[str] = None
    ):
        self.title = title
        self.url = url
        self.description = description
        self.date = date
        self.source_file = source_file
        self.domain = urlparse(url).netloc
        self.gleaning_id = gleaning_id or self._generate_id()
        self.status = status
        self.reason = reason

    def _generate_id(self) -> str:
        """Generate unique ID from URL."""
        return hashlib.md5(self.url.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.gleaning_id,
            "title": self.title,
            "url": self.url,
            "description": self.description,
            "date": self.date,
            "domain": self.domain,
            "source_file": self.source_file,
            "extracted_at": datetime.now().isoformat()
        }

    def to_markdown(self) -> str:
        """Convert to markdown note format."""
        # Quote title for YAML safety (handles colons, quotes, etc.)
        # ensure_ascii=False keeps emojis as literal Unicode (surrogate pairs break YAML)
        quoted_title = json.dumps(self.title, ensure_ascii=False)

        # Quote description for YAML safety
        quoted_description = json.dumps(self.description, ensure_ascii=False) if self.description else '""'

        # Quote reason for YAML safety
        quoted_reason = json.dumps(self.reason, ensure_ascii=False) if self.reason else '""'

        # Build frontmatter
        frontmatter_lines = [
            f"title: {quoted_title}",
            f"url: {self.url}",
            f"domain: {self.domain}",
            f"created: {self.date}",
            f"source: {self.source_file}",
            f"gleaning_id: {self.gleaning_id}",
            f"status: {self.status}",
            f"type: gleaning",
            f"description: {quoted_description}"
        ]

        # Add reason only if inactive
        if self.status == "inactive" and self.reason:
            frontmatter_lines.append(f"reason: {quoted_reason}")

        frontmatter = "\n".join(frontmatter_lines)

        return f"""---
{frontmatter}
---

# {self.title}

{self.description}

## Link

[{self.title}]({self.url})

## Source

Gleaned from [[{Path(self.source_file).stem}]] on {self.date}
"""


class GleaningsExtractor:
    """Extracts gleanings from daily notes."""

    # Regex patterns for different gleaning formats

    # Pattern 1: Markdown link - [Title](URL)  [HH:MM]
    MARKDOWN_LINK_PATTERN = re.compile(
        r'^-\s+\[([^\]]+)\]\(([^)]+)\)',
        re.MULTILINE
    )

    # Pattern 2: Naked URL with bullet - https://...
    NAKED_URL_BULLET_PATTERN = re.compile(
        r'^-\s+(https?://[^\s]+)',
        re.MULTILINE
    )

    # Pattern 3: Naked URL bare (no bullet) - https://...
    NAKED_URL_BARE_PATTERN = re.compile(
        r'^(https?://[^\s]+)$',
        re.MULTILINE
    )

    # Pattern for timestamp - [HH:MM]
    TIMESTAMP_PATTERN = re.compile(r'\[(\d{2}:\d{2})\]')

    # Regex to find Gleanings section
    SECTION_PATTERN = re.compile(
        r'^##\s+Gleanings\s*$',
        re.MULTILINE
    )

    def __init__(self, vault_path: Path, state_file: Optional[Path] = None):
        self.vault_path = Path(vault_path).expanduser()

        # Validate vault path exists
        if not self.vault_path.exists():
            raise FileNotFoundError(
                f"Vault path does not exist: {self.vault_path}\n"
                f"Please check the path and try again."
            )

        if not self.vault_path.is_dir():
            raise NotADirectoryError(
                f"Vault path is not a directory: {self.vault_path}"
            )

        self.state_file = state_file or (self.vault_path / ".temoa" / "extraction_state.json")
        self.state, migrated = self._load_state()

        # If migration happened, save immediately to persist it
        if migrated:
            self._save_state()

        # Initialize status manager
        self.status_manager = GleaningStatusManager(self.vault_path / ".temoa")
        
        # Initialize normalizer registry
        self.normalizer_registry = NormalizerRegistry()

    def _load_state(self) -> tuple[Dict, bool]:
        """Load extraction state. Returns (state, migrated)."""
        migrated = False
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                # Migrate old format (processed_files list) to new format (dict with mtime)
                if isinstance(state.get("processed_files"), list):
                    # Convert list to dict, no mtime available for old entries
                    state["processed_files"] = {
                        path: None for path in state["processed_files"]
                    }
                    migrated = True
                return state, migrated
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_run": None,
            "extracted_gleanings": {},
            "processed_files": {}  # Now dict: {path: mtime}
        }, False

    def _save_state(self):
        """Save extraction state."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state["last_run"] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def find_daily_notes(self, incremental: bool = True) -> List[Path]:
        """Find daily notes to process."""
        daily_notes = []
        seen_paths = set()  # Track unique paths to avoid duplicates on case-insensitive filesystems

        # Search for daily notes (capital-case only)
        # Note: On case-insensitive filesystems (macOS), lowercase patterns
        # would match the same files, causing confusing output
        patterns = [
            "Daily/**/*.md",
            "Journal/**/*.md",
        ]

        for pattern in patterns:
            for note in self.vault_path.glob(pattern):
                # Resolve to absolute path to handle case-insensitive filesystem duplicates
                note_resolved = note.resolve()

                # Skip if we've already seen this file (case-insensitive duplicate)
                if note_resolved in seen_paths:
                    continue

                # In incremental mode, check if file was modified since last processing
                if incremental:
                    rel_path = str(note.relative_to(self.vault_path))
                    last_mtime = self.state["processed_files"].get(rel_path)
                    current_mtime = note.stat().st_mtime

                    # Skip if file hasn't been modified since last extraction
                    if last_mtime is not None and current_mtime <= last_mtime:
                        continue

                seen_paths.add(note_resolved)
                daily_notes.append(note)

        return daily_notes

    def extract_from_note(self, note_path: Path, dry_run: bool = False) -> List[Gleaning]:
        """Extract gleanings from a single note."""
        gleanings = []

        with open(note_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the Gleanings section
        section_match = self.SECTION_PATTERN.search(content)
        if not section_match:
            return gleanings

        # Extract section after "## Gleanings"
        section_start = section_match.end()

        # Find next section (## Something) or end of file
        next_section = re.search(r'^##\s+', content[section_start:], re.MULTILINE)
        if next_section:
            section_end = section_start + next_section.start()
            section_content = content[section_start:section_end]
        else:
            section_content = content[section_start:]

        # Extract date from frontmatter or filename
        base_date = self._extract_date(note_path, content)

        # Split section into lines for easier processing
        lines = section_content.split('\n')

        # Find all gleanings in section
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and comment lines (lines starting with >)
            if not line or (line.startswith('>') and not lines[i-1] if i > 0 else False):
                i += 1
                continue

            title = None
            url = None
            timestamp = None
            prefetched_description = None  # Set when API fetch returns a description

            # Try Pattern 1: Markdown link - [Title](URL)
            markdown_match = re.match(r'^-\s+\[([^\]]+)\]\(([^)]+)\)', line)
            if markdown_match:
                title = markdown_match.group(1).strip()
                url = markdown_match.group(2).strip()

                # Extract timestamp if present
                timestamp_match = self.TIMESTAMP_PATTERN.search(line)
                if timestamp_match:
                    timestamp = timestamp_match.group(1)

            # Try Pattern 2: Naked URL with bullet - https://...
            elif re.match(r'^-\s+(https?://)', line):
                naked_bullet_match = re.match(r'^-\s+(https?://[^\s]+)', line)
                if naked_bullet_match:
                    url = naked_bullet_match.group(1).strip()

                    # Extract timestamp if present
                    timestamp_match = self.TIMESTAMP_PATTERN.search(line)
                    if timestamp_match:
                        timestamp = timestamp_match.group(1)

                    # Fetch title from URL (skip during dry run)
                    if dry_run:
                        parsed = urlparse(url)
                        title = f"[{parsed.netloc or 'Title will be fetched'}]"
                    else:
                        print(f"  Fetching title for naked URL: {url[:60]}...")
                        netloc = urlparse(url).netloc
                        if "github.com" in netloc:
                            title, prefetched_description = fetch_github_title_and_description(url)
                        elif "youtube.com" in netloc or "youtu.be" in netloc:
                            title = fetch_youtube_title(url)
                        else:
                            title, prefetched_description = _fetch_html_title_and_description(url)

            # Try Pattern 3: Naked URL bare (no bullet) - https://...
            elif re.match(r'^https?://', line):
                naked_bare_match = re.match(r'^(https?://[^\s]+)', line)
                if naked_bare_match:
                    url = naked_bare_match.group(1).strip()

                    # Extract timestamp if present
                    timestamp_match = self.TIMESTAMP_PATTERN.search(line)
                    if timestamp_match:
                        timestamp = timestamp_match.group(1)

                    # Fetch title from URL (skip during dry run)
                    if dry_run:
                        parsed = urlparse(url)
                        title = f"[{parsed.netloc or 'Title will be fetched'}]"
                    else:
                        print(f"  Fetching title for naked URL: {url[:60]}...")
                        netloc = urlparse(url).netloc
                        if "github.com" in netloc:
                            title, prefetched_description = fetch_github_title_and_description(url)
                        elif "youtube.com" in netloc or "youtu.be" in netloc:
                            title = fetch_youtube_title(url)
                        else:
                            title, prefetched_description = _fetch_html_title_and_description(url)

            # If we found a gleaning, extract description and create object
            # title may be None for naked URLs where fetch failed; normalizer handles fallback
            if url:
                # Collect ALL consecutive description lines (lines starting with >)
                description_lines = []
                j = i + 1
                while j < len(lines):
                    desc_line = lines[j].strip()
                    if desc_line.startswith('>'):
                        # Remove leading > and whitespace
                        desc_text = desc_line[1:].strip()
                        if desc_text:  # Only add non-empty lines
                            description_lines.append(desc_text)
                        j += 1
                    elif not desc_line:
                        # Empty line - might be continuation, check next line
                        if j + 1 < len(lines) and lines[j + 1].strip().startswith('>'):
                            description_lines.append('')  # Preserve paragraph break
                            j += 1
                        else:
                            break
                    else:
                        # Non-description line, stop collecting
                        break

                description = '\n'.join(description_lines)

                # If no user-written description but API gave us one, use it
                if not description and prefetched_description:
                    description = prefetched_description

                # Build date with timestamp if available
                date = base_date
                if timestamp:
                    date = f"{base_date} {timestamp}"

                # Normalize title and description based on URL domain
                title, description = self.normalizer_registry.normalize(url, title, description)

                # Generate ID to check status and reason
                gleaning_id = hashlib.md5(url.encode()).hexdigest()[:12]
                status = self.status_manager.get_status(gleaning_id)

                # Get reason from status record if exists
                reason = None
                status_record = self.status_manager.get_gleaning_record(gleaning_id)
                if status_record and "reason" in status_record:
                    reason = status_record["reason"]

                gleaning = Gleaning(
                    title=title,
                    url=url,
                    description=description,
                    date=date,
                    source_file=str(note_path.relative_to(self.vault_path)),
                    gleaning_id=gleaning_id,
                    status=status,
                    reason=reason
                )

                gleanings.append(gleaning)

                # Skip past description lines we already processed
                i = j
                continue

            i += 1

        return gleanings

    def _extract_date(self, note_path: Path, content: str) -> str:
        """Extract date from frontmatter or filename."""
        # Try frontmatter first
        frontmatter_match = re.search(r'^date:\s*(\d{4}-\d{2}-\d{2})', content, re.MULTILINE)
        if frontmatter_match:
            return frontmatter_match.group(1)

        # Try filename (YYYY-MM-DD pattern)
        filename_match = re.search(r'(\d{4}-\d{2}-\d{2})', note_path.stem)
        if filename_match:
            return filename_match.group(1)

        # Fallback to file modification time
        mtime = datetime.fromtimestamp(note_path.stat().st_mtime)
        return mtime.strftime('%Y-%m-%d')

    def create_gleaning_note(self, gleaning: Gleaning, output_dir: Path, dry_run: bool = False):
        """Create individual gleaning note."""
        output_file = output_dir / f"{gleaning.gleaning_id}.md"

        if dry_run:
            print(f"[DRY RUN] Would create: {output_file.relative_to(self.vault_path)}")
            return

        output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(gleaning.to_markdown())

        print(f"Created: {output_file.relative_to(self.vault_path)}")

    def extract_all(self, incremental: bool = True, dry_run: bool = False, log_format: bool = False):
        """Extract all gleanings from daily notes."""
        output_dir = self.vault_path / "L" / "Gleanings"

        # In full mode, clear existing state to start fresh
        if not incremental and not dry_run:
            if not log_format:
                print("Full mode: Clearing existing extraction state")
            self.state = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "last_run": None,
                "extracted_gleanings": {},
                "processed_files": []
            }
            if not log_format:
                print()

        if not log_format:
            print(f"Vault path: {self.vault_path}")
            print(f"Output directory: {output_dir.relative_to(self.vault_path)}")
            print(f"Mode: {'Incremental' if incremental else 'Full (starting fresh)'}")
            print(f"Dry run: {dry_run}")
            print()

        # Find notes to process
        daily_notes = self.find_daily_notes(incremental=incremental)
        if not log_format:
            print(f"Found {len(daily_notes)} daily notes to process")
            print()

        total_gleanings = 0
        new_gleanings = 0
        duplicate_gleanings = 0

        for note_path in daily_notes:
            gleanings = self.extract_from_note(note_path, dry_run=dry_run)

            if gleanings and not log_format:
                print(f"Processing: {note_path.relative_to(self.vault_path)} ({len(gleanings)} gleanings)")

            for gleaning in gleanings:
                total_gleanings += 1

                # Check for duplicates (only in incremental mode or dry-run)
                if gleaning.gleaning_id in self.state["extracted_gleanings"]:
                    duplicate_gleanings += 1
                    if not log_format:
                        print(f"  - DUPLICATE: {gleaning.title[:60]}... (ID: {gleaning.gleaning_id})")
                    continue

                # Create gleaning note
                self.create_gleaning_note(gleaning, output_dir, dry_run=dry_run)
                new_gleanings += 1

                # Update state
                if not dry_run:
                    self.state["extracted_gleanings"][gleaning.gleaning_id] = gleaning.to_dict()

            # Mark file as processed with its modification time
            if not dry_run:
                rel_path = str(note_path.relative_to(self.vault_path))
                self.state["processed_files"][rel_path] = note_path.stat().st_mtime

        # Save state
        if not dry_run:
            self._save_state()

        # Summary
        if log_format:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            mode = "dry-run" if dry_run else ("full" if not incremental else "incremental")
            print(f"## {ts} | extract\n+{new_gleanings} new, {duplicate_gleanings} dupes, {total_gleanings} found, {len(daily_notes)} files | {mode}")
        else:
            print()
            print("=" * 60)
            print(f"Extraction {'preview' if dry_run else 'complete'}!")
            print(f"Total gleanings found: {total_gleanings}")
            print(f"New gleanings {'would be created' if dry_run else 'created'}: {new_gleanings}")
            print(f"Duplicates skipped: {duplicate_gleanings}")
            print(f"Files processed: {len(daily_notes)}")
            print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Extract gleanings from daily notes")
    parser.add_argument(
        "--vault-path",
        type=Path,
        required=True,
        help="Path to Obsidian vault"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Process all files (not just new ones)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be extracted without creating files"
    )
    parser.add_argument(
        "--log-format",
        action="store_true",
        help="Output a single timestamped markdown line instead of verbose output"
    )

    args = parser.parse_args()

    try:
        extractor = GleaningsExtractor(args.vault_path)
        extractor.extract_all(incremental=not args.full, dry_run=args.dry_run, log_format=args.log_format)
    except (FileNotFoundError, NotADirectoryError) as e:
        if args.log_format:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            print(f"## {ts} | extract | ERROR: {e}")
        else:
            print(f"Error: {e}", file=__import__('sys').stderr)
        return 1
    except Exception as e:
        if args.log_format:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            print(f"## {ts} | extract | ERROR: {e}")
        else:
            print(f"Unexpected error: {e}", file=__import__('sys').stderr)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
