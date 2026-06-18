import sqlite3
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from generate_db import build_enterprise_database

# Configure view space
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

# Core Navigation Panel
st.sidebar.title("Navigation Center")
page = st.sidebar.radio("Go To Panel:", ["Operational Alerts", "Executive Board Pack", "Written Strategic Report"])

# ==========================================
# CENTRAL DATABASE CALCULATIONS & PREPARATIONS
# ==========================================
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

saas_financial_query = """
SELECT 
    SUM(CASE WHEN contract_status = 'Active' THEN mrr * 12 ELSE 0 END) as arr,
    SUM(CASE WHEN contract_status = 'Active' THEN mrr ELSE 0 END) as mrr,
    ROUND((SUM(CASE WHEN contract_status = 'Active' THEN mrr ELSE 0 END) * 100.0) / (SUM(mrr) + 0.001), 2) as nrr_pct,
    ROUND((SUM(CASE WHEN contract_status = 'Churned' THEN mrr ELSE 0 END) * 100.0) / (SUM(mrr) + 0.001), 2) as gross_revenue_churn,
    COUNT(CASE WHEN contract_status = 'Active' THEN 1 END) as active_logos
FROM subscriptions;
"""

# Extract global variables for cross-page metrics integration
df_risk = run_query(predictive_risk_query)
df_fin = run_query(saas_financial_query)

arr_val = df_fin['arr'].iloc[0] or 0.0
mrr_val = df_fin['mrr'].iloc[0] or 0.0
nrr_val = df_fin['nrr_pct'].iloc[0] or 0.0
churn_val = df_fin['gross_revenue_churn'].iloc[0] or 0.0
logos_val = df_fin['active_logos'].iloc[0] or 0

critical_df = df_risk[df_risk['churn_risk_score'] >= 60]
critical_logos = len(critical_df)
exposed_mrr = critical_df['mrr'].sum()
exposed_arr = exposed_mrr * 12

# ------------------------------------------
# PANEL 1: OPERATIONAL ALERTS VIEW
# ------------------------------------------
if page == "Operational Alerts":
    st.title("Operational Revenue Leakage Engine")
    st.markdown("Real-time telemetry layer running historical window calculations across database logs.")
    st.markdown("---")
    
    m_col1, m_col2 = st.columns(2)
    m_col1.metric("Critical Churn-Risk Logos (Score >= 60)", f"{critical_logos} Accounts", delta="- Action Required", delta_color="inverse")
    m_col2.metric("At-Risk Exposed Monthly Revenue", f"${exposed_mrr:,.2f}", delta="Exposed Capital Buffer", delta_color="off")
    
    st.markdown("---")
    st.subheader("Predictive Churn Ledger Matrix")
    st.dataframe(df_risk[['company_name', 'industry', 'plan_tier', 'mrr', 'user_change_pct', 'api_change_pct', 'tickets', 'churn_risk_score']], use_container_width=True)
    
    with st.expander("Examine Predictive Score Matrix Formulation SQL"):
        st.code(predictive_risk_query, language="sql")

# ------------------------------------------
# PANEL 2: EXECUTIVE BOARD PACK VIEW
# ------------------------------------------
elif page == "Executive Board Pack":
    st.title("Executive Board Administration Pack")
    st.markdown("Macro-level corporate financial health analytics suite detailing institutional performance vectors.")
    st.markdown("---")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Annual Recurring Revenue (ARR)", f"${arr_val:,.2f}")
    c2.metric("Monthly Recurring Revenue (MRR)", f"${mrr_val:,.2f}")
    c3.metric("Net Revenue Retention (NRR)", f"{nrr_val}%")
    c4.metric("Gross Revenue Churn", f"{churn_val}%")
    
    st.markdown("---")
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

# ------------------------------------------
# PANEL 3: WRITTEN STRATEGIC REPORT (The Lost Report Restored)
# ------------------------------------------
elif page == "Written Strategic Report":
    st.title("Strategic Analysis Briefing: ARR Defense & Churn Anomalies")
    st.markdown("*Official Board of Directors Performance Ledger — Generated Live from Operational Databases*")
    st.markdown("---")
    
    # Section 1
    st.subheader("1. Strategic Financial Health Summary")
    st.markdown(f"""
    An executive audit of our relational ledger indicates a strong top-line operational structure, countered by an immediate capital concentration risk. 
    The platform currently maintains a stable **Annual Recurring Revenue (ARR)** run rate of **${arr_val:,.2f}** across **{logos_val} active corporate accounts**. 

    However, our macro core metric calculation indicates a **Gross Revenue Churn Rate of {churn_val}%** alongside a **Net Revenue Retention (NRR) score of {nrr_val}%**. 
    In modern B2B SaaS software environments, institutional stability requires Gross Churn to remain under 5-7%. Our current value indicates an immediate breakdown in user adoption or structural technical friction that requires active operational remediation.
    """)
    
    # Section 2
    st.subheader("2. Verticals Analysis & Risk Concentration")
    df_concentration = run_query("""
        SELECT c.industry, 
               SUM(s.mrr) as industry_mrr,
               ROUND(SUM(s.mrr) * 100.0 / (SELECT SUM(mrr) FROM subscriptions WHERE contract_status = 'Active'), 2) as revenue_share
        FROM companies c 
        JOIN subscriptions s ON c.company_id = s.company_id 
        WHERE s.contract_status = 'Active' 
        GROUP BY c.industry 
        ORDER BY industry_mrr DESC;
    """)
    
    top_industry = df_concentration.iloc[0]['industry']
    top_share = df_concentration.iloc[0]['revenue_share']
    
    st.markdown(f"""
    An assessment of active contract records isolates a heavy vulnerability toward specific structural segments. 
    Our primary anchor is the **{top_industry} vertical**, which commands a dominant **{top_share}% of total active corporate ARR**.
    
    **Strategic Threat Assessment:** Because our financial stability relies heavily on a single vertical, any market slowdown or shared technical issue within the {top_industry} space will cause severe, asymmetric damage to our broader ARR run-rate. Diversification strategies must be introduced immediately across under-represented tiers.
    """)
    
    # Section 3
    st.subheader("3. Operational Revenue Leakage Matrix")
    st.markdown(f"""
    By applying an analytical `LAG()` window partition across monthly user logs, the analytics engine bypassed traditional contract markers and isolated hidden revenue risk. 
    The system caught **{critical_logos} high-paying active corporate logos** exhibiting severe user engagement and API call drop-offs within the last 30-day tracking window.
    """)
    
    # Display the top at-risk accounts in a table inside the report
    st.table(critical_df[['company_name', 'industry', 'plan_tier', 'mrr', 'user_change_pct', 'api_change_pct', 'tickets', 'churn_risk_score']].head(5))
    
    # Section 4
    st.subheader("4. Technical Root-Cause & Business Impact")
    st.markdown(f"""
    In enterprise subscription software, **user activity drops are a direct leading indicator of client termination.** Accounts do not churn out of nowhere; they stop logging into the platform first. 
    
    Because these accounts are currently marked as "Active" in the billing system, traditional accounting models entirely overlook this risk. However, their sharp activity drop suggests these companies have stopped using our services and are actively testing alternatives.
    
    **The Business Impact Summary:** Left unmitigated, this operational drift exposes **${exposed_mrr:,.2f} in Monthly Recurring Revenue**. If these accounts lapse, it will hit our next quarterly baseline with an immediate loss of **${exposed_arr:,.2f} in total ARR**.
    """)
    
    # Section 5
    st.subheader("5. Data-Driven Strategic Recommendations")
    st.markdown("""
    To stabilize our revenue base, executive leadership should immediately act on this three-part remediation strategy:
    
    * **Deploy Immediate Customer Success Interventions:** Mobilize dedicated account managers to open priority lines of communication directly with product stakeholders at the highest-risk accounts within 48 hours. This usage drop must be addressed with the urgency of a system outage.
    * **Review Recent Technical Deployments:** Since the probabilistic data engine caught overlapping failures across usage logs, product teams must audit recent software and API gateway updates to verify that a bug didn't accidentally block user client tokens.
    * **Automate Real-Time System Triggers:** Migrate our SQL window lookback parameters into active database webhooks. Account executives should receive an automated notification the exact moment a client's usage falls below a 20% margin, replacing retro-active monthly reviews with real-time churn defense.
    """)