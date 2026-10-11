import pandas as pd
import sqlite3

def ingest_csv():
    df = pd.read_csv("../data/sample-records.csv")

    conn = sqlite3.connect("../database/entity_resolution.db")

    df.to_sql("raw_records", conn, if_exists="replace", index=False)

    conn.close()

    print("Data ingested successfully")

if __name__ == "__main__":
    ingest_csv()