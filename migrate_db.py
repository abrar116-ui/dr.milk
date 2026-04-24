import sqlite3
import os

def migrate():
    db_path = 'instance/drmilk.db' if os.path.exists('instance/drmilk.db') else 'drmilk.db'
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute('ALTER TABLE "order" ADD COLUMN is_subscription BOOLEAN DEFAULT 0')
    except Exception as e:
        print("is_subscription column already exists or error:", str(e))
        
    try:
        c.execute('ALTER TABLE "order" ADD COLUMN subscription_end DATETIME')
    except Exception as e:
        print("subscription_end column already exists or error:", str(e))
        
    conn.commit()
    conn.close()
    print("Database migration completed.")

if __name__ == '__main__':
    migrate()
