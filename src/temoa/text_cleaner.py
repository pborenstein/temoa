"""
Text cleaning utilities for gleanings.

Removes problematic unicode characters that break indexing or YAML parsing:
- Emojis
- Zero-width characters
- RTL/LTR marks
- Smart quotes (normalize to ASCII)
- En/em dashes (normalize to hyphens)
- Non-breaking spaces
"""

import re


def remove_emojis(text: str) -> str:
    """
    Remove emoji characters from text.

    Covers most common emoji unicode ranges.

    Args:
        text: Input text

    Returns:
        Text with emojis removed
    """
    if not text:
        return text

    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002500-\U00002BEF"  # chinese char
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"  # zero-width joiner (part of emoji sequences)
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"  # variation selector (part of emoji sequences)
        "\u3030"
        "]+",
        flags=re.UNICODE
    )

    return emoji_pattern.sub("", text)


def remove_zero_width(text: str) -> str:
    """
    Remove zero-width characters.

    These are invisible characters that break searching and indexing.

    Args:
        text: Input text

    Returns:
        Text with zero-width characters removed
    """
    if not text:
        return text

    # Zero-width space, non-joiner, joiner, no-break space marker
    zero_width_pattern = re.compile(r'[\u200B-\u200D\uFEFF]')
    return zero_width_pattern.sub("", text)


def remove_rtl_marks(text: str) -> str:
    """
    Remove RTL (right-to-left) and LTR (left-to-right) marks.

    These formatting marks can break searching.

    Args:
        text: Input text

    Returns:
        Text with RTL/LTR marks removed
    """
    if not text:
        return text

    # Left-to-right mark, right-to-left mark, and embedding marks
    rtl_pattern = re.compile(r'[\u200E-\u200F\u202A-\u202E]')
    return rtl_pattern.sub("", text)


def normalize_quotes(text: str) -> str:
    """
    Normalize smart quotes to ASCII quotes.

    Converts:
    - Single smart quotes (' ') to apostrophe (')
    - Double smart quotes (" ") to straight quotes (")

    Args:
        text: Input text

    Returns:
        Text with normalized quotes
    """
    if not text:
        return text

    # Single quotes: ' ' → '
    text = re.sub(r'[\u2018\u2019]', "'", text)

    # Double quotes: " " → "
    text = re.sub(r'[\u201C\u201D]', '"', text)

    return text


def normalize_dashes(text: str) -> str:
    """
    Normalize en-dashes and em-dashes to hyphens.

    Converts:
    - En dash (–) to hyphen (-)
    - Em dash (—) to hyphen (-)
    - Other dash variants to hyphen (-)

    Args:
        text: Input text

    Returns:
        Text with normalized dashes
    """
    if not text:
        return text

    # En dash, em dash, and other dash variants → -
    text = re.sub(r'[\u2010-\u2015]', '-', text)

    return text


def normalize_spaces(text: str) -> str:
    """
    Normalize non-breaking spaces and clean up extra whitespace.

    Converts:
    - Non-breaking space to regular space
    - Multiple spaces to single space
    - Strips leading/trailing whitespace

    Args:
        text: Input text

    Returns:
        Text with normalized spaces
    """
    if not text:
        return text

    # Non-breaking space → regular space
    text = text.replace('\u00A0', ' ')

    # Multiple spaces → single space
    text = re.sub(r'\s+', ' ', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def clean_text(text: str) -> str:
    """
    Apply all text cleaning operations.

    Removes:
    - Emojis
    - Zero-width characters
    - RTL/LTR marks
    - Normalizes smart quotes to ASCII
    - Normalizes en/em dashes to hyphens
    - Normalizes spaces

    Args:
        text: Input text

    Returns:
        Cleaned text safe for YAML frontmatter and indexing

    Example:
        >>> clean_text("Hello 🚀 World")
        'Hello World'
        >>> clean_text("It's "quoted" text—with dashes")
        "It's \"quoted\" text-with dashes"
    """
    if not text:
        return text

    # Apply all cleaning operations in order
    text = remove_emojis(text)
    text = remove_zero_width(text)
    text = remove_rtl_marks(text)
    text = normalize_quotes(text)
    text = normalize_dashes(text)
    text = normalize_spaces(text)

    return text
