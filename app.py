import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import plotly.express as px

# Database setup
def init_db():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT,
                  type TEXT,
                  category TEXT,
                  amount REAL,
                  description TEXT)''')
    conn.commit()
    conn.close()

# Add transaction
def add_transaction(date, trans_type, category, amount, description):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute("INSERT INTO transactions (date, type, category, amount, description) VALUES (?, ?, ?, ?, ?)",
              (date, trans_type, category, amount, description))
    conn.commit()
    conn.close()

# Get all transactions
def get_transactions():
    conn = sqlite3.connect('expenses.db')
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()
    return df

# Delete transaction
def delete_transaction(trans_id):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE id=?", (trans_id,))
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Streamlit UI
st.title("💰 Personal Expense Tracker")

# Sidebar for adding transactions
st.sidebar.header("Add Transaction")

with st.sidebar.form("transaction_form"):
    date = st.date_input("Date", datetime.now())
    trans_type = st.selectbox("Type", ["Income", "Expense"])
    
    if trans_type == "Expense":
        category = st.selectbox("Category", ["Food", "Travel", "Bills", "Savings", "Other"])
    else:
        category = "Income"
    
    amount = st.number_input("Amount", min_value=0.0, step=0.01)
    description = st.text_input("Description")
    
    submitted = st.form_submit_button("Add Transaction")
    
    if submitted and amount > 0:
        add_transaction(str(date), trans_type, category, amount, description)
        st.success("Transaction added!")
        st.rerun()

# Main content
df = get_transactions()

if not df.empty:
    # Summary section
    st.header("📊 Summary")
    
    col1, col2, col3 = st.columns(3)
    
    total_income = df[df['type'] == 'Income']['amount'].sum()
    total_expense = df[df['type'] == 'Expense']['amount'].sum()
    balance = total_income - total_expense
    
    col1.metric("Total Income", f"₹{total_income:,.2f}")
    col2.metric("Total Expense", f"₹{total_expense:,.2f}")
    col3.metric("Balance", f"₹{balance:,.2f}", delta=f"{balance:,.2f}")
    
    # Monthly spending chart
    st.header("📈 Monthly Spending")
    
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M').astype(str)
    
    expense_df = df[df['type'] == 'Expense']
    monthly_expenses = expense_df.groupby('month')['amount'].sum().reset_index()
    
    if not monthly_expenses.empty:
        fig = px.bar(monthly_expenses, x='month', y='amount', 
                     title='Monthly Expenses',
                     labels={'amount': 'Amount (₹)', 'month': 'Month'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Category breakdown
    st.header("🏷️ Expense by Category")
    
    if not expense_df.empty:
        category_expenses = expense_df.groupby('category')['amount'].sum().reset_index()
        fig2 = px.pie(category_expenses, values='amount', names='category', 
                      title='Expense Distribution')
        st.plotly_chart(fig2, use_container_width=True)
    
    # Transactions table
    st.header("📋 All Transactions")
    
    # Display dataframe with delete option
    for idx, row in df.iterrows():
        col1, col2, col3, col4, col5, col6 = st.columns([1.5, 1, 1, 1, 2, 0.5])
        
        # Format date to display properly
        date_str = pd.to_datetime(row['date']).strftime('%Y-%m-%d')
        col1.write(date_str)
        col2.write(row['type'])
        col3.write(row['category'])
        col4.write(f"₹{row['amount']:,.2f}")
        col5.write(row['description'])
        
        if col6.button("🗑️", key=f"del_{row['id']}"):
            delete_transaction(row['id'])
            st.rerun()
    
    # Export to CSV
    st.header("💾 Export Data")
    
    # Format dataframe for export
    export_df = df.copy()
    export_df['date'] = pd.to_datetime(export_df['date']).dt.strftime('%Y-%m-%d')
    export_df = export_df[['id', 'date', 'type', 'category', 'amount', 'description']]
    
    csv = export_df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"expenses_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

else:
    st.info("No transactions yet. Add your first transaction using the sidebar!")
