# Bills Tracker Demo

A small Python/Streamlit app for viewing monthly bills, recording paid status, and adding bills.

**Public demo only:** Every supplied bill, amount, and category is invented. There are no bank accounts, real customer records, secrets, API keys, or finance integrations. This is an independent demo version, **not a copy of the owner's private application**.

## Features
- Monthly bill list with due dates and categories
- Local paid/unpaid tracking for each month
- Monthly planned, paid, and remaining totals
- Add bills via a form
- Local SQLite storage (file ignored by Git)
- Unit tests for monthly isolation, validation, and shorter months

## Run locally

Requires Python 3.10+.

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

The app creates `demo_bills.sqlite3` automatically the first time it runs. This local database is excluded from version control.

## Test

```bash
pip install -r requirements-dev.txt
python -m pytest
```

## Repository layout

```text
app.py                  Streamlit interface
ledger.py               SQLite bill logic
requirements.txt        Runtime dependencies
requirements-dev.txt    Test dependencies
tests/test_ledger.py     Unit tests
```

## Security and privacy
- Never commit a real transaction export or a database containing real data.
- `.gitignore` excludes SQLite databases, `.env` files, credentials, and common local build files.
- Before publishing, check the entire Git history as well as the working tree if you use this inside an existing repository.
- This application is a tracker, not payment software.

## License
MIT. See `LICENSE`.
