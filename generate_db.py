import sqlite3
import random
import os
from datetime import datetime, timedelta

def build_enterprise_database():
    # FIX: seeded so the synthetic dataset (and any screenshots/demos of it)
    # is reproducible run to run instead of changing every time it's rebuilt.
    random.seed(42)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "saas_revenue.db")

    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. ARCHITECT SCHEMAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        company_id INTEGER PRIMARY KEY,
        company_name TEXT NOT NULL,
        industry TEXT NOT NULL,
        account_created TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        subscription_id INTEGER PRIMARY KEY,
        company_id INTEGER NOT NULL,
        plan_tier TEXT NOT NULL,
        mrr REAL NOT NULL,
        contract_status TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES companies(company_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usage_logs (
        log_id INTEGER PRIMARY KEY,
        company_id INTEGER NOT NULL,
        log_date TEXT NOT NULL,
        active_users_count INTEGER NOT NULL,
        api_call_volume INTEGER NOT NULL,
        support_tickets_count INTEGER NOT NULL,
        FOREIGN KEY (company_id) REFERENCES companies(company_id)
    );
    """)

    # 2. SEED STRUCTURAL METADATA
    industries = ["Fintech", "Healthcare Logistics", "Cybersecurity", "E-Commerce Infrastructure", "Automotive Tech"]
    tiers = [("Growth", 1200.00), ("Scale", 3500.00), ("Enterprise", 8500.00)]

    cursor.execute("SELECT COUNT(*) FROM companies;")
    if cursor.fetchone()[0] == 0:
        for i in range(1, 61):
            comp_name = f"AlphaCorp {i:02d} LLC"
            ind = random.choice(industries)

            creation_date = (datetime.now() - timedelta(days=random.randint(200, 450))).date().isoformat()
            cursor.execute("INSERT INTO companies (company_name, industry, account_created) VALUES (?, ?, ?)",
                           (comp_name, ind, creation_date))
            comp_id = cursor.lastrowid

            tier, price = random.choice(tiers)
            status = "Active" if random.random() > 0.15 else "Churned"
            cursor.execute("INSERT INTO subscriptions (company_id, plan_tier, mrr, contract_status) VALUES (?, ?, ?, ?)",
                           (comp_id, tier, price, status))

            base_users = random.randint(30, 200)
            base_api = base_users * random.randint(150, 400)

            risk_profile = "Healthy"
            rand_draw = random.random()
            if status == "Active":
                if rand_draw < 0.08: risk_profile = "Adoption_Failure"
                elif rand_draw < 0.15: risk_profile = "API_Integration_Drop"
                elif rand_draw < 0.22: risk_profile = "Seasonal_Slowdown"
                elif rand_draw < 0.26: risk_profile = "High_Support_Volume"

            for month_offset in range(11, -1, -1):
                log_date = (datetime.now() - timedelta(days=month_offset * 30)).date().isoformat()

                user_mod = random.uniform(0.9, 1.1)
                api_mod = random.uniform(0.85, 1.15)
                tickets = random.randint(0, 3)

                if month_offset <= 1:
                    if risk_profile == "Adoption_Failure":
                        user_mod *= 0.45
                        tickets = random.randint(1, 2)
                    elif risk_profile == "API_Integration_Drop":
                        api_mod *= 0.30
                        tickets = random.randint(4, 8)
                    elif risk_profile == "Seasonal_Slowdown":
                        user_mod *= 0.75
                        api_mod *= 0.75
                    elif risk_profile == "High_Support_Volume":
                        tickets = random.randint(6, 12)

                if status == "Churned" and month_offset <= 3:
                    continue

                final_users = max(int(base_users * user_mod), 1)
                final_api = max(int(base_api * api_mod), 10)

                cursor.execute("""
                INSERT INTO usage_logs (company_id, log_date, active_users_count, api_call_volume, support_tickets_count) 
                VALUES (?, ?, ?, ?, ?)
                """, (comp_id, log_date, final_users, final_api, tickets))

        print("New relational data records seeded successfully.")
    else:
        print("Existing database detected. Skipping seed layer to prevent duplication.")

    conn.commit()
    conn.close()
    print(f"Database verified seamlessly at: {db_path}")

if __name__ == "__main__":
    build_enterprise_database()
