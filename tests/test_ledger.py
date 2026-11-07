import pytest
from ledger import (add_bill, connect, due_date, list_month, month_totals,
                    seed_if_empty, set_paid, setup, valid_month)


@pytest.fixture
def db():
    conn = connect(':memory:')
    setup(conn)
    yield conn
    conn.close()


def test_seed_only_once(db):
    seed_if_empty(db)
    seed_if_empty(db)
    assert len(list_month(db, '2026-11')) == 6


def test_month_isolation(db):
    ident = add_bill(db, 'Test Rent', 120000, 1, 'Housing')
    set_paid(db, ident, '2026-11', True)
    assert list_month(db, '2026-11')[0]['is_paid']
    assert not list_month(db, '2026-12')[0]['is_paid']
    assert month_totals(list_month(db, '2026-11')) == {
        'total_cents': 120000, 'paid_cents': 120000, 'remaining_cents': 0}
    set_paid(db, ident, '2026-11', False)
    assert not list_month(db, '2026-11')[0]['is_paid']


def test_february_due_date_clamped():
    assert due_date('2028-02', 31).isoformat() == '2028-02-29'
    assert due_date('2027-02', 31).isoformat() == '2027-02-28'


@pytest.mark.parametrize('month', ['2026-13', '2026-1', 'not-a-month', '2026-02-30', ''])
def test_bad_month(month):
    with pytest.raises(ValueError):
        valid_month(month)


@pytest.mark.parametrize('name,cents,day,category', [('', 100, 5, 'Other'), ('Bill', -1, 5, 'Other'),
                                                     ('Bill', 100, 0, 'Other'), ('Bill', 100, 32, 'Other'),
                                                     ('Bill', 100, 10, '')])
def test_invalid_bill(db, name, cents, day, category):
    with pytest.raises(ValueError):
        add_bill(db, name, cents, day, category)


def test_mark_missing_bill(db):
    with pytest.raises(ValueError, match='does not exist'):
        set_paid(db, 100, '2026-11', True)
