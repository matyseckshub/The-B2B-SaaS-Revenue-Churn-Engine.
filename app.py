import sqlite3
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# DYNAMIC IMPORT: Imports the database generator script automatically
from generate_db import build_enterprise_database

# Set page structure to enterprise style
st.set_page_config(page_title="Enterprise Revenue Intelligence Platform", layout="wide")
st.title("Enterprise Revenue & Churn Intelligence Engine")
st.markdown("---")

# Dynamic path targeting
script_dir = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(script_dir, "saas_revenue.db")

# ==========================================
# AUTOMATED PRODUCTION INITIALIZATION
# ==========================================
# If deployed on the web or run freshly and the DB file is missing, 
# this block auto-generates the database dynamically so the app never crashes.
if not os.path.exists(DB_FILE):
    with st.spinner("Initializing relational database engine and generating records..."):
        build_enterprise_database()

# ==========================================
# 1. THE PURE SQL ANALYTICS QUERIES 
# ==========================================

financials_query = """
SELECT 
    SUM(CASE WHEN contract_status = 'Active' THEN monthly_recurring_revenue * 12 ELSE 0 END) as ARR,
    COUNT(CASE WHEN contract_status = 'Active' THEN 1 END) as Active_Logos,
    SUM(CASE WHEN contract_status = 'Churned' THEN monthly_recurring_revenue ELSE 0 END) * 100.0 / 
    (SUM(monthly_recurring_revenue) + 0.0001) as Churn_Rate_Percentage
FROM subscriptions;
"""

leak_detection_query = """
WITH MonthlyUsage AS (
    SELECT 
        company_id,
        STRFTIME('%Y-%m', log_date) as activity_month,
        active_users_count as current_users,
        LAG(active_users_count, 1) OVER (PARTITION BY company_id ORDER BY log_date) as previous_users
    FROM usage_logs
)
SELECT 
    c.company_name,
    c.industry,
    s.plan_tier,
    s.monthly_recurring_revenue,
    mu.current_users,
    mu.previous_users,
    ROUND(((mu.current_users - mu.previous_users) * 100.0 / mu.previous_users), 2) as user_drop_percentage
FROM MonthlyUsage mu
JOIN companies c ON mu.company_id = c.company_id
JOIN subscriptions s ON c.company_id = s.company_id
WHERE mu.previous_users IS NOT NULL 
  AND user_drop_percentage <= -40.0
  AND s.contract_status = 'Active'
ORDER BY user_drop_percentage ASC;
"""

# Fetch datasets safely from our generated SQL file
conn = sqlite3.connect(DB_FILE)
df_finance = pd.read_sql_query(financials_query, conn)
df_leaks = pd.read_sql_query(leak_detection_query, conn)
conn.close()

# ==========================================
# 2. EXECUTIVE FRONTEND INTERFACE
# ==========================================

arr_val = df_finance['ARR'].iloc[0] or 0.0
logos_val = df_finance['Active_Logos'].iloc[0] or 0
churn_val = df_finance['Churn_Rate_Percentage'].iloc[0] or 0.0

col1, col2, col3 = st.columns(3)
col1.metric("Annual Recurring Revenue (ARR)", f"${arr_val:,.2f}")
col2.metric("Active Enterprise Client Accounts", f"{logos_val} Logos")
col3.metric("Gross Revenue Churn Rate", f"{churn_val:.2f}%")

st.markdown("---")

left_col, right_col = st.columns([3, 2])

with left_col:
    st.subheader("Operational Revenue Leakage Alert Matrix")
    st.markdown("Accounts with user engagement drops greater than 40% month-over-month.")
    
    st.dataframe(
        df_leaks[['company_name', 'industry', 'plan_tier', 'monthly_recurring_revenue', 'user_drop_percentage']],
        use_container_width=True
    )

with right_col:
    st.subheader("Enterprise Tech Stack Proof")
    st.markdown("This live report executes an advanced SQL query utilizing CTEs and Window Functions directly.")
    with st.expander("Inspect Raw SQL Architecture Code"):
        st.code(leak_detection_query, language="sql")

st.markdown("---")
st.subheader("Industry Value Concentration")

conn = sqlite3.connect(DB_FILE)
df_chart = pd.read_sql_query("""
    SELECT c.industry, SUM(s.monthly_recurring_revenue) as mrr 
    FROM companies c 
    JOIN subscriptions s ON c.company_id = s.company_id 
    WHERE s.contract_status = 'Active' 
    GROUP BY c.industry;
""", conn)
conn.close()

fig, ax = plt.subplots(figsize=(8, 3))
sns.barplot(data=df_chart, x='mrr', y='industry', palette="Blues_r", ax=ax, hue='industry', legend=False)
ax.set_xlabel("Total Monthly Recurring Revenue (USD)")
ax.set_ylabel("Industry Sector")
st.pyplot(fig)