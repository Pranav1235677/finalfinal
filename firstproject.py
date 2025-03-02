import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from faker import Faker
import random

# Initialize Faker
fake = Faker()

# Function to generate a simulated dataset
def generate_data(month):
    categories = ["Food", "Transportation", "Bills", "Groceries", "Entertainment", 
                  "Healthcare", "Shopping", "Dining", "Travel", "Education"]
    payment_modes = ["Cash", "Online", "NetBanking", "Credit Card", "Debit Card", "Wallet"]
    month_mapping = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12
    }
    data = []
    for _ in range(100):
        # Generate a random date within the specified month
        random_date = fake.date_between_dates(
            date_start=pd.Timestamp(year=2024, month=month_mapping[month], day=1),
            date_end=pd.Timestamp(year=2024, month=month_mapping[month], day=28)  # Adjust for month length
        )
        data.append({
            "Date": random_date,
            "Category": random.choice(categories),
            "Payment_Mode": random.choice(payment_modes),
            "Description": fake.sentence(nb_words=6),
            "Amount_Paid": round(random.uniform(10.0, 500.0), 2),
            "Cashback": round(random.uniform(0.0, 20.0), 2),
            "Month": month
        })
    return pd.DataFrame(data)

# Function to initialize the SQLite database with month-specific tables
def init_db():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    months = ["January", "February", "March", "April", "May", "June", 
              "July", "August", "September", "October", "November", "December"]
    for month in months:
        table_name = month.lower()  # Use lowercase for table names
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                Date TEXT,
                Category TEXT,
                Payment_Mode TEXT,
                Description TEXT,
                Amount_Paid REAL,
                Cashback REAL,
                Month TEXT
            )
        """)
    conn.commit()
    conn.close()

# Function to load data into the appropriate month table
def load_data_to_db(data, month):
    conn = sqlite3.connect('expenses.db')
    table_name = month.lower()
    data.to_sql(table_name, conn, if_exists='append', index=False)
    conn.close()

# Function to query data from a specific month table
def query_data_from_table(table):
    conn = sqlite3.connect('expenses.db')
    result = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    return result

# Initialize the database
init_db()

# Main Streamlit app
st.title("Personal Expense Tracker")

# Sidebar options
option = st.sidebar.selectbox(
    "Choose an option",
    ["Generate Data", "View Data", "Visualize Insights", "Run SQL Query", "Run Predefined SQL Queries"]
)

if option == "Generate Data":
    st.subheader("Generate Expense Data")
    month = st.text_input("Enter the month (e.g., January):", "January")
    if st.button("Generate"):
        try:
            data = generate_data(month)
            load_data_to_db(data, month)
            st.success(f"Data for {month} generated and loaded into the database!")
            st.dataframe(data.head())
        except KeyError:
            st.error("Invalid month entered. Please ensure the month is spelled correctly.")

elif option == "View Data":
    st.subheader("View Expense Data")
    month = st.text_input("Enter the month to view data (e.g., January):", "January")
    if st.button("View"):
        try:
            table = month.lower()
            data = query_data_from_table(table)
            st.dataframe(data)
        except Exception as e:
            st.error(f"An error occurred: {e}")

elif option == "Visualize Insights":
    st.subheader("Spending Insights")
    month = st.text_input("Enter the month to visualize data (e.g., January):", "January")
    if st.button("Visualize"):
        try:
            table = month.lower()
            query = f"SELECT Category, SUM(Amount_Paid) as Total_Spent FROM {table} GROUP BY Category"
            conn = sqlite3.connect('expenses.db')
            data = pd.read_sql_query(query, conn)
            conn.close()

            st.bar_chart(data.set_index("Category"))

            # Pie Chart
            fig, ax = plt.subplots()
            ax.pie(data["Total_Spent"], labels=data["Category"], autopct='%1.1f%%', startangle=140)
            ax.axis('equal')
            st.pyplot(fig)
        except Exception as e:
            st.error(f"An error occurred: {e}")

elif option == "Run SQL Query":
    st.subheader("Run Custom SQL Query")
    query = st.text_area("Enter your SQL query:")
    if st.button("Execute"):
        try:
            conn = sqlite3.connect('expenses.db')
            data = pd.read_sql_query(query, conn)
            conn.close()
            st.dataframe(data)
        except Exception as e:
            st.error(f"An error occurred: {e}")

elif option == "Run Predefined SQL Queries":
    st.subheader("Run Predefined SQL Queries")
    queries = {
        "Total Spending by Category": "SELECT Category, SUM(Amount_Paid) as Total_Spent FROM {table} GROUP BY Category",
        "Top 5 Highest Spending Transactions": "SELECT * FROM {table} ORDER BY Amount_Paid DESC LIMIT 5",
        "Total Cashback Earned": "SELECT SUM(Cashback) as Total_Cashback FROM {table}",
        "Monthly Spending Breakdown": "SELECT Month, SUM(Amount_Paid) as Total_Spent FROM {table} GROUP BY Month",
        "Average Transaction Amount": "SELECT AVG(Amount_Paid) as Average_Transaction FROM {table}",
        "Total Spending Per Payment Mode": "SELECT Payment_Mode, SUM(Amount_Paid) as Total_Spent FROM {table} GROUP BY Payment_Mode",
        "Transaction Count by Category": "SELECT Category, COUNT(*) as Transaction_Count FROM {table} GROUP BY Category",
        "Total Spending on Groceries": "SELECT SUM(Amount_Paid) as Grocery_Spending FROM {table} WHERE Category = 'Groceries'",
        "Highest Cashback Transactions": "SELECT * FROM {table} WHERE Cashback > 0 ORDER BY Cashback DESC LIMIT 5",
        "Daily Spending Breakdown": "SELECT Date, SUM(Amount_Paid) as Total_Spent FROM {table} GROUP BY Date ORDER BY Date ASC",
        "Spending on Food and Dining": "SELECT SUM(Amount_Paid) as Food_And_Dining_Spending FROM {table} WHERE Category IN ('Food', 'Dining')",
        "Categories with Cashback": "SELECT Category, SUM(Cashback) as Total_Cashback FROM {table} GROUP BY Category",
        "Spending Above 300": "SELECT * FROM {table} WHERE Amount_Paid > 300 ORDER BY Amount_Paid DESC",
        "Transaction Count by Payment Mode": "SELECT Payment_Mode, COUNT(*) as Transaction_Count FROM {table} GROUP BY Payment_Mode",
        "Top 3 Days with Highest Spending": "SELECT Date, SUM(Amount_Paid) as Total_Spent FROM {table} GROUP BY Date ORDER BY Total_Spent DESC LIMIT 3",
        "Lowest Spending Days": "SELECT Date, SUM(Amount_Paid) as Total_Spent FROM {table} GROUP BY Date ORDER BY Total_Spent ASC LIMIT 5",
        "Spending on Transportation": "SELECT SUM(Amount_Paid) as Transportation_Spending FROM {table} WHERE Category = 'Transportation'",
        "Transactions with Cashback": "SELECT * FROM {table} WHERE Cashback > 0",
        "Spending Trends by Week": "SELECT strftime('%W', Date) as Week, SUM(Amount_Paid) as Total_Spent FROM {table} GROUP BY Week",
        "Maximum Spending per Category": "SELECT Category, MAX(Amount_Paid) as Max_Spent FROM {table} GROUP BY Category",
        "Cash Transactions Only": "SELECT * FROM {table} WHERE Payment_Mode = 'Cash'",
        "Online Transactions Only": "SELECT * FROM {table} WHERE Payment_Mode = 'Online'",
        "Spending on Entertainment": "SELECT SUM(Amount_Paid) as Entertainment_Spending FROM {table} WHERE Category = 'Entertainment'",
        "Total Transactions per Month": "SELECT Month, COUNT(*) as Transaction_Count FROM {table} GROUP BY Month",
        "Average Cashback Earned": "SELECT AVG(Cashback) as Avg_Cashback FROM {table}",
        "High Spending Categories": "SELECT Category, SUM(Amount_Paid) as Total_Spent FROM {table} GROUP BY Category HAVING Total_Spent > 1000",
        "Transactions with No Cashback": "SELECT * FROM {table} WHERE Cashback = 0",
        "Spending Split by Payment Mode": "SELECT Payment_Mode, SUM(Amount_Paid) as Total_Spent FROM {table} GROUP BY Payment_Mode ORDER BY Total_Spent DESC",
        "Spending Summary": "SELECT Category, Payment_Mode, SUM(Amount_Paid) as Total_Spent FROM {table} GROUP BY Category, Payment_Mode ORDER BY Total_Spent DESC"
    }

    query_name = st.selectbox("Choose a predefined query", list(queries.keys()))
    month = st.text_input("Enter the month for the query (e.g., January):", "January")
    if st.button("Run Query"):
        try:
            table = month.lower()
            query = queries[query_name].format(table=table)
            conn = sqlite3.connect('expenses.db')
            data = pd.read_sql_query(query, conn)
            conn.close()
            st.dataframe(data)
        except Exception as e:
            st.error(f"An error occurred: {e}")