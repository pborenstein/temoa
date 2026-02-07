#!/usr/bin/env python3
"""
Transform GitHub gleanings to new format:
- Short titles (owner/repo)
- Rich descriptions from README
- Tags in YAML frontmatter
- No H1 headings
- Delete github_readme_excerpt field
"""

import re
import sys
from pathlib import Path
from typing import Optional
import requests
import time
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def get_github_readme(url: str) -> Optional[str]:
    """
    Fetch README content from GitHub repo.

    Args:
        url: GitHub URL (any format)

    Returns:
        Plain text from README, or None if not found
    """
    # Extract owner/repo from various GitHub URL formats
    patterns = [
        r'github\.com/([^/]+)/([^/?#]+)',
        r'raw\.githubusercontent\.com/([^/]+)/([^/]+)',
    ]

    owner, repo = None, None
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            owner, repo = match.groups()
            # Clean up repo name (remove .git, query params, etc)
            repo = re.sub(r'\.(git|md)$', '', repo)
            repo = re.split(r'[?#]', repo)[0]
            break

    if not owner or not repo:
        return None

    # Try to fetch README from GitHub API
    api_url = f'https://api.github.com/repos/{owner}/{repo}/readme'

    try:
        response = requests.get(api_url, headers={'Accept': 'application/vnd.github.raw'}, timeout=10)
        if response.status_code == 200:
            return response.text
        return None
    except Exception as e:
        print(f"  ⚠️  Failed to fetch README for {owner}/{repo}: {e}")
        return None


def extract_description_from_readme(readme_text: str, max_sentences: int = 3) -> Optional[str]:
    """
    Extract meaningful description from README text.

    Skips:
    - HTML/markdown images
    - Badges
    - Headers
    - Empty lines
    - URLs (standalone)

    Returns first few sentences of actual content.
    """
    if not readme_text:
        return None

    lines = readme_text.split('\n')
    sentences = []

    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Skip standalone URLs (images, assets, etc)
        if re.match(r'^https?://', line):
            continue

        # Skip images/badges
        if re.match(r'[!\[<]', line):
            continue

        # Skip markdown headers
        if line.startswith('#'):
            continue

        # Skip horizontal rules
        if re.match(r'^[-*_]{3,}$', line):
            continue

        # Skip code blocks
        if line.startswith('```'):
            continue

        # Skip section headers (## something)
        if re.match(r'^##', line):
            continue

        # Skip emojis/icons at start
        if re.match(r'^[\U0001F300-\U0001F9FF]', line):
            continue

        # Clean up markdown formatting
        clean_line = line
        clean_line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_line)  # Remove links
        clean_line = re.sub(r'[*_`]', '', clean_line)  # Remove formatting
        clean_line = re.sub(r'[\U0001F300-\U0001F9FF]', '', clean_line)  # Remove emojis
        clean_line = re.sub(r'\s+', ' ', clean_line).strip()  # Normalize whitespace

        # Skip if it's just a section marker or too short
        if not clean_line or len(clean_line) < 30:
            continue

        # Skip common non-descriptive phrases
        if clean_line.lower().startswith(('installation', 'usage', 'requirements', 'features', 'getting started', 'you can install', 'to install', 'install')):
            continue

        # Stop if we hit installation/usage instructions
        if any(word in clean_line.lower() for word in ['pip install', 'npm install', 'docker', 'requirements.txt', 'package.json']):
            # Only break if we already have some content
            if sentences:
                break
            continue

        sentences.append(clean_line)

        if len(sentences) >= max_sentences:
            break

    if sentences:
        description = ' '.join(sentences)
        # Ensure it ends with period
        if not description.endswith('.'):
            description += '.'
        return description

    return None


def select_tags(github_topics: list[str], max_tags: int = 7) -> list[str]:
    """
    Select most relevant tags from github_topics.

    Prioritizes:
    - Specific technology/domain terms
    - Avoids generic terms like 'list', 'directory', 'awesome-list'
    """
    # Generic terms to deprioritize
    generic = {'list', 'directory', 'awesome-list', 'resources', 'collection', 'curated'}

    # Split into priority groups
    specific = [t for t in github_topics if t not in generic]
    fallback = [t for t in github_topics if t in generic]

    # Take specific first, then generic if needed
    selected = specific[:max_tags]
    if len(selected) < max_tags:
        selected.extend(fallback[:max_tags - len(selected)])

    return selected[:max_tags]


def extract_short_title(current_title: str, url: str) -> str:
    """
    Extract owner/repo from current long title or URL.

    Examples:
        'owner/repo: long description' -> 'owner/repo'
        'owner/repo' -> 'owner/repo'
        '' (empty) -> extract from URL
    """
    # If title exists, try to extract owner/repo pattern
    if current_title:
        match = re.match(r'^([^/:]+/[^/:]+)', current_title)
        if match:
            return match.group(1)

    # Fallback: extract from URL
    match = re.search(r'github\.com/([^/]+/[^/?#]+)', url)
    if match:
        owner_repo = match.group(1)
        # Clean up
        owner_repo = re.sub(r'\.(git|md)$', '', owner_repo)
        return owner_repo

    return current_title or 'unknown'


def transform_github_gleaning(file_path: Path, dry_run: bool = False) -> bool:
    """
    Transform a single GitHub gleaning file.

    Returns:
        True if transformation was successful, False otherwise
    """
    try:
        # Parse existing gleaning
        content = file_path.read_text()

        # Check if it's a GitHub gleaning
        if 'domain: github.com' not in content:
            return False

        # Parse frontmatter and body
        parts = content.split('---', 2)
        if len(parts) < 3:
            print(f"  ⚠️  Invalid format: {file_path.name}")
            return False

        frontmatter = yaml.safe_load(parts[1])

        # Extract short title
        url = frontmatter.get('url', '')
        old_title = frontmatter.get('title', '')
        new_title = extract_short_title(old_title, url)

        # Get README for better description
        readme_text = get_github_readme(url)

        new_description = frontmatter.get('description', '')
        if readme_text:
            extracted = extract_description_from_readme(readme_text)
            if extracted and len(extracted) > len(new_description):
                new_description = extracted
                if not dry_run:
                    print(f"     Enhanced description from README")
        elif not dry_run:
            print(f"     Could not fetch README, keeping current description")

        # Select tags from github_topics (if available)
        github_topics = frontmatter.get('github_topics', [])
        tags = select_tags(github_topics) if github_topics else []

        # Update frontmatter
        frontmatter['title'] = new_title
        frontmatter['description'] = new_description
        if tags:
            frontmatter['tags'] = tags

        # Remove github_readme_excerpt
        if 'github_readme_excerpt' in frontmatter:
            del frontmatter['github_readme_excerpt']

        # Build new body (no H1 heading)
        stars = frontmatter.get('github_stars', 0)
        language = frontmatter.get('github_language', 'Unknown')
        last_push = frontmatter.get('github_last_push', '')

        # Format date (just date part, not time)
        if last_push:
            last_push = str(last_push).split()[0]  # Take just YYYY-MM-DD

        new_body = f"""{new_description}

**{stars} ★** · {language} · Last updated {last_push}

## Link

[{new_title}]({url})

## Source

Gleaned from [[{frontmatter.get('source', '').replace('.md', '')}]] on {frontmatter.get('created', '')}
"""

        # Reconstruct file
        new_content = '---\n'
        new_content += yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)
        new_content += '---\n\n'
        new_content += new_body

        if dry_run:
            print(f"  📝 Would transform: {file_path.name}")
            print(f"     Title: {old_title} -> {new_title}")
            print(f"     Description: {len(frontmatter.get('description', ''))} -> {len(new_description)} chars")
            print(f"     Tags: {len(tags)} selected")
            return True

        # Write transformed file
        file_path.write_text(new_content)
        print(f"  ✓ Transformed: {file_path.name}")
        return True

    except Exception as e:
        print(f"  ❌ Error transforming {file_path.name}: {e}")
        return False


def main():
    """Transform all GitHub gleanings."""
    import argparse

    parser = argparse.ArgumentParser(description='Transform GitHub gleanings to new format')
    parser.add_argument('--vault', type=Path, required=True, help='Path to vault')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--limit', type=int, help='Limit number of files to process (for testing)')

    args = parser.parse_args()

    # Find all GitHub gleanings
    gleanings_dir = args.vault / 'L' / 'Gleanings'
    if not gleanings_dir.exists():
        print(f"❌ Gleanings directory not found: {gleanings_dir}")
        return 1

    # Find all markdown files with github.com URLs
    github_gleanings = []
    for md_file in gleanings_dir.glob('*.md'):
        content = md_file.read_text()
        if 'domain: github.com' in content:
            github_gleanings.append(md_file)

    print(f"Found {len(github_gleanings)} GitHub gleanings")

    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No files will be modified\n")

    # Process files
    processed = 0
    successful = 0

    for gleaning_file in github_gleanings:
        if args.limit and processed >= args.limit:
            break

        if transform_github_gleaning(gleaning_file, dry_run=args.dry_run):
            successful += 1

        processed += 1

        # Rate limit GitHub API
        if not args.dry_run and processed % 10 == 0:
            print(f"  ⏸️  Pausing to respect GitHub API rate limits...")
            time.sleep(2)

    print(f"\n✓ Complete: {successful}/{processed} gleanings transformed")

    if args.dry_run:
        print("\nRun without --dry-run to apply changes")

    return 0


if __name__ == '__main__':
    sys.exit(main())
