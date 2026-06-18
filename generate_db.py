import sqlite3
import random
import os
from datetime import datetime, timedelta

def build_enterprise_database():
    # Dynamic path handling
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "saas_revenue.db")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. CREATE SYSTEM TABLES WITH MULTI-RUN SAFETY CHECKS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        company_id INTEGER PRIMARY KEY,
        company_name TEXT NOT NULL,
        industry TEXT NOT NULL,
        account_created DATE NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        subscription_id INTEGER PRIMARY KEY,
        company_id INTEGER NOT NULL,
        plan_tier TEXT NOT NULL,
        monthly_recurring_revenue REAL NOT NULL,
        contract_status TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES companies(company_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usage_logs (
        log_id INTEGER PRIMARY KEY,
        company_id INTEGER NOT NULL,
        log_date DATE NOT NULL,
        active_users_count INTEGER NOT NULL,
        api_call_volume INTEGER NOT NULL,
        FOREIGN KEY (company_id) REFERENCES companies(company_id)
    );
    """)

    # Only seed records if the database tables are fresh and empty
    cursor.execute("SELECT COUNT(*) FROM companies;")
    if cursor.fetchone()[0] == 0:
        # 2. SEED SYNTHETIC CORPORATE RECORDS
        industries = ["Fintech", "Healthcare Logistics", "Cybersecurity", "E-Commerce Infrastructure", "Automotive Tech"]
        tiers = [("Growth", 1200.00), ("Scale", 3500.00), ("Enterprise", 8500.00)]
        
        for i in range(1, 51):
            comp_name = f"AlphaCorp {i:02d} LLC"
            ind = random.choice(industries)
            creation_date = (datetime.now() - timedelta(days=random.randint(180, 500))).date()
            
            cursor.execute("INSERT INTO companies (company_name, industry, account_created) VALUES (?, ?, ?)", 
                           (comp_name, ind, creation_date))
            
            # This is the verified ID variable name
            comp_id = cursor.lastrowid
            
            tier, price = random.choice(tiers)
            status = "Active" if random.random() > 0.15 else "Churned"
            cursor.execute("INSERT INTO subscriptions (company_id, plan_tier, monthly_recurring_revenue, contract_status) VALUES (?, ?, ?, ?)",
                           (comp_id, tier, price, status))
            
            base_users = random.randint(10, 150)
            base_api = base_users * random.randint(100, 300)
            is_leaking_account = (i % 7 == 0 and status == "Active")

            for month_offset in [2, 1, 0]:
                log_date = (datetime.now() - timedelta(days=month_offset * 30)).date()
                
                if is_leaking_account and month_offset == 0:
                    users = int(base_users * 0.3)
                    api = int(base_api * 0.25)
                else:
                    users = int(base_users * random.uniform(0.9, 1.1))
                    api = int(base_api * random.uniform(0.85, 1.15))
                    
                # FIX: Swapped company_id to the active loop variable comp_id
                cursor.execute("INSERT INTO usage_logs (company_id, log_date, active_users_count, api_call_volume) VALUES (?, ?, ?, ?)",
                               (comp_id, log_date, users, api))
        print("New relational data records seeded successfully.")
    else:
        print("Existing database detected. Skipping seed layer to prevent duplication.")

    conn.commit()
    conn.close()
    print(f"Database verified seamlessly at: {db_path}")

if __name__ == "__main__":
    build_enterprise_database()