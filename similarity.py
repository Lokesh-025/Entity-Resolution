import pandas as pd
import sqlite3
from rapidfuzz import fuzz

def calculate_similarity():
    conn = sqlite3.connect("database/entity_resolution.db")

    records_df = pd.read_sql("SELECT * FROM processed_records", conn)
    candidates_df = pd.read_sql("SELECT * FROM candidate_pairs", conn)

    results = []

    for _, pair in candidates_df.iterrows():
        record1 = records_df[records_df["id"] == pair["record_id_1"]].iloc[0]
        record2 = records_df[records_df["id"] == pair["record_id_2"]].iloc[0]


        name1 = str(record1["name_clean"])
        name2 = str(record2["name_clean"])

        name_score = max(
         fuzz.ratio(name1, name2),
         fuzz.partial_ratio(name1, name2),
    fuzz.token_sort_ratio(name1, name2)
          )

        email_score = fuzz.ratio(
            record1["email_clean"],
            record2["email_clean"]
        )

        phone_score = 100 if (
            record1["phone_clean"] == record2["phone_clean"]
        ) else 0

        final_score = (
            0.5 * name_score +
            0.3 * email_score +
            0.2 * phone_score
        )

        results.append({
            "record_id_1": pair["record_id_1"],
            "record_id_2": pair["record_id_2"],
            "name_score": name_score,
            "email_score": email_score,
            "phone_score": phone_score,
            "final_score": round(final_score, 2)
        })

    result_df = pd.DataFrame(results)

    result_df.to_sql(
        "similarity_scores",
        conn,
        if_exists="replace",
        index=False
    )

    conn.close()

    print("Similarity scoring completed successfully")
    print(result_df)

if __name__ == "__main__":
    calculate_similarity()