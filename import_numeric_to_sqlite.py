import pandas as pd
import sqlite3
import glob
import os

# === numeric_split の場所 ===
INPUT_DIR = r"C:\Users\takeh\OneDrive\デスクトップ\numeric_split"

# === 出力する SQLite の場所（corp-analytics-api 内） ===
DB_PATH = r"C:\Users\takeh\OneDrive\デスクトップ\corp-analytics-api\numeric.db"

# === SQLite 接続 ===
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# === テーブル作成 ===
cursor.execute("""
CREATE TABLE IF NOT EXISTS numeric_data (
    doc_id TEXT,
    company TEXT,
    date TEXT,
    sales REAL,
    operating_income REAL,
    profit REAL,
    operating_income_per_employee REAL,
    equity_ratio REAL,
    current_ratio REAL,
    cash_and_equivalents REAL,
    roe REAL,
    roa REAL,
    employees REAL
)
""")
conn.commit()

# === numeric_split の CSV を全部読み込む ===
files = glob.glob(os.path.join(INPUT_DIR, "*.csv"))

for file in files:
    print(f"📥 Loading {file} ...")
    df = pd.read_csv(file)
    df.to_sql("numeric_data", conn, if_exists="append", index=False)
    print(f"✔ Imported {len(df)} rows")

conn.close()
print("🎉 完了：numeric.db を作成しました！")
