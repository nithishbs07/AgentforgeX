import os
import sys
import json
import csv
import sqlite3
from datetime import datetime

# Add parent directory to path to locate config/db path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

try:
    from app.core.config import settings
    # Parse DB Path
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite:///"):
        DB_PATH = db_url.replace("sqlite:///", "")
    else:
        DB_PATH = "./agentforge.db"
except Exception:
    DB_PATH = "./agentforge.db"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_abs_path = os.path.abspath(os.path.join(PROJECT_ROOT, DB_PATH))
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

def export_db_logs():
    print("=== Exporting Evaluation Logs from SQLite ===")
    if not os.path.exists(db_abs_path):
        print(f"Warning: Database file not found at {db_abs_path}. Skipping database export.")
        return

    try:
        conn = sqlite3.connect(db_abs_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evaluation_logs ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        
        # Convert sqlite rows to list of dicts
        data = []
        for r in rows:
            data.append(dict(r))
        conn.close()
        
        if not data:
            print("No logs found in evaluation_logs table.")
            return

        # 1. Export JSON
        json_path = os.path.join(RESULTS_DIR, "evaluation_logs_export.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"Exported evaluation logs to JSON: {json_path}")
        
        # 2. Export CSV
        csv_path = os.path.join(RESULTS_DIR, "evaluation_logs_export.csv")
        headers = list(data[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        print(f"Exported evaluation logs to CSV: {csv_path}")
        
    except Exception as e:
        print(f"Error exporting database logs: {e}")

def run_export():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    export_db_logs()
    
    print("\n=== Research Results Export Complete ===")

if __name__ == "__main__":
    run_export()
