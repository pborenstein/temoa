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
        """Should extract user/repo from 'user/repo: Description' format."""
        url = "https://github.com/user/repo"
        title = "user/repo: Turn any Git repository into a documentation link."
        result = self.normalizer.normalize_title(url, title)
        assert result == "user/repo"

    def test_normalize_title_with_dash_separator(self):
        """Should extract user/repo from 'user/repo - Description' format."""
        url = "https://github.com/user/repo"
        title = "user/repo - Turn any Git repository into a documentation link."
        result = self.normalizer.normalize_title(url, title)
        assert result == "user/repo"

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

        assert norm_title == "user/repo"
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
