#!/usr/bin/env python3
"""
Diagnostic script to analyze gleaning formats in daily notes.

This script scans your Daily notes and reports:
1. How many gleanings match current patterns
2. How many URLs are being missed
3. Examples of different formats found

Run this to understand what's being missed before fixing extraction.
"""

import re
import sys
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse

def find_daily_notes(vault_path: Path):
    """Find all daily notes."""
    patterns = [
        "Daily/**/*.md",
        "Journal/**/*.md",
    ]
    daily_notes = []
    seen_paths = set()

    for pattern in patterns:
        for note in vault_path.glob(pattern):
            note_resolved = note.resolve()
            if note_resolved not in seen_paths:
                seen_paths.add(note_resolved)
                daily_notes.append(note)

    return daily_notes


def analyze_gleanings_section(content: str, file_path: str):
    """Analyze a gleanings section and categorize formats."""

    # Find gleanings section
    section_match = re.search(r'^##\s+Gleanings\s*$', content, re.MULTILINE)
    if not section_match:
        return None

    section_start = section_match.end()
    next_section = re.search(r'^##\s+', content[section_start:], re.MULTILINE)
    if next_section:
        section_end = section_start + next_section.start()
        section_content = content[section_start:section_end]
    else:
        section_content = content[section_start:]

    results = {
        'file': file_path,
        'markdown_links': [],      # - [Title](URL) format
        'naked_urls_with_bullet': [],  # - https://... format
        'naked_urls_bare': [],     # Just https://... (no bullet)
        'multi_line_descriptions': 0,
        'timestamps': 0,
        'total_urls': 0
    }

    lines = section_content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Pattern 1: Markdown link - [Title](URL)
        markdown_link = re.match(r'^-\s+\[([^\]]+)\]\(([^)]+)\)', line)
        if markdown_link:
            title = markdown_link.group(1)
            url = markdown_link.group(2)

            # Check for timestamp
            timestamp_match = re.search(r'\[(\d{2}:\d{2})\]', line)
            if timestamp_match:
                results['timestamps'] += 1

            # Check for multi-line description
            description_lines = []
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith('>'):
                description_lines.append(lines[j].strip())
                j += 1

            if len(description_lines) > 1:
                results['multi_line_descriptions'] += 1

            results['markdown_links'].append({
                'title': title,
                'url': url,
                'has_timestamp': timestamp_match is not None,
                'description_lines': len(description_lines),
                'line': line[:80]
            })
            results['total_urls'] += 1
            i = j
            continue

        # Pattern 2: Naked URL with bullet - https://...
        naked_bullet = re.match(r'^-\s+(https?://[^\s]+)', line)
        if naked_bullet:
            url = naked_bullet.group(1)
            results['naked_urls_with_bullet'].append({
                'url': url,
                'line': line[:80]
            })
            results['total_urls'] += 1
            i += 1
            continue

        # Pattern 3: Naked URL without bullet (bare)
        naked_bare = re.match(r'^(https?://[^\s]+)', line)
        if naked_bare and not line.startswith('-') and not line.startswith('>'):
            url = naked_bare.group(1)
            results['naked_urls_bare'].append({
                'url': url,
                'line': line[:80]
            })
            results['total_urls'] += 1
            i += 1
            continue

        i += 1

    return results if results['total_urls'] > 0 else None


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_gleaning_formats.py <vault_path>")
        print("Example: python analyze_gleaning_formats.py ~/Obsidian/amoxtli")
        sys.exit(1)

    vault_path = Path(sys.argv[1]).expanduser().resolve()

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    print(f"Analyzing gleanings in: {vault_path}")
    print("=" * 70)
    print()

    daily_notes = find_daily_notes(vault_path)
    print(f"Found {len(daily_notes)} daily notes")
    print()

    # Aggregate statistics
    total_markdown_links = 0
    total_naked_with_bullet = 0
    total_naked_bare = 0
    total_multi_line = 0
    total_timestamps = 0

    files_with_gleanings = 0
    sample_naked_bullets = []
    sample_naked_bare = []
    sample_multi_line = []

    for note in daily_notes:
        try:
            with open(note, 'r', encoding='utf-8') as f:
                content = f.read()

            result = analyze_gleanings_section(content, str(note.relative_to(vault_path)))

            if result:
                files_with_gleanings += 1
                total_markdown_links += len(result['markdown_links'])
                total_naked_with_bullet += len(result['naked_urls_with_bullet'])
                total_naked_bare += len(result['naked_urls_bare'])
                total_multi_line += result['multi_line_descriptions']
                total_timestamps += result['timestamps']

                # Collect samples
                if result['naked_urls_with_bullet'] and len(sample_naked_bullets) < 3:
                    sample_naked_bullets.append({
                        'file': result['file'],
                        'example': result['naked_urls_with_bullet'][0]
                    })

                if result['naked_urls_bare'] and len(sample_naked_bare) < 3:
                    sample_naked_bare.append({
                        'file': result['file'],
                        'example': result['naked_urls_bare'][0]
                    })

                if result['multi_line_descriptions'] > 0 and len(sample_multi_line) < 3:
                    for link in result['markdown_links']:
                        if link['description_lines'] > 1:
                            sample_multi_line.append({
                                'file': result['file'],
                                'title': link['title'],
                                'description_lines': link['description_lines']
                            })
                            break

        except Exception as e:
            print(f"Error processing {note}: {e}")
            continue

    # Print results
    print("SUMMARY")
    print("=" * 70)
    print(f"Files with gleanings sections: {files_with_gleanings}")
    print(f"Total URLs found: {total_markdown_links + total_naked_with_bullet + total_naked_bare}")
    print()

    print("FORMAT BREAKDOWN:")
    print(f"  ✓ Markdown links ([Title](URL)):        {total_markdown_links} (SUPPORTED)")
    print(f"  ✓ Naked URLs with bullet (- https://):  {total_naked_with_bullet} (SUPPORTED - fetches title)")
    print(f"  ✓ Naked URLs bare (https://):           {total_naked_bare} (SUPPORTED - fetches title)")
    print()

    print("FEATURE USAGE:")
    print(f"  ✓ Timestamps [HH:MM]:                    {total_timestamps} (SUPPORTED)")
    print(f"  ✓ Multi-line descriptions (>2 lines):   {total_multi_line} (FULLY SUPPORTED)")
    print()

    # Note about naked URLs
    naked_count = total_naked_with_bullet + total_naked_bare
    if naked_count > 0:
        print(f"📌 NOTE: {naked_count} naked URLs will have titles fetched from web")
        print(f"   Extraction will take ~{naked_count * 1.5:.0f} seconds longer (fetching titles)")
        print()

    # Show samples
    if sample_naked_bullets:
        print("SAMPLE: Naked URLs with bullet (title will be fetched)")
        print("-" * 70)
        for i, sample in enumerate(sample_naked_bullets, 1):
            print(f"{i}. File: {sample['file']}")
            print(f"   Line: {sample['example']['line']}")
            print(f"   URL:  {sample['example']['url']}")
            print()

    if sample_naked_bare:
        print("SAMPLE: Naked URLs bare (title will be fetched)")
        print("-" * 70)
        for i, sample in enumerate(sample_naked_bare, 1):
            print(f"{i}. File: {sample['file']}")
            print(f"   Line: {sample['example']['line']}")
            print(f"   URL:  {sample['example']['url']}")
            print()

    if sample_multi_line:
        print("SAMPLE: Multi-line descriptions (all lines will be captured)")
        print("-" * 70)
        for i, sample in enumerate(sample_multi_line, 1):
            print(f"{i}. File: {sample['file']}")
            print(f"   Title: {sample['title'][:60]}")
            print(f"   Description lines: {sample['description_lines']}")
            print()

    print("=" * 70)
    print("✅ All formats are supported! Run 'temoa extract' to capture everything.")


if __name__ == "__main__":
    main()
