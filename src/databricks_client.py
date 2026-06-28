"""Databricks SQL execution helpers.

This module runs SQL against a real Databricks SQL warehouse when credentials
are present, and returns a fake pandas DataFrame in demo mode so the prototype
still works end-to-end without any external setup.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.config import Settings, is_demo_mode


def _demo_dataframe() -> pd.DataFrame:
    """Return a simple sample dataframe for local testing."""
    return pd.DataFrame(
        [
            {
                "campaign_id": "cmp_1001",
                "advertiser_name": "Northwind",
                "air_date": "2026-06-24",
                "impressions": 154200,
                "spend": 842.15,
                "clicks": 1824,
            },
            {
                "campaign_id": "cmp_1002",
                "advertiser_name": "Contoso",
                "air_date": "2026-06-25",
                "impressions": 98050,
                "spend": 611.70,
                "clicks": 1092,
            },
            {
                "campaign_id": "cmp_1003",
                "advertiser_name": "Fabrikam",
                "air_date": "2026-06-26",
                "impressions": 221430,
                "spend": 1195.40,
                "clicks": 2689,
            },
        ]
    )


def _run_databricks_sql(sql: str, settings: Settings) -> pd.DataFrame:
    """Execute SQL against Databricks and return the result as a DataFrame."""
    from databricks import sql as databricks_sql

    connection = databricks_sql.connect(
        server_hostname=settings.databricks_server_hostname,
        http_path=settings.databricks_http_path,
        access_token=settings.databricks_access_token,
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description] if cursor.description else []
            return pd.DataFrame(rows, columns=columns)
    finally:
        connection.close()


def run_query(sql: str, settings: Settings) -> pd.DataFrame:
    """Run a validated SQL query and return results as a DataFrame."""
    if is_demo_mode(settings):
        return _demo_dataframe()

    return _run_databricks_sql(sql, settings)

