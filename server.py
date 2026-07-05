from fastapi import FastAPI
import sqlite3
import pandas as pd
import numpy as np
import requests
import os

app = FastAPI()

# Google Drive の numeric.db ダウンロードURL
DB_URL = "https://drive.google.com/uc?export=download&id=1mX5vU8AKBesWTd8G6tHalfaPIQAQddHp"

# Google Drive から numeric.db を取得して /tmp に保存
def download_db():
    local_path = "/tmp/numeric.db"

    # すでに存在する場合は削除（毎回最新を取得するため）
    if os.path.exists(local_path):
        os.remove(local_path)

    r = requests.get(DB_URL)
    with open(local_path, "wb") as f:
        f.write(r.content)

    return local_path


# ================================
# 企業の財務データ（最新5年分）
# ================================
@app.get("/company_history")
def get_company_history(company: str):
    db_local = download_db()
    conn = sqlite3.connect(db_local)
    df = pd.read_sql_query("SELECT * FROM numeric_data", conn)
    conn.close()

    def normalize(text):
        if text is None:
            return ""
        text = str(text)
        replace_words = ["株式会社", "（株）", "(株)", "㈱", "　", " ", "\n", "\t"]
        for w in replace_words:
            text = text.replace(w, "")
        return text.strip()

    df["company_norm"] = df["company"].apply(normalize)
    company_norm = normalize(company)

    df_match = df[df["company_norm"].str.contains(company_norm)]

    if df_match.empty:
        return {"message": f"{company} はEDINET提出企業ではありません。"}

    df_match = df_match.sort_values("date", ascending=False).head(5)

    return df_match.to_dict(orient="records")


# ================================
# 指標の重み付けランキング（欠損企業除外）
# ================================
@app.get("/rank_weighted")
def rank_weighted(metrics: str, weights: str, top_n: int = 10):
    db_local = download_db()
    conn = sqlite3.connect(db_local)
    df = pd.read_sql_query("SELECT * FROM numeric_data", conn)
    conn.close()

    df["year"] = df["date"].str[:4].astype(int)
    df = df[df["year"].isin([2026, 2025])]

    df = df.sort_values("date", ascending=False)
    df = df.drop_duplicates(subset=["company"], keep="first")

    metric_list = [m.strip() for m in metrics.split(",")]
    weight_list = [float(w) for w in weights.split(",")]

    if len(metric_list) != len(weight_list):
        return {"error": "metrics と weights の数が一致していません"}

    for m in metric_list:
        df[m] = pd.to_numeric(df[m], errors="coerce")

    df = df.dropna(subset=metric_list)

    df["score"] = 0
    for m, w in zip(metric_list, weight_list):
        df["score"] += df[m] * w

    df_rank = df.sort_values("score", ascending=False).head(top_n)

    df_rank = df_rank.replace([np.nan, None], 0)

    return df_rank.to_dict(orient="records")
