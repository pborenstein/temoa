"""
Tests for URL normalizers.
"""

import pytest
from temoa.normalizers import (
    GitHubNormalizer,
    DefaultNormalizer,
    NormalizerRegistry,
)


class TestGitHubNormalizer:
    """Tests for GitHubNormalizer."""

    def setup_method(self):
        self.normalizer = GitHubNormalizer()

    def test_matches_github_urls(self):
        """Should match github.com URLs."""
        assert self.normalizer.matches("https://github.com/user/repo")
        assert self.normalizer.matches("http://github.com/user/repo")
        assert not self.normalizer.matches("https://example.com")

    def test_normalize_title_with_colon_separator(self):
        """Should preserve 'user/repo: Description' format (deliberate design)."""
        url = "https://github.com/user/repo"
        title = "user/repo: Turn any Git repository into a documentation link."
        result = self.normalizer.normalize_title(url, title)
        assert result == "user/repo: Turn any Git repository into a documentation link."

    def test_normalize_title_with_dash_separator(self):
        """Should preserve title when dash part doesn't look like user/repo."""
        url = "https://github.com/user/repo"
        title = "user/repo - Turn any Git repository into a documentation link."
        result = self.normalizer.normalize_title(url, title)
        assert result == "user/repo - Turn any Git repository into a documentation link."

    def test_normalize_title_no_separator(self):
        """Should return title as-is if no separator found."""
        url = "https://github.com/user/repo"
        title = "user/repo"
        result = self.normalizer.normalize_title(url, title)
        assert result == "user/repo"

    def test_normalize_title_none_extracts_from_url(self):
        """Should extract user/repo from URL if title is None."""
        url = "https://github.com/user/repo"
        result = self.normalizer.normalize_title(url, None)
        assert result == "user/repo"

    def test_normalize_title_complex_url_path(self):
        """Should extract user/repo from URL with extra path components."""
        url = "https://github.com/user/repo/issues/123"
        result = self.normalizer.normalize_title(url, None)
        assert result == "user/repo"

    def test_normalize_description_removes_repo_suffix(self):
        """Should remove ' - user/repo' suffix from description."""
        url = "https://github.com/user/repo"
        desc = "Turn any Git repository into a documentation link. - user/repo"
        result = self.normalizer.normalize_description(url, desc)
        assert result == "Turn any Git repository into a documentation link."

    def test_normalize_description_removes_contribute_suffix(self):
        """Should remove 'Contribute to user/repo...' suffix."""
        url = "https://github.com/user/repo"
        desc = "Open Source LLMOps tool. Contribute to user/repo development."
        result = self.normalizer.normalize_description(url, desc)
        assert result == "Open Source LLMOps tool."

    def test_normalize_description_none(self):
        """Should return empty string if description is None."""
        url = "https://github.com/user/repo"
        result = self.normalizer.normalize_description(url, None)
        assert result == ""

    def test_normalize_description_removes_emojis(self):
        """Should remove emoji characters from description."""
        url = "https://github.com/user/repo"
        desc = "🚀 A fast tool for 📊 data analysis ✨"
        result = self.normalizer.normalize_description(url, desc)
        assert result == "A fast tool for data analysis"
        assert "🚀" not in result
        assert "📊" not in result
        assert "✨" not in result

    def test_normalize_description_complex_emojis(self):
        """Should remove various emoji types."""
        url = "https://github.com/user/repo"
        desc = "Tool 🔥 with 💯 support ⚡ and 🎉 features"
        result = self.normalizer.normalize_description(url, desc)
        assert result == "Tool with support and features"


class TestDefaultNormalizer:
    """Tests for DefaultNormalizer."""

    def setup_method(self):
        self.normalizer = DefaultNormalizer()

    def test_matches_all_urls(self):
        """Should match any URL."""
        assert self.normalizer.matches("https://example.com")
        assert self.normalizer.matches("https://github.com/user/repo")
        assert self.normalizer.matches("http://any-domain.org")

    def test_normalize_title_returns_as_is(self):
        """Should return title unchanged."""
        url = "https://example.com"
        title = "Example Site: Great Content"
        result = self.normalizer.normalize_title(url, title)
        assert result == title

    def test_normalize_title_none_returns_url(self):
        """Should return URL if title is None."""
        url = "https://example.com"
        result = self.normalizer.normalize_title(url, None)
        assert result == url

    def test_normalize_description_returns_as_is(self):
        """Should return description unchanged."""
        url = "https://example.com"
        desc = "Some description with - separators"
        result = self.normalizer.normalize_description(url, desc)
        assert result == desc

    def test_normalize_description_none_returns_empty(self):
        """Should return empty string if description is None."""
        url = "https://example.com"
        result = self.normalizer.normalize_description(url, None)
        assert result == ""


class TestNormalizerRegistry:
    """Tests for NormalizerRegistry."""

    def setup_method(self):
        self.registry = NormalizerRegistry()

    def test_selects_github_normalizer(self):
        """Should select GitHubNormalizer for GitHub URLs."""
        normalizer = self.registry.get_normalizer("https://github.com/user/repo")
        assert isinstance(normalizer, GitHubNormalizer)

    def test_selects_default_normalizer(self):
        """Should select DefaultNormalizer for unknown domains."""
        normalizer = self.registry.get_normalizer("https://example.com")
        assert isinstance(normalizer, DefaultNormalizer)

    def test_normalize_github_url(self):
        """Should normalize GitHub URL with appropriate normalizer."""
        url = "https://github.com/user/repo"
        title = "user/repo: A great tool"
        desc = "A great tool for developers. - user/repo"

        norm_title, norm_desc = self.registry.normalize(url, title, desc)

        assert norm_title == "user/repo: A great tool"
        assert norm_desc == "A great tool for developers."

    def test_normalize_non_github_url(self):
        """Should pass through non-GitHub URLs unchanged."""
        url = "https://example.com"
        title = "Example: Great Site"
        desc = "Great site - with separators"

        norm_title, norm_desc = self.registry.normalize(url, title, desc)

        assert norm_title == title
        assert norm_desc == desc

    def test_normalize_with_none_values(self):
        """Should handle None title and description."""
        url = "https://github.com/user/repo"

        norm_title, norm_desc = self.registry.normalize(url, None, None)

        assert norm_title == "user/repo"  # Extracted from URL
        assert norm_desc == ""


class TestEdgeCaseURLs:
    """Test unusual URL formats and edge cases."""

    def setup_method(self):
        self.registry = NormalizerRegistry()

    def test_url_with_query_parameters(self):
        """Should handle URLs with query parameters."""
        url = "https://github.com/user/repo?tab=readme"
        title = "user/repo: Description"

        norm_title, norm_desc = self.registry.normalize(url, title, None)
        assert norm_title == "user/repo: Description"

    def test_url_with_fragment(self):
        """Should handle URLs with fragments."""
        url = "https://github.com/user/repo#installation"
        title = "user/repo: Description"

        norm_title, norm_desc = self.registry.normalize(url, title, None)
        assert norm_title == "user/repo: Description"

    def test_url_with_port(self):
        """Should handle URLs with explicit ports."""
        url = "https://github.com:443/user/repo"
        normalizer = GitHubNormalizer()

        assert normalizer.matches(url)
        result = normalizer.normalize_title(url, None)
        assert result == "user/repo"

    def test_url_with_auth(self):
        """Should handle URLs with authentication info."""
        url = "https://user:pass@github.com/user/repo"
        normalizer = GitHubNormalizer()

        # Should still match
        assert normalizer.matches(url)

    def test_url_with_subdomain(self):
        """Should handle GitHub URLs with subdomains."""
        url = "https://gist.github.com/user/1234567"
        normalizer = GitHubNormalizer()

        # Should match github.com domain
        result = normalizer.matches(url)
        assert result

    def test_url_with_trailing_slash(self):
        """Should handle URLs with trailing slashes."""
        url = "https://github.com/user/repo/"
        normalizer = GitHubNormalizer()

        result = normalizer.normalize_title(url, None)
        assert result == "user/repo"

    def test_url_with_multiple_slashes(self):
        """Should handle URLs with extra slashes."""
        url = "https://github.com//user//repo"
        normalizer = GitHubNormalizer()

        # Should extract user/repo after normalizing double slashes
        result = normalizer.normalize_title(url, None)
        assert result == "user/repo"

    def test_international_domain(self):
        """Should handle international domain names."""
        url = "https://例え.jp/path"
        normalizer = DefaultNormalizer()

        result = normalizer.normalize_title(url, "Title")
        assert result == "Title"

    def test_very_long_url(self):
        """Should handle very long URLs."""
        long_path = "/".join([f"segment{i}" for i in range(100)])
        url = f"https://github.com/user/repo/{long_path}"
        normalizer = GitHubNormalizer()

        # Should still extract user/repo
        result = normalizer.normalize_title(url, None)
        assert result == "user/repo"

    def test_url_with_uppercase(self):
        """Should handle URLs with uppercase characters."""
        url = "https://GitHub.COM/User/Repo"
        normalizer = GitHubNormalizer()

        # Should match (case-insensitive domain matching)
        assert normalizer.matches(url)


class TestMultipleNormalizers:
    """Test chaining normalizers and complex scenarios."""

    def test_github_url_through_registry(self):
        """Should route GitHub URL to correct normalizer."""
        registry = NormalizerRegistry()

        url = "https://github.com/anthropics/claude-code"
        title = "anthropics/claude-code: CLI tool for development"
        desc = "A CLI tool for development - anthropics/claude-code"

        norm_title, norm_desc = registry.normalize(url, title, desc)

        assert norm_title == "anthropics/claude-code: CLI tool for development"
        assert " - anthropics/claude-code" not in norm_desc

    def test_fallback_to_default_normalizer(self):
        """Should fall back to default for unknown domains."""
        registry = NormalizerRegistry()

        url = "https://example.org/article"
        title = "Example: Article Title"
        desc = "Article description - Example"

        norm_title, norm_desc = registry.normalize(url, title, desc)

        # DefaultNormalizer doesn't modify
        assert norm_title == title
        assert norm_desc == desc

    def test_multiple_urls_batch_normalization(self):
        """Should handle batch normalization efficiently."""
        registry = NormalizerRegistry()

        urls = [
            ("https://github.com/user1/repo1", "user1/repo1: Desc", "Desc - user1/repo1"),
            ("https://github.com/user2/repo2", "user2/repo2: Tool", "Tool - user2/repo2"),
            ("https://example.com", "Example", "Example site"),
        ]

        results = [registry.normalize(url, title, desc) for url, title, desc in urls]

        assert results[0][0] == "user1/repo1: Desc"
        assert results[1][0] == "user2/repo2: Tool"
        assert results[2][0] == "Example"


class TestPerformanceBenchmarks:
    """Test normalization performance."""

    def test_single_normalization_performance(self):
        """Should normalize single URL in < 5ms."""
        import time

        registry = NormalizerRegistry()
        url = "https://github.com/user/repo"
        title = "user/repo: A great tool for developers"
        desc = "A great tool for developers - user/repo"

        start = time.time()
        for _ in range(100):
            registry.normalize(url, title, desc)
        duration = time.time() - start

        # 100 normalizations in < 500ms = < 5ms each
        assert duration < 0.5, f"100 normalizations took {duration * 1000:.2f}ms"

    def test_batch_normalization_performance(self):
        """Should normalize 100 URLs efficiently."""
        import time

        registry = NormalizerRegistry()

        # Create 100 test URLs
        urls = [
            (
                f"https://github.com/user{i}/repo{i}",
                f"user{i}/repo{i}: Tool {i}",
                f"Tool {i} - user{i}/repo{i}"
            )
            for i in range(100)
        ]

        start = time.time()
        results = [registry.normalize(url, title, desc) for url, title, desc in urls]
        duration = time.time() - start

        # Should complete in < 100ms
        assert duration < 0.1, f"100 normalizations took {duration * 1000:.2f}ms"
        assert len(results) == 100

    def test_regex_performance(self):
        """Should handle regex operations efficiently."""
        import time

        normalizer = GitHubNormalizer()
        desc = "🚀 " * 100 + "Great tool " * 50 + "🎉 " * 100

        start = time.time()
        for _ in range(100):
            normalizer.normalize_description("https://github.com/user/repo", desc)
        duration = time.time() - start

        # 100 emoji removals in < 100ms
        assert duration < 0.1, f"Emoji removal took {duration * 1000:.2f}ms"


class TestEmojiEdgeCases:
    """Test advanced emoji handling."""

    def test_multi_byte_emoji(self):
        """Should remove multi-byte emoji correctly."""
        normalizer = GitHubNormalizer()
        url = "https://github.com/user/repo"

        # Multi-byte emoji
        desc = "Tool 👨‍💻 for 👩‍🔬 developers"
        result = normalizer.normalize_description(url, desc)

        # Should remove emoji
        assert "👨‍💻" not in result
        assert "👩‍🔬" not in result
        assert "Tool" in result
        assert "developers" in result

    def test_emoji_sequences(self):
        """Should remove complex emoji sequences."""
        normalizer = GitHubNormalizer()
        url = "https://github.com/user/repo"

        # Family emoji (multiple codepoints)
        desc = "Family 👨‍👩‍👧‍👦 friendly tool"
        result = normalizer.normalize_description(url, desc)

        assert "Family" in result
        assert "friendly" in result
        assert "tool" in result

    def test_flag_emoji(self):
        """Should remove flag emoji."""
        normalizer = GitHubNormalizer()
        url = "https://github.com/user/repo"

        desc = "Global 🇺🇸 🇯🇵 🇬🇧 support"
        result = normalizer.normalize_description(url, desc)

        assert "Global" in result
        assert "support" in result
        assert "🇺🇸" not in result

    def test_emoji_with_skin_tone(self):
        """Should remove emoji with skin tone modifiers."""
        normalizer = GitHubNormalizer()
        url = "https://github.com/user/repo"

        desc = "Wave 👋🏽 hello 👍🏻"
        result = normalizer.normalize_description(url, desc)

        assert "Wave" in result
        assert "hello" in result
        # Emoji should be removed
        assert "👋" not in result
        assert "👍" not in result

    def test_mixed_emoji_and_text(self):
        """Should preserve text while removing emoji."""
        normalizer = GitHubNormalizer()
        url = "https://github.com/user/repo"

        desc = "⚡Fast⚡ 🔥blazing🔥 ✨clean✨ code"
        result = normalizer.normalize_description(url, desc)

        # Should preserve text
        assert "Fast" in result
        assert "blazing" in result
        assert "clean" in result
        assert "code" in result

        # Should remove emoji
        assert "⚡" not in result
        assert "🔥" not in result
        assert "✨" not in result

    def test_emoji_at_boundaries(self):
        """Should handle emoji at string boundaries."""
        normalizer = GitHubNormalizer()
        url = "https://github.com/user/repo"

        # Emoji at start
        desc = "🚀 Fast tool"
        result = normalizer.normalize_description(url, desc)
        assert result.strip() == "Fast tool"

        # Emoji at end
        desc = "Fast tool 🚀"
        result = normalizer.normalize_description(url, desc)
        assert result.strip() == "Fast tool"

        # Only emoji
        desc = "🚀🔥💯"
        result = normalizer.normalize_description(url, desc)
        assert result.strip() == ""


class TestWhitespaceVariations:
    """Test handling of various whitespace patterns."""

    def test_title_with_tabs(self):
        """Should preserve title with tabs (no colon-stripping)."""
        normalizer = GitHubNormalizer()
        url = "https://github.com/user/repo"

        title = "user/repo:\tDescription\twith\ttabs"
        result = normalizer.normalize_title(url, title)
        assert result == "user/repo:\tDescription\twith\ttabs"

    def test_title_with_newlines(self):
        """Should preserve title with newlines (no colon-stripping)."""
        normalizer = GitHubNormalizer()
        url = "https://github.com/user/repo"

        title = "user/repo:\nDescription\nwith\nlines"
        result = normalizer.normalize_title(url, title)
        assert result == "user/repo:\nDescription\nwith\nlines"

    def test_description_with_mixed_whitespace(self):
        """Should handle mixed whitespace in description."""
        normalizer = GitHubNormalizer()
        url = "https://github.com/user/repo"

        desc = "Description\t with \n mixed   whitespace  - user/repo"
        result = normalizer.normalize_description(url, desc)

        # Should remove suffix
        assert " - user/repo" not in result
        # Should preserve the rest
        assert "Description" in result

    def test_leading_trailing_whitespace(self):
        """Should handle leading/trailing whitespace."""
        normalizer = GitHubNormalizer()
        url = "https://github.com/user/repo"

        title = "  user/repo: Description  "
        result = normalizer.normalize_title(url, title)
        # Should extract user/repo (whitespace handling depends on implementation)
        assert "user/repo" in result

    def test_excessive_whitespace(self):
        """Should handle excessive whitespace."""
        normalizer = GitHubNormalizer()
        url = "https://github.com/user/repo"

        desc = "Tool     with     many     spaces - user/repo"
        result = normalizer.normalize_description(url, desc)

        assert " - user/repo" not in result
        assert "Tool" in result

    def test_unicode_whitespace(self):
        """Should preserve title with Unicode whitespace (no colon-stripping)."""
        normalizer = GitHubNormalizer()
        url = "https://github.com/user/repo"

        # Non-breaking space (U+00A0)
        title = "user/repo:\u00A0Description"
        result = normalizer.normalize_title(url, title)
        assert result == "user/repo:\u00A0Description"

    def test_empty_string_after_normalization(self):
        """Should handle cases where normalization results in empty string."""
        normalizer = GitHubNormalizer()
        url = "https://github.com/user/repo"

        # Only whitespace and separators
        desc = "   - user/repo"
        result = normalizer.normalize_description(url, desc)

        # Should result in empty or whitespace-only string
        assert isinstance(result, str)
