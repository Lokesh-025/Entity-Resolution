import pandas as pd
import sqlite3

def decide_matches():
    conn = sqlite3.connect("database/entity_resolution.db")

    df = pd.read_sql("SELECT * FROM similarity_scores", conn)

    def classify(score):
        if score >= 85:
            return "AUTO_MERGE"
        elif score >= 70:
            return "HUMAN_REVIEW"
        else:
            return "REJECT"

    df["decision"] = df["final_score"].apply(classify)

    df.to_sql(
        "match_decisions",
        conn,
        if_exists="replace",
        index=False
    )

    conn.close()

    print("Match decision completed successfully")
    print(df)

if __name__ == "__main__":
    decide_matches()