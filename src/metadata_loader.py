"""Metadata loading helpers.

The LLM prompt is only as good as the schema and business definitions we give it.
This file loads metadata/tables.yaml and formats it into a compact prompt block.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_metadata(path: str | Path) -> dict[str, Any]:
    """Load table metadata from YAML.

    If the file is missing or empty, the app still works and simply prompts with
    an empty metadata set.
    """
    metadata_path = Path(path)
    if not metadata_path.exists():
        return {"tables": []}

    with metadata_path.open("r", encoding="utf-8") as file:
        loaded = yaml.safe_load(file) or {}

    if not isinstance(loaded, dict):
        return {"tables": []}

    loaded.setdefault("tables", [])
    return loaded


def format_metadata_for_prompt(metadata: dict[str, Any]) -> str:
    """Turn the YAML metadata into a compact text block for the LLM prompt."""
    tables = metadata.get("tables", [])
    if not tables:
        return "No table metadata is available."

    lines: list[str] = []
    for table in tables:
        table_name = table.get("full_name") or table.get("name") or "unknown_table"
        description = table.get("description", "")
        business_definition = table.get("business_definition", "")
        lines.append(f"Table: {table_name}")
        if description:
            lines.append(f"  Description: {description}")
        if business_definition:
            lines.append(f"  Business definition: {business_definition}")

        columns = table.get("columns", [])
        if columns:
            lines.append("  Columns:")
            for column in columns:
                column_name = column.get("name", "unknown_column")
                column_type = column.get("type", "unknown_type")
                column_description = column.get("description", "")
                column_business = column.get("business_definition", "")
                column_line = f"    - {column_name} ({column_type})"
                if column_description:
                    column_line += f": {column_description}"
                lines.append(column_line)
                if column_business:
                    lines.append(f"      Business definition: {column_business}")

        examples = table.get("example_questions", [])
        if examples:
            lines.append("  Example questions:")
            for example in examples:
                lines.append(f"    - {example}")

        lines.append("")

    return "\n".join(lines).strip()

