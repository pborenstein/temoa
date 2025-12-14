"""
Vault content reader for the Synthesis Project.
"""
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from tqdm import tqdm
from nahuatl_frontmatter import parse_content

logger = logging.getLogger(__name__)


class VaultContent:
    """Represents content from a single vault file."""

    def __init__(
        self,
        file_path: Path,
        title: str,
        content: str,
        vault_root: Path,
        frontmatter: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ):
        self.file_path = file_path
        self.relative_path = str(file_path.relative_to(vault_root))
        self.title = title
        self.content = content
        self.frontmatter = frontmatter or {}
        self.tags = tags or []
        self.created_date = frontmatter.get('created') if frontmatter else None
        self.modified_date = file_path.stat().st_mtime
    
    def __repr__(self):
        return f"VaultContent('{self.relative_path}', {len(self.content)} chars)"


class VaultReader:
    """Reads and processes vault content for embedding generation."""
    
    def __init__(self, vault_root: Path):
        """Initialize with vault root directory."""
        self.vault_root = Path(vault_root)
        if not self.vault_root.exists():
            raise ValueError(f"Vault root does not exist: {vault_root}")
        
        logger.info(f"VaultReader initialized for: {self.vault_root}")
    
    def discover_files(self, include_patterns: List[str] = None, exclude_patterns: List[str] = None) -> List[Path]:
        """Discover all markdown files in the vault.
        
        Args:
            include_patterns: Glob patterns for files to include
            exclude_patterns: Glob patterns for files to exclude
            
        Returns:
            List of markdown file paths
        """
        if include_patterns is None:
            include_patterns = ["**/*.md"]
        
        if exclude_patterns is None:
            exclude_patterns = [
                ".obsidian/**",
                ".tools/**", 
                ".trash/**",
                ".claude/**",
                "Utilities/**",
                "**/.DS_Store",
                "**/.venv/**",
                "**/node_modules/**"
            ]
        
        all_files = []
        for pattern in include_patterns:
            all_files.extend(self.vault_root.glob(pattern))
        
        filtered_files = []
        for file_path in all_files:
            relative_path = file_path.relative_to(self.vault_root)
            relative_str = str(relative_path)
            
            exclude = False
            
            # Check for any dot directory at any level
            path_parts = relative_path.parts
            for part in path_parts:
                if part.startswith('.') and part != '..':
                    exclude = True
                    break
            
            # Check for Utilities directory
            if not exclude and 'Utilities' in path_parts:
                exclude = True
            
            # Check for other exclusions if not already excluded
            if not exclude:
                for exclude_pattern in exclude_patterns:
                    if '/.venv/' in relative_str or relative_str.startswith('.venv/'):
                        exclude = True
                        break
                    elif '/node_modules/' in relative_str or relative_str.startswith('node_modules/'):
                        exclude = True
                        break
                    elif relative_path.match(exclude_pattern):
                        exclude = True
                        break
            
            if not exclude:
                filtered_files.append(file_path)
        
        logger.info(f"Discovered {len(filtered_files)} markdown files")
        return sorted(filtered_files)
    
    def parse_frontmatter(self, content: str, file_path: Optional[Path] = None) -> Tuple[Optional[Dict], str]:
        """Parse YAML frontmatter from markdown content.

        Now delegates to nahuatl-frontmatter shared library.

        Args:
            content: Markdown content with potential frontmatter
            file_path: Optional file path for better error reporting

        Returns:
            Tuple of (frontmatter_dict, content_without_frontmatter)
        """
        metadata, body = parse_content(content)

        if metadata is None and file_path:
            logger.debug(f"No frontmatter or parse error in {file_path}")

        return metadata, body
    
    def extract_inline_tags(self, content: str) -> List[str]:
        """Extract inline #tags from markdown content."""
        tag_pattern = r'#([a-zA-Z0-9_-]+)'
        matches = re.findall(tag_pattern, content)
        return list(set(matches))
    
    def clean_content(self, content: str) -> str:
        """Clean markdown content for embedding.

        Removes wiki links, cleans formatting, preserves readable text.
        """
        content = re.sub(r'\[\[([^\]]+)\]\]', r'\1', content)
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
        content = re.sub(r'#+\s*', '', content)
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
        content = re.sub(r'\*([^*]+)\*', r'\1', content)
        content = re.sub(r'`([^`]+)`', r'\1', content)
        content = re.sub(r'\n+', ' ', content)
        content = content.strip()
        return content

    def read_file(self, file_path: Path) -> Optional[VaultContent]:
        """Read a single vault file and extract content.
        
        Returns:
            VaultContent object or None if file cannot be read
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            frontmatter, content = self.parse_frontmatter(raw_content, file_path)
            
            title = file_path.stem
            if frontmatter and 'title' in frontmatter:
                title = frontmatter['title']
            
            tags = []
            if frontmatter and 'tags' in frontmatter:
                if isinstance(frontmatter['tags'], list):
                    tags.extend(frontmatter['tags'])
                elif isinstance(frontmatter['tags'], str):
                    tags.append(frontmatter['tags'])
            
            # Only use frontmatter tags, skip inline tags
            tags = list(set(tags))

            cleaned_content = self.clean_content(content)

            # Prepend description if present in frontmatter
            # Description is a curated summary and should influence semantic search
            description = frontmatter.get('description') if frontmatter else None
            if description:
                # Put description first, then content
                # This gives description natural positional weight in embeddings
                embedding_content = f"{description}. {cleaned_content}"
            else:
                embedding_content = cleaned_content

            return VaultContent(
                file_path=file_path,
                title=title,
                content=embedding_content,
                vault_root=self.vault_root,
                frontmatter=frontmatter,
                tags=tags
            )
            
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None
    
    def read_vault(self, limit: Optional[int] = None) -> List[VaultContent]:
        """Read all vault content.
        
        Args:
            limit: Optional limit on number of files to process (for testing)
            
        Returns:
            List of VaultContent objects
        """
        files = self.discover_files()
        
        if limit:
            files = files[:limit]
        
        content_objects = []
        for file_path in tqdm(files, desc="Reading vault files"):
            content = self.read_file(file_path)
            if content and content.content.strip():
                content_objects.append(content)
        
        logger.info(f"Successfully read {len(content_objects)} files")
        return content_objects
    
    def get_strategic_subset(self, target_count: int = 200) -> List[Path]:
        """Get a strategic subset of files for embeddings.
        
        Selects files across key domains for semantic diversity:
        - Daily notes (recent entries for temporal patterns)
        - Reference/Tech (technical interests)
        - Reference/Culture (films, books, creative content) 
        - L/ directory (personal reflections)
        - Other reference materials
        
        Args:
            target_count: Target number of files to select
            
        Returns:
            List of strategically selected file paths
        """
        all_files = self.discover_files()
        
        daily_files = [f for f in all_files if "/Daily/" in str(f)]
        reference_tech = [f for f in all_files if "/Reference/Tech/" in str(f)]
        reference_culture = [f for f in all_files if "/Reference/Culture/" in str(f)]
        l_files = [f for f in all_files if "/L/" in str(f) and "/Daily/" not in str(f)]
        other_reference = [f for f in all_files if "/Reference/" in str(f) 
                          and "/Tech/" not in str(f) and "/Culture/" not in str(f)]
        
        breakdown = {
            "daily": min(50, len(daily_files)),
            "reference_tech": min(40, len(reference_tech)), 
            "reference_culture": min(30, len(reference_culture)),
            "l_directory": min(50, len(l_files)),
            "other_reference": min(30, len(other_reference))
        }
        
        selected_files = []
        
        if daily_files:
            daily_sample = daily_files[-breakdown["daily"]:]
            selected_files.extend(daily_sample)
        
        if reference_tech:
            tech_sample = reference_tech[:breakdown["reference_tech"]]
            selected_files.extend(tech_sample)
        
        if reference_culture:
            culture_sample = reference_culture[:breakdown["reference_culture"]]
            selected_files.extend(culture_sample)
        
        if l_files:
            l_sample = l_files[:breakdown["l_directory"]]
            selected_files.extend(l_sample)
        
        if other_reference:
            other_sample = other_reference[:breakdown["other_reference"]]
            selected_files.extend(other_sample)
        
        logger.info(f"Strategic subset: {len(selected_files)} files selected")
        logger.info(f"  Daily: {len([f for f in selected_files if '/Daily/' in str(f)])}")
        logger.info(f"  Reference/Tech: {len([f for f in selected_files if '/Reference/Tech/' in str(f)])}")
        logger.info(f"  Reference/Culture: {len([f for f in selected_files if '/Reference/Culture/' in str(f)])}")
        logger.info(f"  L/ directory: {len([f for f in selected_files if '/L/' in str(f)])}")
        logger.info(f"  Other Reference: {len([f for f in selected_files if '/Reference/' in str(f) and '/Tech/' not in str(f) and '/Culture/' not in str(f)])}")
        
        return selected_files