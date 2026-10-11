import pandas as pd
import sqlite3


def build_clusters(pairs):
    parent = {}

    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        rx = find(x)
        ry = find(y)
        if rx != ry:
            parent[ry] = rx

    for a, b in pairs:
        if a not in parent:
            parent[a] = a
        if b not in parent:
            parent[b] = b

    for a, b in pairs:
        union(a, b)

    clusters = {}
    for node in parent:
        root = find(node)
        clusters.setdefault(root, []).append(node)

    return list(clusters.values())


def choose_best(values, column_name=None):
    values = [str(v).strip() for v in values if pd.notna(v)]

    if not values:
        return None

    # Special rule for names
    if column_name and "name" in column_name.lower():
        best = max(values, key=len)

        # Capitalize properly
        best = " ".join(word.capitalize() for word in best.split())

        return best

    # Other columns
    return max(values, key=len)


def create_golden_records():
    conn = sqlite3.connect("database/entity_resolution.db")

    raw_df = pd.read_sql("SELECT * FROM raw_records", conn)

    decisions_df = pd.read_sql("""
        SELECT * FROM match_decisions
        WHERE decision = 'AUTO_MERGE'
    """, conn)

    pairs = list(zip(
        decisions_df["record_id_1"],
        decisions_df["record_id_2"]
    ))

    clusters = build_clusters(pairs)

    golden_records = []
    used_ids = set()

    # HANDLE DUPLICATE CLUSTERS
    for idx, cluster in enumerate(clusters, start=1):
        cluster_df = raw_df[raw_df["id"].isin(cluster)]

        used_ids.update(cluster)

        golden_records.append({
            "golden_id": idx,
            "canonical_name": choose_best(cluster_df["name"], "name"),
            "canonical_email": choose_best(cluster_df["email"], "email"),
            "canonical_phone": choose_best(cluster_df["phone"], "phone"),
            "canonical_address": choose_best(cluster_df["address"], "address")
        })

    # HANDLE UNIQUE NON-DUPLICATE RECORDS
    unique_df = raw_df[~raw_df["id"].isin(used_ids)]

    start_idx = len(golden_records) + 1

    for i, (_, row) in enumerate(unique_df.iterrows(), start=start_idx):
        golden_records.append({
            "golden_id": i,
            "canonical_name": choose_best([row["name"]], "name"),
            "canonical_email": choose_best([row["email"]], "email"),
            "canonical_phone": choose_best([row["phone"]], "phone"),
            "canonical_address": choose_best([row["address"]], "address")
        })

    golden_df = pd.DataFrame(golden_records)

    golden_df.to_sql(
        "golden_records",
        conn,
        if_exists="replace",
        index=False
    )

    conn.close()