import pandas as pd
import sqlite3

def generate_candidates():
    conn = sqlite3.connect("database/entity_resolution.db")

    df = pd.read_sql("SELECT * FROM processed_records", conn)

    # create block key
    df["block_key"] = (
        df["name_clean"].str[0] +
        df["phone_clean"].str[-4:]
    )

    candidate_pairs = []

    for block, group in df.groupby("block_key"):
        records = group.to_dict("records")

        for i in range(len(records)):
            for j in range(i + 1, len(records)):
                candidate_pairs.append({
                    "record_id_1": records[i]["id"],
                    "record_id_2": records[j]["id"],
                    "block_key": block
                })

    candidate_df = pd.DataFrame(candidate_pairs)

    candidate_df.to_sql(
        "candidate_pairs",
        conn,
        if_exists="replace",
        index=False
    )

    conn.close()

    print("Blocking completed successfully")
    print(candidate_df)

if __name__ == "__main__":
    generate_candidates()