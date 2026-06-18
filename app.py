import sqlite3
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from generate_db import build_enterprise_database

# Configure layout space
st.set_page_config(page_title="Executive Revenue Intelligence", layout="wide")

script_dir = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(script_dir, "saas_revenue.db")

# Self-healing database check
if not os.path.exists(DB_FILE):
    build_enterprise_database()

# Safe data query engine runner
def run_query(query):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Core Sidebar Navigation Control Panel
st.sidebar.title("Navigation Center")
page = st.sidebar.radio("Go To Panel:", ["Operational Alerts", "Executive Board Pack"])

# ------------------------------------------
# PAGE 1: OPERATIONAL ALERTS VIEW
# ------------------------------------------
if page == "Operational Alerts":
    st.title("Operational Revenue Leakage Engine")
    st.markdown("Real-time telemetry layer running historical window calculations across database logs.")
    st.markdown("---")
    
    # Advanced Predictive Risk Scoring Query utilizing CTEs and Mathematical Weights
    predictive_risk_query = """
    WITH MonthlyMetrics AS (
        SELECT 
            company_id,
            log_date,
            active_users_count as users,
            api_call_volume as api,
            support_tickets_count as tickets,
            LAG(active_users_count, 1) OVER (PARTITION BY company_id ORDER BY log_date) as prev_users,
            LAG(api_call_volume, 1) OVER (PARTITION BY company_id ORDER BY log_date) as prev_api
        FROM usage_logs
    ),
    LatestMetrics AS (
        SELECT 
            mm.*,
            c.company_name,
            c.industry,
            c.account_created,
            s.plan_tier,
            s.mrr,
            ROW_NUMBER() OVER (PARTITION BY mm.company_id ORDER BY mm.log_date DESC) as rn
        FROM MonthlyMetrics mm
        JOIN companies c ON mm.company_id = c.company_id
        JOIN subscriptions s ON c.company_id = s.company_id
        WHERE s.contract_status = 'Active'
    )
    SELECT 
        company_name,
        industry,
        plan_tier,
        mrr,
        users,
        tickets,
        ROUND(((users - prev_users) * 100.0 / (prev_users + 0.001)), 2) as user_change_pct,
        ROUND(((api - prev_api) * 100.0 / (prev_api + 0.001)), 2) as api_change_pct,
        -- SCORE FORMULA MATRIX: 40% User login + 30% API drops + 20% Seniority Context + 10% Tickets
        ROUND(
            (CASE WHEN ((users - prev_users) * 100.0 / (prev_users + 0.001)) <= -30.0 THEN 40 ELSE 0 END) +
            (CASE WHEN ((api - prev_api) * 100.0 / (prev_api + 0.001)) <= -30.0 THEN 30 ELSE 0 END) +
            (CASE WHEN tickets >= 5 THEN 10 ELSE 0 END) +
            (CASE WHEN CAST((JULIANDAY('now') - JULIANDAY(account_created)) AS INT) > 365 THEN 20 ELSE 5 END)
        , 2) as churn_risk_score
    FROM LatestMetrics
    WHERE rn = 1
    ORDER BY churn_risk_score DESC;
    """
    
    df_risk = run_query(predictive_risk_query)
    
    # Render Risk Matrix Visual KPI blocks
    critical_logos = len(df_risk[df_risk['churn_risk_score'] >= 60])
    exposed_cash = df_risk[df_risk['churn_risk_score'] >= 60]['mrr'].sum()
    
    m_col1, m_col2 = st.columns(2)
    m_col1.metric("Critical Churn-Risk Logos (Score >= 60)", f"{critical_logos} Accounts", delta="- Action Required", delta_color="inverse")
    m_col2.metric("At-Risk Exposed Monthly Revenue", f"${exposed_cash:,.2f}", delta="Exposed Capital Buffer", delta_color="off")
    
    st.markdown("---")
    st.subheader("Predictive Churn Ledger Matrix")
    
    # Render interactive data matrix sheet
    st.dataframe(df_risk[['company_name', 'industry', 'plan_tier', 'mrr', 'user_change_pct', 'api_change_pct', 'tickets', 'churn_risk_score']], use_container_width=True)
    
    with st.expander("Examine Predictive Score Matrix Formulation SQL"):
        st.code(predictive_risk_query, language="sql")

# ------------------------------------------
# PAGE 2: EXECUTIVE BOARD PACK VIEW
# ------------------------------------------
elif page == "Executive Board Pack":
    st.title("Executive Board Administration Pack")
    st.markdown("Macro-level corporate financial health analytics suite detailing institutional performance vectors.")
    st.markdown("---")
    
    # Financial Aggregations using industry standard SaaS accounting math
    saas_financial_query = """
    SELECT 
        SUM(CASE WHEN contract_status = 'Active' THEN mrr * 12 ELSE 0 END) as arr,
        SUM(CASE WHEN contract_status = 'Active' THEN mrr ELSE 0 END) as mrr,
        -- True Net Revenue Retention: Current Active Revenue / (Active + Historical Churned Revenue)
        ROUND((SUM(CASE WHEN contract_status = 'Active' THEN mrr ELSE 0 END) * 100.0) / 
        (SUM(mrr) + 0.001), 2) as nrr_pct,
        -- True Gross Churn calculation
        ROUND((SUM(CASE WHEN contract_status = 'Churned' THEN mrr ELSE 0 END) * 100.0) / 
        (SUM(mrr) + 0.001), 2) as gross_revenue_churn
    FROM subscriptions;
    """
    
    df_fin = run_query(saas_financial_query)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Annual Recurring Revenue (ARR)", f"${df_fin['arr'].iloc[0]:,.2f}")
    c2.metric("Monthly Recurring Revenue (MRR)", f"${df_fin['mrr'].iloc[0]:,.2f}")
    c3.metric("Net Revenue Retention (NRR)", f"{df_fin['nrr_pct'].iloc[0]}%")
    c4.metric("Gross Revenue Churn", f"{df_fin['gross_revenue_churn'].iloc[0]}%")
    
    st.markdown("---")
    
    # Financial concentration distribution chart panels
    graph_col1, graph_col2 = st.columns(2)
    
    with graph_col1:
        st.subheader("Industry Value & Revenue Concentration")
        df_ind = run_query("""
            SELECT c.industry, SUM(s.mrr) as revenue 
            FROM companies c JOIN subscriptions s ON c.company_id = s.company_id 
            WHERE s.contract_status = 'Active' GROUP BY c.industry;
        """)
        fig, ax = plt.subplots(figsize=(6, 3.5))
        sns.barplot(data=df_ind, x='revenue', y='industry', palette="Blues_r", ax=ax, hue='industry', legend=False)
        ax.set_xlabel("Total Active MRR ($)")
        st.pyplot(fig)
        plt.close()
        
    with graph_col2:
        st.subheader("Value Distribution Across Plan Tiers")
        df_tier = run_query("""
            SELECT plan_tier, SUM(mrr) as revenue 
            FROM subscriptions WHERE contract_status = 'Active' GROUP BY plan_tier;
        """)
        fig2, ax2 = plt.subplots(figsize=(6, 3.5))
        ax2.pie(df_tier['revenue'], labels=df_tier['plan_tier'], autopct='%1.1f%%', colors=['#2c3e50', '#3498db', '#bdc3c7'], startangle=90)
        st.pyplot(fig2)
        plt.close()