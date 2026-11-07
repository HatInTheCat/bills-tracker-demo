"""A public-safe monthly bills dashboard using synthetic demo data."""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import os
from pathlib import Path
import streamlit as st
from ledger import add_bill, connect, list_month, month_totals, seed_if_empty, set_paid, setup

st.set_page_config(page_title='Bills Tracker Demo', page_icon='📅', layout='wide')
DB_PATH = Path(os.environ.get('BILLS_DEMO_DB', 'demo_bills.sqlite3'))


def money(cents: int) -> str:
    return f'${cents / 100:,.2f}'


def get_conn():
    conn = connect(DB_PATH)
    setup(conn)
    seed_if_empty(conn)
    return conn


st.title('📅 Bills Tracker — Sample Data')
st.caption('Demo only • All bill names and amounts are fictional • No bank integrations')
month = st.date_input('Choose a month', value=date.today().replace(day=1)).strftime('%Y-%m')
with get_conn() as conn:
    bills = list_month(conn, month)
    totals = month_totals(bills)

col1, col2, col3 = st.columns(3)
col1.metric('Planned', money(totals['total_cents']))
col2.metric('Paid', money(totals['paid_cents']))
col3.metric('Remaining', money(totals['remaining_cents']))
st.subheader(f'Bills for {month}')

for bill in bills:
    row = st.columns([1, 3, 2, 2, 2])
    updated = row[0].checkbox('Paid', value=bill['is_paid'], key=f'{month}-{bill["id"]}',
                              label_visibility='collapsed')
    row[1].write(bill['name'])
    row[2].write(bill['category'])
    row[3].write(bill['due_date'])
    row[4].write(money(bill['amount_cents']))
    if updated != bill['is_paid']:
        with get_conn() as conn:
            set_paid(conn, bill['id'], month, updated)
        st.rerun()

with st.expander('Add a sample bill'):
    with st.form('new_bill'):
        name = st.text_input('Bill name')
        category = st.selectbox('Category', ['Housing', 'Utilities', 'Transport', 'Subscriptions', 'Other'])
        amount = st.number_input('Amount ($)', min_value=0.00, value=25.00, step=1.00)
        day = st.number_input('Due day', min_value=1, max_value=31, value=15, step=1)
        if st.form_submit_button('Add bill'):
            cents = int((Decimal(str(amount)) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
            try:
                with get_conn() as conn:
                    add_bill(conn, name, cents, int(day), category)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

st.info('Payment checkboxes are local tracking only. They do not send payments or connect to any accounts.')
