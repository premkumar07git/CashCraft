import streamlit as st
import sqlite3
import pandas as pd
from datetime import date as dt_date, datetime
import matplotlib.pyplot as plt 
import atexit


class ExpenseDB:
    def __init__(self):
        self.conn = sqlite3.connect("expenses.db", check_same_thread=False)
        self.create_table()

    def create_table(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                category TEXT,
                amount REAL,
                description TEXT
            )
        ''')
        self.conn.commit()

    def add_expense(self, date, category, amount, description):
        self.conn.execute(
            "INSERT INTO expenses (date, category, amount, description) VALUES (?, ?, ?, ?)",
            (str(date), category, amount, description)
        )
        self.conn.commit()

    def get_all_expenses(self):
        return pd.read_sql_query("SELECT * FROM expenses ORDER BY date DESC", self.conn)

    def get_category_totals(self):
        return pd.read_sql_query("SELECT category, SUM(amount) as total FROM expenses GROUP BY category", self.conn)

    def close(self):
        self.conn.close()


db = ExpenseDB()


DEFAULT_VALUES = {
    "date": dt_date.today(),
    "category": "Food",
    "amount": 0.0,
    "description": ""
}


if "form_toggle" not in st.session_state:
    st.session_state.form_toggle = False

st.title("💸 CashCraft Pro – SQLite Expense Tracker")
st.caption("Track and visualize your expenses effortlessly")


key_suffix = str(st.session_state.form_toggle)


with st.form("expense_form"):
    date = st.date_input("Date", value=DEFAULT_VALUES["date"], key=f"date_{key_suffix}")
    category = st.selectbox("Category", ["Food", "Bills", "Shopping", "Transport", "Entertainment","House rent", "Other"], key=f"category_{key_suffix}")
    amount = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f", key=f"amount_{key_suffix}")
    description = st.text_input("Description", key=f"description_{key_suffix}")
    submit = st.form_submit_button("➕ Add Expense")


if submit:
    if amount <= 0:
        st.error("Amount must be greater than 0")
    else:
        db.add_expense(date, category, amount, description)
        st.success("✅ Expense added successfully!")
        st.session_state.form_toggle = not st.session_state.form_toggle
        st.rerun()  # Rerun the script to refresh input fields

st.subheader("📁 Upload Cleaned CSV File")
uploaded_file = st.file_uploader("Upload a CSV", type=["csv"])

if uploaded_file is not None:
   
    try:
        file_df = pd.read_csv(uploaded_file)

       
        st.write("📄 File Preview:")
        st.dataframe(file_df)

       
        if st.button("📤 Import to Database"):
            for _, row in file_df.iterrows():
               
                if pd.notna(row['date']) and pd.notna(row['category']) and pd.notna(row['amount']):
                    db.add_expense(
                        row['date'],
                        row['category'],
                        float(row['amount']),
                        row.get('description', '') if 'description' in row else ''
                    )
            st.success("✅ Data imported successfully!")
            st.rerun()

    except Exception as e:
        st.error(f"Error processing file: {e}")


st.subheader("📊 All Expenses")
df = db.get_all_expenses()


if not df.empty:
    min_date = datetime.strptime(df['date'].min(), "%Y-%m-%d").date()
    max_date = datetime.strptime(df['date'].max(), "%Y-%m-%d").date()
else:
    min_date = max_date = dt_date.today()


st.dataframe(df, use_container_width=True)





st.subheader("📈 Summary")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Expenses", f"${df['amount'].sum():.2f}" if not df.empty else "$0.00")
with col2:
    st.metric("Transactions", len(df))
with col3:
    st.metric("Average Expense", f"${df['amount'].mean():.2f}" if not df.empty else "$0.00")


st.subheader("📊 Expense by Category")
cat_data = db.get_category_totals()
if not cat_data.empty:
    st.bar_chart(cat_data.set_index('category'))
else:
    st.info("No data to display")



st.subheader("📊 Category-wise Expense (Matplotlib)")
if not cat_data.empty:
    fig, ax = plt.subplots()
    ax.bar(cat_data['category'], cat_data['total'], color='skyblue')
    ax.set_xlabel("Category")
    ax.set_ylabel("Total Amount")
    ax.set_title("Total Expenses by Category")
    ax.grid(axis='y')
    st.pyplot(fig)
else:
    st.info("No data available")

st.subheader("📌 Expense Share by Category (Pie Chart)")
if not cat_data.empty:
    fig, ax = plt.subplots()
    ax.pie(cat_data['total'], labels=cat_data['category'], autopct='%1.1f%%', startangle=140)
    ax.axis('equal')  # Equal aspect ratio ensures pie is drawn as a circle
    st.pyplot(fig)



st.subheader("📆 Monthly Expenses Summary")
if not df.empty:
    df['month'] = pd.to_datetime(df['date']).dt.to_period('M').astype(str)
    monthly = df.groupby('month')['amount'].sum().reset_index()
    fig, ax = plt.subplots()
    ax.bar(monthly['month'], monthly['amount'], color='lightgreen')
    ax.set_title("Monthly Expenses")
    ax.set_xlabel("Month")
    ax.set_ylabel("Amount")
    ax.tick_params(axis='x', rotation=45)
    st.pyplot(fig)



st.download_button("💾 Export as CSV", df.to_csv(index=False).encode('utf-8'), "expenses.csv", "text/csv")


atexit.register(db.close)
 
