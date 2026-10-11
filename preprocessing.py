import pandas as pd
import sqlite3
import re

def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text).lower().strip()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

def clean_phone(phone):
    if pd.isna(phone):
        return ""
    return re.sub(r'\D', '', str(phone))

def preprocess_data():
    conn = sqlite3.connect("database/entity_resolution.db")

    df = pd.read_sql("SELECT * FROM raw_records", conn)

    print("Columns:", df.columns)

    df["name_clean"] = df["name"].apply(clean_text)
    df["email_clean"] = df["email"].apply(clean_text)
    df["phone_clean"] = df["phone"].apply(clean_phone)
    df["address_clean"] = df["address"].apply(clean_text)

    df.to_sql("processed_records", conn, if_exists="replace", index=False)

    conn.close()

    print("Preprocessing completed successfully")

if __name__ == "__main__":
    preprocess_data()