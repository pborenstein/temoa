"""
Custom exception types for Temoa.

Provides specific exception classes for different error scenarios to enable
better error handling and debugging. Never use bare `except Exception` -
always catch specific exception types.
"""


class TemoaError(Exception):
    """Base exception for all Temoa errors.

    All Temoa-specific exceptions inherit from this base class.
    This allows catching all Temoa errors with a single except clause
    while still allowing system exceptions (KeyboardInterrupt, SystemExit)
    to propagate correctly.
    """
    pass


class VaultReadError(TemoaError):
    """Error reading vault files.

    Raised when file I/O operations fail while reading vault content.
    Examples: file not found, permission denied, encoding errors.
    """
    pass


class SearchError(TemoaError):
    """Error during search operation.

    Raised when search operations fail. This includes semantic search,
    BM25 search, hybrid search, and archaeology operations.
    """
    pass


class IndexError(TemoaError):
    """Error during indexing operation.

    Raised when building or updating search indexes fails.
    Examples: embedding generation failed, BM25 index build failed,
    storage write failed.

    Note: Shadows built-in IndexError, but this is intentional and scoped
    to Temoa module. Use `builtins.IndexError` if you need the built-in.
    """
    pass


class ConfigError(TemoaError):
    """Configuration error.

    Raised when configuration is invalid or missing.
    Examples: config file not found, invalid JSON, missing required fields,
    vault path doesn't exist.
    """
    pass


class GleaningError(TemoaError):
    """Error during gleaning operations.

    Raised when gleaning extraction, maintenance, or status management fails.
    Examples: invalid frontmatter, URL normalization failed, link check failed.
    """
    pass
