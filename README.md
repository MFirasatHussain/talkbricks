# TalkBricks

TalkBricks is a beginner-friendly prototype for asking natural-language questions about Databricks data.

It does four things:

1. Takes a plain-English question from the user.
2. Uses the OpenAI API to generate Databricks SQL.
3. Validates the SQL so only read-only queries can run.
4. Executes the query against Databricks, or falls back to demo data when Databricks credentials are not configured.

## Project Structure

```text
app.py
requirements.txt
.env.example
README.md
src/
  config.py
  databricks_client.py
  llm.py
  metadata_loader.py
  sql_validator.py
metadata/
  tables.yaml
```

## Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate it

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
copy .env.example .env
```

Required variables:

```text
DATABRICKS_SERVER_HOSTNAME
DATABRICKS_HTTP_PATH
DATABRICKS_ACCESS_TOKEN
OPENAI_API_KEY
OPENAI_MODEL
```

If the Databricks values are missing, the app automatically switches to demo mode and returns a fake pandas DataFrame instead of failing.

## Run the App

```bash
streamlit run app.py
```

## Demo Mode

You can test the app without Databricks credentials.

1. Leave the Databricks variables blank.
2. Keep `OPENAI_API_KEY` optional if you want to test the UI without calling OpenAI.
3. Start the app with `streamlit run app.py`.

When demo mode is active, the UI clearly shows that the query results are synthetic.

## Safety Notes

- SQL validation blocks write and destructive statements.
- Only `SELECT` and `WITH` queries are allowed to run.
- Multiple statements separated by semicolons are rejected.
- Generated SQL should still be reviewed before use in any production environment.

## Where to Edit Metadata

Update [`metadata/tables.yaml`](./metadata/tables.yaml) to add real tables, columns, business definitions, and example questions.

## Future Improvements

- Add schema introspection from Databricks so metadata stays in sync automatically.
- Support query history and saved questions.
- Add richer SQL validation and query rewriting.
- Add authentication and role-based access controls.
- Show query plans and cost estimates before execution.
- Add charting for common aggregate results.

