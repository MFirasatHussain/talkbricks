"""Natural-language-to-SQL generation for TalkBricks.

The app prefers the OpenAI API when credentials are available. If the API is not
configured, a small rule-based fallback keeps the prototype runnable for demos.
"""

from __future__ import annotations

import re
from typing import Any

from openai import OpenAI

from src.config import get_settings
from src.metadata_loader import format_metadata_for_prompt


def _strip_code_fences(text: str) -> str:
    """Remove markdown fences if the model accidentally returns them."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped


def _first_table(metadata: dict[str, Any]) -> str:
    """Pick the first table from metadata as the safest fallback target."""
    tables = metadata.get("tables", [])
    if not tables:
        return "campaign_performance"
    return tables[0].get("full_name") or tables[0].get("name") or "campaign_performance"


def _contains_any(text: str, keywords: list[str]) -> bool:
    lower_text = text.lower()
    return any(keyword in lower_text for keyword in keywords)


def _rule_based_sql(question: str, metadata: dict[str, Any]) -> str:
    """Fallback SQL generator used when OpenAI is unavailable."""
    table_name = _first_table(metadata)
    question_lower = question.lower()

    if _contains_any(question_lower, ["by advertiser", "group by advertiser", "advertiser performance"]):
        sql = f"""
SELECT
  advertiser_name,
  SUM(impressions) AS total_impressions,
  SUM(spend) AS total_spend,
  SUM(clicks) AS total_clicks
FROM {table_name}
GROUP BY advertiser_name
ORDER BY total_impressions DESC
LIMIT 100
"""
        return sql.strip()

    if _contains_any(question_lower, ["clicks", "spend", "impressions", "campaign"]):
        sql = f"""
SELECT
  campaign_id,
  advertiser_name,
  air_date,
  impressions,
  spend,
  clicks
FROM {table_name}
ORDER BY air_date DESC
LIMIT 100
"""
        return sql.strip()

    if _contains_any(question_lower, ["last 30 days", "past 30 days", "recent"]):
        sql = f"""
SELECT
  campaign_id,
  advertiser_name,
  air_date,
  impressions,
  spend,
  clicks
FROM {table_name}
WHERE air_date >= date_sub(current_date(), 30)
ORDER BY air_date DESC
LIMIT 100
"""
        return sql.strip()

    return f"SELECT * FROM {table_name} LIMIT 100"


def _append_default_limit(sql: str) -> str:
    """Add LIMIT 100 when the model forgot to include a limit."""
    normalized = sql.strip()

    if normalized.endswith(";"):
        normalized = normalized[:-1].rstrip()

    if normalized.startswith("--"):
        return normalized

    if re.search(r"\blimit\b", normalized, flags=re.IGNORECASE):
        return normalized

    return f"{normalized} LIMIT 100"


def generate_sql(question: str, metadata: dict[str, Any]) -> str:
    """Generate a Databricks-safe SQL query from a natural-language question.

    The function returns SQL only. If the question is too unclear, the model is
    instructed to return a comment instead of guessing.
    """
    question = (question or "").strip()
    if not question:
        return "-- Please enter a question."

    settings = get_settings()
    metadata_block = format_metadata_for_prompt(metadata)

    if not settings.openai_api_key:
        # Demo fallback: keep the app runnable even without OpenAI credentials.
        return _append_default_limit(_rule_based_sql(question, metadata))

    client = OpenAI(api_key=settings.openai_api_key)
    system_prompt = (
        "You are a careful SQL generator for Databricks SQL.\n"
        "Return SQL only. Do not include markdown, code fences, or explanations.\n"
        "Rules:\n"
        "- Only generate SELECT queries.\n"
        "- Always add LIMIT 100 unless the user explicitly asks for a smaller limit.\n"
        "- Never generate INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, MERGE, TRUNCATE, GRANT, or REVOKE.\n"
        "- Use fully qualified table names from the metadata when available.\n"
        "- Use Databricks SQL syntax.\n"
        "- If the question is unclear and a safe SQL query is not possible, return a SQL comment that says the question needs clarification.\n"
    )

    user_prompt = (
        "Metadata:\n"
        f"{metadata_block}\n\n"
        f"Question:\n{question}\n"
    )

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or ""
        cleaned = _strip_code_fences(content).strip()
        if not cleaned:
            return "-- The question needs clarification."
        return _append_default_limit(cleaned)
    except Exception:
        # If the API call fails, fall back to a deterministic local query so the
        # prototype remains usable in demos and workshops.
        return _append_default_limit(_rule_based_sql(question, metadata))
