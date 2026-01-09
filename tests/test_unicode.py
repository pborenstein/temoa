"""
Comprehensive tests for Unicode sanitization.

Tests the sanitize_unicode() function which prevents UnicodeEncodeError
when serializing search results to JSON. Focus on surrogate pairs, emoji,
nested structures, and performance.
"""

import pytest
import time
from temoa.server import sanitize_unicode


class TestBasicStringSanitization:
    """Test basic string sanitization."""

    def test_valid_unicode_unchanged(self):
        """Valid Unicode strings should pass through unchanged."""
        text = "Hello, world! 你好世界 مرحبا"
        result = sanitize_unicode(text)
        assert result == text

    def test_ascii_text_unchanged(self):
        """ASCII text should pass through unchanged."""
        text = "Simple ASCII text 123"
        result = sanitize_unicode(text)
        assert result == text

    def test_empty_string(self):
        """Empty string should remain empty."""
        result = sanitize_unicode("")
        assert result == ""

    def test_none_value(self):
        """None values should pass through."""
        result = sanitize_unicode(None)
        assert result is None


class TestSurrogatePairs:
    """Test handling of invalid surrogate pairs."""

    def test_high_surrogate_alone(self):
        """High surrogate without low surrogate should be replaced."""
        # \uD800 is a high surrogate that's invalid on its own
        text = "Test \uD800 content"
        result = sanitize_unicode(text)

        # Should not contain the invalid surrogate
        assert "\uD800" not in result
        # Should contain replacement character or be sanitized
        assert isinstance(result, str)
        assert len(result) > 0

    def test_low_surrogate_alone(self):
        """Low surrogate without high surrogate should be replaced."""
        # \uDFFF is a low surrogate that's invalid on its own
        text = "Test \uDFFF content"
        result = sanitize_unicode(text)

        # Should not contain the invalid surrogate
        assert "\uDFFF" not in result
        assert isinstance(result, str)

    def test_reversed_surrogate_pair(self):
        """Reversed surrogate pair should be replaced."""
        # Low then high is invalid
        text = "Test \uDC00\uD800 content"
        result = sanitize_unicode(text)

        assert isinstance(result, str)
        # Should be sanitized (exact output depends on implementation)

    def test_multiple_surrogates(self):
        """Multiple invalid surrogates should all be replaced."""
        text = "Test \uD800 middle \uDFFF end"
        result = sanitize_unicode(text)

        assert "\uD800" not in result
        assert "\uDFFF" not in result
        assert isinstance(result, str)

    def test_surrogate_at_start(self):
        """Surrogate at start of string should be handled."""
        text = "\uD800 content"
        result = sanitize_unicode(text)
        assert isinstance(result, str)

    def test_surrogate_at_end(self):
        """Surrogate at end of string should be handled."""
        text = "content \uD800"
        result = sanitize_unicode(text)
        assert isinstance(result, str)


class TestEmojiSequences:
    """Test handling of emoji and multi-codepoint sequences."""

    def test_simple_emoji(self):
        """Simple emoji should pass through unchanged."""
        text = "Test 😀 🔥 💯"
        result = sanitize_unicode(text)
        assert result == text

    def test_emoji_sequences(self):
        """Multi-codepoint emoji sequences should work."""
        # Family emoji (multiple codepoints)
        text = "Family 👨‍👩‍👧‍👦 emoji"
        result = sanitize_unicode(text)
        # Should preserve the emoji (may have some variation)
        assert isinstance(result, str)
        assert "Family" in result
        assert "emoji" in result

    def test_skin_tone_modifiers(self):
        """Emoji with skin tone modifiers should work."""
        text = "Wave 👋🏽 hand"
        result = sanitize_unicode(text)
        assert isinstance(result, str)
        assert "Wave" in result
        assert "hand" in result

    def test_flag_emoji(self):
        """Regional indicator sequences (flags) should work."""
        text = "Flag 🇺🇸 🇯🇵 🇬🇧"
        result = sanitize_unicode(text)
        assert isinstance(result, str)
        assert "Flag" in result

    def test_emoji_zwj_sequences(self):
        """Zero-width joiner sequences should work."""
        # Health worker emoji with skin tone and gender
        text = "Health 🧑‍⚕️ worker"
        result = sanitize_unicode(text)
        assert isinstance(result, str)
        assert "Health" in result
        assert "worker" in result


class TestNestedStructures:
    """Test sanitization of nested data structures."""

    def test_flat_dict(self):
        """Flat dictionary should be sanitized."""
        data = {
            "valid": "Good text",
            "invalid": "Bad \uD800 text"
        }
        result = sanitize_unicode(data)

        assert isinstance(result, dict)
        assert result["valid"] == "Good text"
        assert "\uD800" not in result["invalid"]

    def test_nested_dict(self):
        """Nested dictionaries should be recursively sanitized."""
        data = {
            "level1": {
                "level2": {
                    "level3": "Deep \uD800 text"
                }
            }
        }
        result = sanitize_unicode(data)

        assert isinstance(result, dict)
        assert "\uD800" not in result["level1"]["level2"]["level3"]

    def test_list_of_strings(self):
        """List of strings should be sanitized."""
        data = [
            "Valid text",
            "Invalid \uD800 text",
            "More \uDFFF text"
        ]
        result = sanitize_unicode(data)

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == "Valid text"
        assert "\uD800" not in result[1]
        assert "\uDFFF" not in result[2]

    def test_list_of_dicts(self):
        """List of dictionaries should be sanitized."""
        data = [
            {"key": "Valid"},
            {"key": "Invalid \uD800"},
            {"nested": {"key": "Deep \uDFFF"}}
        ]
        result = sanitize_unicode(data)

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]["key"] == "Valid"
        assert "\uD800" not in result[1]["key"]
        assert "\uDFFF" not in result[2]["nested"]["key"]

    def test_tuple_sanitization(self):
        """Tuples should be sanitized and remain tuples."""
        data = ("Valid", "Invalid \uD800", "Text")
        result = sanitize_unicode(data)

        assert isinstance(result, tuple)
        assert len(result) == 3
        assert result[0] == "Valid"
        assert "\uD800" not in result[1]

    def test_mixed_nested_structure(self):
        """Complex mixed structures should be fully sanitized."""
        data = {
            "results": [
                {
                    "title": "Valid title",
                    "content": "Invalid \uD800 content",
                    "metadata": {
                        "tags": ["tag1", "tag\uDFFF2"],
                        "info": ("tuple", "with\uD800invalid")
                    }
                }
            ]
        }
        result = sanitize_unicode(data)

        assert isinstance(result, dict)
        assert "\uD800" not in result["results"][0]["content"]
        assert "\uDFFF" not in result["results"][0]["metadata"]["tags"][1]
        assert "\uD800" not in result["results"][0]["metadata"]["info"][1]


class TestNoneAndMissingValues:
    """Test handling of None values and missing data."""

    def test_dict_with_none_values(self):
        """Dictionary with None values should preserve them."""
        data = {
            "key1": "value",
            "key2": None,
            "key3": "text \uD800"
        }
        result = sanitize_unicode(data)

        assert result["key1"] == "value"
        assert result["key2"] is None
        assert "\uD800" not in result["key3"]

    def test_list_with_none_values(self):
        """List with None values should preserve them."""
        data = ["text", None, "more \uD800 text", None]
        result = sanitize_unicode(data)

        assert result[0] == "text"
        assert result[1] is None
        assert "\uD800" not in result[2]
        assert result[3] is None

    def test_nested_none_values(self):
        """Nested structures with None should work."""
        data = {
            "level1": {
                "value": None,
                "nested": {
                    "value": "text \uD800",
                    "another": None
                }
            }
        }
        result = sanitize_unicode(data)

        assert result["level1"]["value"] is None
        assert "\uD800" not in result["level1"]["nested"]["value"]
        assert result["level1"]["nested"]["another"] is None


class TestMixedValidInvalid:
    """Test partial corruption scenarios."""

    def test_mostly_valid_with_one_invalid(self):
        """Mostly valid content with single invalid character."""
        text = "This is a long valid sentence with one invalid \uD800 character in the middle and more valid text after."
        result = sanitize_unicode(text)

        # Should preserve all the valid parts
        assert "This is a long valid sentence" in result
        assert "character in the middle" in result
        assert "more valid text after" in result
        # Should remove the invalid part
        assert "\uD800" not in result

    def test_alternating_valid_invalid(self):
        """Alternating valid and invalid characters."""
        text = "a\uD800b\uDFFFc\uD800d"
        result = sanitize_unicode(text)

        # Should preserve valid chars
        assert "a" in result
        assert "b" in result
        assert "c" in result
        assert "d" in result
        # Should remove invalid
        assert "\uD800" not in result
        assert "\uDFFF" not in result


class TestLargeResponses:
    """Test performance with large result sets."""

    def test_100_small_results(self):
        """Should handle 100 small results efficiently."""
        # Simulate search results
        results = [
            {
                "title": f"Result {i}",
                "content": f"Content for result {i} with some \uD800 invalid chars",
                "score": 0.9 - (i * 0.001)
            }
            for i in range(100)
        ]

        start = time.time()
        sanitized = sanitize_unicode(results)
        duration = time.time() - start

        # Should complete in < 10ms
        assert duration < 0.01, f"Took {duration * 1000:.2f}ms, expected < 10ms"

        # Verify results
        assert len(sanitized) == 100
        for result in sanitized:
            assert "\uD800" not in result["content"]

    def test_10_large_results(self):
        """Should handle 10 large results efficiently."""
        # Simulate large document results
        large_content = ("Lorem ipsum " * 100) + "\uD800" + ("dolor sit amet " * 100)
        results = [
            {
                "title": f"Large Result {i}",
                "content": large_content,
                "score": 0.9
            }
            for i in range(10)
        ]

        start = time.time()
        sanitized = sanitize_unicode(results)
        duration = time.time() - start

        # Should complete in < 50ms
        assert duration < 0.05, f"Took {duration * 1000:.2f}ms, expected < 50ms"

        # Verify results
        assert len(sanitized) == 10
        for result in sanitized:
            assert "\uD800" not in result["content"]

    def test_deeply_nested_structure(self):
        """Should handle deeply nested structures efficiently."""
        # Create nested structure 20 levels deep
        data = {"value": "text \uD800"}
        for _ in range(20):
            data = {"nested": data}

        start = time.time()
        sanitized = sanitize_unicode(data)
        duration = time.time() - start

        # Should complete in < 5ms
        assert duration < 0.005, f"Took {duration * 1000:.2f}ms, expected < 5ms"

        # Navigate to deepest level
        current = sanitized
        for _ in range(20):
            current = current["nested"]

        assert "\uD800" not in current["value"]


class TestNonStringTypes:
    """Test handling of non-string types."""

    def test_integer_values(self):
        """Integer values should pass through unchanged."""
        assert sanitize_unicode(42) == 42
        assert sanitize_unicode(0) == 0
        assert sanitize_unicode(-100) == -100

    def test_float_values(self):
        """Float values should pass through unchanged."""
        assert sanitize_unicode(3.14) == 3.14
        assert sanitize_unicode(0.0) == 0.0
        assert sanitize_unicode(-1.5) == -1.5

    def test_boolean_values(self):
        """Boolean values should pass through unchanged."""
        assert sanitize_unicode(True) is True
        assert sanitize_unicode(False) is False

    def test_mixed_types_in_dict(self):
        """Dictionary with mixed types should preserve types."""
        data = {
            "string": "text \uD800",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "none": None,
            "list": [1, 2, "text\uDFFF"]
        }
        result = sanitize_unicode(data)

        assert "\uD800" not in result["string"]
        assert result["int"] == 42
        assert result["float"] == 3.14
        assert result["bool"] is True
        assert result["none"] is None
        assert result["list"][0] == 1
        assert "\uDFFF" not in result["list"][2]


class TestEdgeCases:
    """Test unusual edge cases."""

    def test_very_long_string(self):
        """Should handle very long strings efficiently."""
        long_text = "x" * 10000 + "\uD800" + "y" * 10000
        result = sanitize_unicode(long_text)

        assert len(result) >= 20000
        assert "\uD800" not in result

    def test_string_with_only_surrogates(self):
        """String containing only surrogates should be sanitized."""
        text = "\uD800\uDFFF\uD800\uDFFF"
        result = sanitize_unicode(text)

        assert "\uD800" not in result
        assert "\uDFFF" not in result
        assert isinstance(result, str)

    def test_empty_dict(self):
        """Empty dictionary should remain empty."""
        result = sanitize_unicode({})
        assert result == {}

    def test_empty_list(self):
        """Empty list should remain empty."""
        result = sanitize_unicode([])
        assert result == []

    def test_empty_tuple(self):
        """Empty tuple should remain empty."""
        result = sanitize_unicode(())
        assert result == ()

    def test_single_replacement_character(self):
        """Replacement character itself should be preserved."""
        text = "Test \ufffd content"  # U+FFFD is the replacement character
        result = sanitize_unicode(text)
        assert result == text


class TestRealWorldScenarios:
    """Test scenarios based on actual search results."""

    def test_search_result_structure(self):
        """Test sanitization of typical search result."""
        result = {
            "file_path": "/vault/file.md",
            "relative_path": "file.md",
            "content": "Some content with \uD800 invalid char",
            "title": "Document Title",
            "score": 0.85,
            "frontmatter": {
                "tags": ["tag1", "tag\uDFFF2"],
                "description": "Description with \uD800 issue"
            },
            "metadata": {
                "created": "2025-01-01",
                "modified": "2025-01-05"
            }
        }

        sanitized = sanitize_unicode(result)

        assert sanitized["file_path"] == "/vault/file.md"
        assert "\uD800" not in sanitized["content"]
        assert sanitized["title"] == "Document Title"
        assert sanitized["score"] == 0.85
        assert "\uDFFF" not in sanitized["frontmatter"]["tags"][1]
        assert "\uD800" not in sanitized["frontmatter"]["description"]

    def test_archaeology_result_structure(self):
        """Test sanitization of archaeology endpoint results."""
        result = {
            "period": "2024-Q4",
            "activity_score": 0.75,
            "files": [
                {
                    "path": "note1.md",
                    "content": "Content \uD800 here"
                },
                {
                    "path": "note2.md",
                    "content": "More \uDFFF content"
                }
            ]
        }

        sanitized = sanitize_unicode(result)

        assert sanitized["period"] == "2024-Q4"
        assert sanitized["activity_score"] == 0.75
        assert "\uD800" not in sanitized["files"][0]["content"]
        assert "\uDFFF" not in sanitized["files"][1]["content"]
