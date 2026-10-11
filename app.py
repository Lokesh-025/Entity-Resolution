import streamlit as st
import pandas as pd
import sqlite3

from src.feedback import save_feedback
from src.preprocessing import preprocess_data
from src.blocking import generate_candidates
from src.similarity import calculate_similarity
from src.matcher import decide_matches
from src.golden_record import create_golden_records


# ==========================
# SMART COLUMN STANDARDIZATION
# ==========================
def standardize_columns(df):
    standardized_df = pd.DataFrame()

    # Build full name from first + last name if available
    cols_lower = [c.lower().strip().replace(" ", "_") for c in df.columns]

    first_name_col = None
    last_name_col = None

    for col in df.columns:
        c = col.lower().strip().replace(" ", "_")

        if "first_name" in c:
            first_name_col = col

        elif "last_name" in c:
            last_name_col = col

    # Create full name first
    if first_name_col and last_name_col:
        standardized_df["name"] = (
            df[first_name_col].astype(str).str.strip() + " " +
            df[last_name_col].astype(str).str.strip()
        )

    else:
        # fallback only for real name columns
        for col in df.columns:
            c = col.lower().strip().replace(" ", "_")

            if c in ["name", "full_name", "customer_name", "person_name"]:
                standardized_df["name"] = df[col]
                break

    # EMAIL
    for col in df.columns:
        c = col.lower().strip().replace(" ", "_")
        if "email" in c or "mail" in c:
            standardized_df["email"] = df[col]
            break

    # PHONE
    for col in df.columns:
        c = col.lower().strip().replace(" ", "_")
        if "phone" in c or "mobile" in c:
            standardized_df["phone"] = df[col]
            break

    # ADDRESS
    for col in df.columns:
        c = col.lower().strip().replace(" ", "_")
        if "city" in c or "address" in c or "location" in c:
            standardized_df["address"] = df[col]
            break

    # keep remaining columns
    for col in df.columns:
        if col not in standardized_df.columns:
            standardized_df[col] = df[col]

    return standardized_df


# ==========================
# STREAMLIT CONFIG
# ==========================
st.set_page_config(
    page_title="Entity Resolution Dashboard",
    layout="wide"
)

st.title("Entity Resolution Engine Dashboard")


# ==========================
# SIDEBAR
# ==========================
st.sidebar.title("Navigation")

section = st.sidebar.radio(
    "Go to",
    [
        "Upload & Process",
        "Dashboard",
        "Duplicates",
        "Golden Records",
        "Human Review"
        
    ]
)


# ==========================
# DATABASE
# ==========================
conn = sqlite3.connect("database/entity_resolution.db")

# ===========================
# DASHBOARD
# ===========================

if section == "Dashboard":
    st.header("Entity Resolution Analytics Dashboard")

    raw_df = pd.read_sql("SELECT * FROM raw_records", conn)
    match_df = pd.read_sql("SELECT * FROM match_decisions", conn)
    duplicate_df = pd.read_sql("SELECT * FROM match_decisions", conn)
    golden_df = pd.read_sql("SELECT * FROM golden_records", conn)

    review_df = duplicate_df[
        duplicate_df["decision"] == "HUMAN_REVIEW"
    ]

    auto_merge_df = duplicate_df[
        duplicate_df["decision"] == "AUTO_MERGE"
    ]

    total_records = len(raw_df)

    duplicate_records = len(
        set(auto_merge_df["record_id_1"]).union(
            set(auto_merge_df["record_id_2"])
        )
    )

    golden_records = len(golden_df)

    human_review = len(review_df)

    duplicate_percentage = round(
        (duplicate_records / total_records) * 100, 2
    )

    golden_percentage = round(
        (golden_records / total_records) * 100, 2
    )

    review_percentage = round(
        (human_review / total_records) * 100, 2
    )

    col1, col2, col3, col4 ,col5= st.columns(5)

    with col1:
        st.metric(
            "📁 Total Records",
            total_records
        )

    with col2:
        st.metric(
            "🔁 Duplicate Unique Records",
            duplicate_records,
            f"{duplicate_percentage}%"
        )
        
    with col3:
     st.metric(
        "🔗 Candidate Pairs",
        len(match_df)
    )

    with col4:
        st.metric(
            "🟢 Golden Records",
            golden_records,
            f"{golden_percentage}%"
        )

    with col5:
        st.metric(
            "👤 Human Review",
            human_review,
            f"{review_percentage}%"
        )

    st.markdown("---")

    st.subheader("Resolution Summary")

    summary_df = pd.DataFrame({
        "Category": [
            "Total Records",
            "Duplicate Records",
            "Golden Records",
            "Human Review"
        ],
        "Count": [
            total_records,
            duplicate_records,
            golden_records,
            human_review
        ]
    })

    st.bar_chart(
        summary_df.set_index("Category")
    )

    st.subheader("System Insights")

    st.info(
        f"""
        Total uploaded records: {total_records}
        
        Duplicate records detected: {duplicate_records}
        
        Final golden records generated: {golden_records}
        
        Records pending human review: {human_review}
        """
    )
# ==========================
# UPLOAD + PROCESS
# ==========================
if section == "Upload & Process":
    st.header("Upload Multiple Source Files")

    uploaded_files = st.file_uploader(
        "Upload CSV / Excel files",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True
    )

    if uploaded_files:
        all_dfs = []

        st.subheader("Uploaded Sources")

        for file in uploaded_files:
            file_name = file.name.lower()

            # Read file
            if file_name.endswith(".csv"):
                df = pd.read_csv(file)

            elif file_name.endswith(".xlsx") or file_name.endswith(".xls"):
                df = pd.read_excel(file)

            else:
                st.error(f"Unsupported file: {file.name}")
                continue

            # Standardize columns
            df = standardize_columns(df)

            # Add source metadata
            df["source_system"] = file.name

            st.write(f"Source: {file.name}")
            st.dataframe(df.head())

            all_dfs.append(df)

        if all_dfs:
            merged_df = pd.concat(all_dfs, ignore_index=True)

            required_cols = ["name", "email", "phone", "address"]

            missing_cols = [
                col for col in required_cols
                if col not in merged_df.columns
            ]

            if missing_cols:
                st.error(f"Missing required columns: {missing_cols}")
                st.stop()

            st.subheader("Unified Multi-Source Dataset")
            st.dataframe(merged_df)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Sources", len(uploaded_files))

            with col2:
                st.metric("Total Records", len(merged_df))

            with col3:
                st.metric("Columns", len(merged_df.columns))

            if st.button("Run Entity Resolution Pipeline"):
                merged_df.insert(
                    0,
                    "id",
                    range(1, len(merged_df) + 1)
                )

                merged_df.to_sql(
                    "raw_records",
                    conn,
                    if_exists="replace",
                    index=False
                )

                conn.close()

                preprocess_data()
                generate_candidates()
                calculate_similarity()
                decide_matches()
                create_golden_records()

                st.success("Pipeline completed successfully")
                st.rerun()


# ==========================
# DUPLICATES
# ==========================
elif section == "Duplicates":
    st.header("Duplicate Candidate Records")

    df = pd.read_sql("SELECT * FROM match_decisions", conn)

    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Duplicates CSV",
        csv,
        "duplicates.csv",
        "text/csv"
    )


# ==========================
# GOLDEN RECORDS
# ==========================
elif section == "Golden Records":
    st.header("Golden Records")

    df = pd.read_sql("SELECT * FROM golden_records", conn)

    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Golden Records CSV",
        csv,
        "golden_records.csv",
        "text/csv"
    )


# ==========================
# HUMAN REVIEW
# ==========================
elif section == "Human Review":
    st.header("Human Review Queue")

    review_df = pd.read_sql("""
    SELECT * FROM match_decisions
    WHERE decision = 'HUMAN_REVIEW'
    """, conn)

    if review_df.empty:
        st.success("No records pending review")

    else:
        for idx, row in review_df.iterrows():
            st.write(f"### Candidate Pair {idx + 1}")
            st.write(f"Record 1 ID: {row['record_id_1']}")
            st.write(f"Record 2 ID: {row['record_id_2']}")
            st.write(f"Confidence Score: {row['final_score']}")

            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"Approve {idx}"):
                    save_feedback(
                        row["record_id_1"],
                        row["record_id_2"],
                        "APPROVED"
                    )
                    st.success("Approved and golden records updated")
                    st.rerun()

            with col2:
                if st.button(f"Reject {idx}"):
                    save_feedback(
                        row["record_id_1"],
                        row["record_id_2"],
                        "REJECTED"
                    )
                    st.error("Rejected and golden records updated")
                    st.rerun()

conn.close()