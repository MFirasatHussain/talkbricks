"""Basic SQL safety checks for TalkBricks.

This is intentionally conservative. We only want to allow read-only SQL that
begins with SELECT or WITH, and we want to reject obvious multi-statement or
destructive queries before they ever reach Databricks.
"""

from __future__ import annotations

import re

from sqlglot import ParseError, parse_one


class SQLValidationError(ValueError):
    """Raised when generated SQL is not safe enough to run."""


FORBIDDEN_KEYWORDS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "CREATE",
    "ALTER",
    "MERGE",
    "TRUNCATE",
    "GRANT",
    "REVOKE",
)


def _strip_trailing_semicolon(sql: str) -> str:
    """Allow one optional trailing semicolon, but nothing more."""
    stripped = sql.strip()
    if stripped.endswith(";"):
        stripped = stripped[:-1].rstrip()
    return stripped


def validate_sql(sql: str) -> str:
    """Validate that the SQL is a single read-only statement.

    Returns the cleaned SQL string if validation passes.
    Raises SQLValidationError if anything looks unsafe.
    """
    if not sql or not sql.strip():
        raise SQLValidationError("SQL is empty.")

    cleaned = _strip_trailing_semicolon(sql)

    if ";" in cleaned:
        raise SQLValidationError("Multiple SQL statements are not allowed.")

    if not re.match(r"^(SELECT|WITH)\b", cleaned, flags=re.IGNORECASE):
        raise SQLValidationError("Only SELECT or WITH queries are allowed.")

    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", cleaned, flags=re.IGNORECASE):
            raise SQLValidationError(f"Forbidden keyword detected: {keyword}.")

    try:
        parse_one(cleaned, read="spark")
    except ParseError as exc:
        raise SQLValidationError(f"SQL parsing failed: {exc}") from exc

    return cleaned

