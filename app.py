"""Streamlit entry point for TalkBricks.

This file keeps the UI logic lightweight and beginner-friendly.
The app asks a question, generates SQL, validates it, and runs it
against Databricks or demo data depending on the environment.
"""

from __future__ import annotations

import streamlit as st

from src.config import get_settings, is_demo_mode
from src.databricks_client import run_query
from src.llm import generate_sql
from src.metadata_loader import load_metadata
from src.sql_validator import SQLValidationError, validate_sql


st.set_page_config(
    page_title="TalkBricks",
    page_icon="TB",
    layout="wide",
)


def initialize_state() -> None:
    """Create the session state keys we use across button clicks."""
    defaults = {
        "generated_sql": "",
        "result_df": None,
        "status_message": "",
        "error_message": "",
        "question": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_header(demo_active: bool) -> None:
    """Render the title area and the mode banner."""
    st.title("TalkBricks")
    st.subheader("Ask questions about your Databricks data")
    st.caption("Generate SQL, validate it, and run it in a safe read-only flow.")

    if demo_active:
        st.info(
            "Demo mode is active because one or more Databricks environment "
            "variables are missing. The app will return a fake pandas DataFrame "
            "so you can test the full UI without a live warehouse."
        )


def render_sidebar(metadata: dict, demo_active: bool) -> None:
    """Show a small sidebar with project context."""
    st.sidebar.header("TalkBricks")
    st.sidebar.write("Prototype for natural-language queries over Databricks.")
    st.sidebar.write(f"Mode: {'Demo' if demo_active else 'Databricks connected'}")

    tables = metadata.get("tables", [])
    if tables:
        st.sidebar.subheader("Loaded Tables")
        for table in tables:
            st.sidebar.write(f"- {table.get('full_name') or table.get('name')}")


def main() -> None:
    initialize_state()

    settings = get_settings()
    metadata = load_metadata(settings.metadata_path)
    demo_active = is_demo_mode(settings)

    render_header(demo_active)
    render_sidebar(metadata, demo_active)

    question = st.text_input(
        "Your question",
        placeholder="For example: show total spend and clicks by advertiser last 30 days",
        key="question",
    )

    col_generate, col_run = st.columns(2)

    with col_generate:
        generate_clicked = st.button("Generate SQL", use_container_width=True)
    with col_run:
        run_clicked = st.button(
            "Run Query",
            use_container_width=True,
            disabled=not st.session_state.generated_sql,
        )

    if generate_clicked:
        st.session_state.error_message = ""
        st.session_state.status_message = ""
        st.session_state.result_df = None
        try:
            if not question.strip():
                raise ValueError("Please enter a question before generating SQL.")
            st.session_state.generated_sql = generate_sql(question, metadata)
            st.session_state.status_message = "SQL generated successfully."
        except Exception as exc:  # noqa: BLE001 - beginner-friendly UI error handling
            st.session_state.generated_sql = ""
            st.session_state.error_message = f"SQL generation failed: {exc}"

    if run_clicked:
        st.session_state.error_message = ""
        st.session_state.status_message = ""
        try:
            if not st.session_state.generated_sql.strip():
                raise ValueError("Generate SQL first, then run the query.")

            validated_sql = validate_sql(st.session_state.generated_sql)
            st.session_state.result_df = run_query(validated_sql, settings)
            st.session_state.status_message = "Query executed successfully."
        except SQLValidationError as exc:
            st.session_state.result_df = None
            st.session_state.error_message = f"SQL validation failed: {exc}"
        except Exception as exc:  # noqa: BLE001 - show execution errors directly in the UI
            st.session_state.result_df = None
            st.session_state.error_message = f"Query execution failed: {exc}"

    if st.session_state.status_message:
        st.success(st.session_state.status_message)

    if st.session_state.error_message:
        st.error(st.session_state.error_message)

    st.markdown("### Generated SQL")
    if st.session_state.generated_sql.strip():
        st.code(st.session_state.generated_sql, language="sql")
    else:
        st.code("-- Your generated SQL will appear here.", language="sql")

    st.markdown("### Results")
    if st.session_state.result_df is not None:
        st.dataframe(st.session_state.result_df, use_container_width=True)
    else:
        st.write("No results yet. Generate SQL, then run the query.")


if __name__ == "__main__":
    main()
