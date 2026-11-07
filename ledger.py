"""SQLite-backed bill tracking logic; stores amounts as integer cents."""
from __future__ import annotations
import calendar
import sqlite3
from datetime import date
from pathlib import Path

SAMPLE_BILLS = (
    ('Apartment Rent', 145000, 1, 'Housing'),
    ('Electricity', 11500, 12, 'Utilities'),
    ('Internet', 6500, 15, 'Utilities'),
    ('Mobile Phone', 8500, 18, 'Utilities'),
    ('Car Insurance', 9800, 22, 'Transport'),
    ('Streaming Service', 1499, 25, 'Subscriptions'),
)


def connect(path: str | Path = 'demo_bills.sqlite3') -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def setup(conn: sqlite3.Connection) -> None:
    with conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL CHECK(length(trim(name)) > 0),
                amount_cents INTEGER NOT NULL CHECK(amount_cents >= 0),
                due_day INTEGER NOT NULL CHECK(due_day BETWEEN 1 AND 31),
                category TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS paid (
                bill_id INTEGER NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
                month TEXT NOT NULL,
                paid_on TEXT NOT NULL,
                PRIMARY KEY (bill_id, month)
            );
        ''')


def seed_if_empty(conn: sqlite3.Connection) -> None:
    if conn.execute('SELECT count(*) FROM bills').fetchone()[0]:
        return
    with conn:
        conn.executemany(
            'INSERT INTO bills (name, amount_cents, due_day, category) VALUES (?, ?, ?, ?)',
            SAMPLE_BILLS,
        )


def add_bill(conn: sqlite3.Connection, name: str, amount_cents: int, due_day: int, category: str) -> int:
    name = name.strip()
    category = category.strip()
    if not name or not category:
        raise ValueError('Name and category are required.')
    if isinstance(amount_cents, bool) or not isinstance(amount_cents, int) or amount_cents < 0:
        raise ValueError('Amount must be a nonnegative integer number of cents.')
    if isinstance(due_day, bool) or not isinstance(due_day, int) or not 1 <= due_day <= 31:
        raise ValueError('Due day must be an integer from 1 to 31.')
    with conn:
        cursor = conn.execute('INSERT INTO bills (name, amount_cents, due_day, category) VALUES (?, ?, ?, ?)',
                              (name, amount_cents, due_day, category))
    return cursor.lastrowid


def valid_month(month: str) -> str:
    try:
        parsed = date.fromisoformat(f'{month}-01')
    except (ValueError, TypeError):
        raise ValueError('Month must have format YYYY-MM.') from None
    if parsed.strftime('%Y-%m') != month:
        raise ValueError('Month must have format YYYY-MM.')
    return month


def due_date(month: str, due_day: int) -> date:
    valid_month(month)
    year, m = (int(p) for p in month.split('-'))
    return date(year, m, min(due_day, calendar.monthrange(year, m)[1]))


def list_month(conn: sqlite3.Connection, month: str) -> list[dict]:
    valid_month(month)
    rows = conn.execute('''
        SELECT b.*, p.paid_on FROM bills b
        LEFT JOIN paid p ON p.bill_id = b.id AND p.month = ?
        ORDER BY b.due_day, b.name
    ''', (month,)).fetchall()
    return [{**dict(row), 'due_date': due_date(month, row['due_day']).isoformat(),
             'is_paid': row['paid_on'] is not None} for row in rows]


def set_paid(conn: sqlite3.Connection, bill_id: int, month: str, paid: bool) -> None:
    valid_month(month)
    if conn.execute('SELECT id FROM bills WHERE id = ?', (bill_id,)).fetchone() is None:
        raise ValueError('Bill does not exist.')
    with conn:
        if paid:
            conn.execute('''INSERT INTO paid (bill_id, month, paid_on) VALUES (?, ?, ?)
                ON CONFLICT (bill_id, month) DO NOTHING''', (bill_id, month, date.today().isoformat()))
        else:
            conn.execute('DELETE FROM paid WHERE bill_id = ? AND month = ?', (bill_id, month))


def month_totals(rows: list[dict]) -> dict[str, int]:
    total = sum(row['amount_cents'] for row in rows)
    paid = sum(row['amount_cents'] for row in rows if row['is_paid'])
    return {'total_cents': total, 'paid_cents': paid, 'remaining_cents': total - paid}
