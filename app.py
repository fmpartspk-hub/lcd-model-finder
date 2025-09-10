import streamlit as st
import pandas as pd
import re

# Normalize text (lowercase, remove special chars)
def normalize_text(s):
    if pd.isna(s):
        return ''
    s = str(s).lower()
    s = re.sub('[^a-z0-9]+', ' ', s)
    return s.strip()

# Search function
def search_model(df, model_col, compat_col, query, split=True):
    df = df.copy()
    df['_compat_norm'] = df[compat_col].apply(normalize_text)
    qnorm = normalize_text(query)

    mask1 = df[compat_col].astype(str).str.contains(query, case=False, na=False)
    mask2 = df['_compat_norm'].str.contains(qnorm, na=False)
    results = df[mask1 | mask2].copy()

    if split:
        sep_regex = r'[,|;/]+'
        df_exploded = df.assign(_temp=df[compat_col].astype(str).str.split(sep_regex)).explode('_temp')
        df_exploded['_temp_norm'] = df_exploded['_temp'].apply(normalize_text)
        mask3 = (
            df_exploded['_temp'].str.contains(query, case=False, na=False)
            | df_exploded['_temp_norm'].str.contains(qnorm, na=False)
        )
        if mask3.any():
            results2 = df_exploded[mask3][[model_col, compat_col]].drop_duplicates()
            results = pd.concat([results, results2]).drop_duplicates().reset_index(drop=True)

    return results[[model_col, compat_col]].reset_index(drop=True)

# Streamlit app (loads fixed file from data/final.xlsx inside repo)
def main():
    st.set_page_config(page_title="LCD Model Finder", layout="wide")
    st.title("📱 LCD Model Compatibility Finder (Hosted)")

    # The app expects your Excel file at data/final.xlsx inside the repo.
    DATA_PATH = "data/final.xlsx"

    try:
        df = pd.read_excel(DATA_PATH, sheet_name=0)
    except Exception as e:
        st.error(f"Failed to read Excel file at '{DATA_PATH}': {e}")
        st.markdown("**How to fix:** Place your Excel file inside the repository under `data/final.xlsx` and redeploy.")
        return

    df.columns = df.columns.str.strip().str.lower().str.split().str.join(' ')
    st.write("**Detected columns:**", list(df.columns))

    compat_candidates = [c for c in df.columns if 'compat' in c or 'compatible' in c]
    model_candidates = [c for c in df.columns if 'model' in c and c not in compat_candidates]

    compat_col = compat_candidates[0] if compat_candidates else st.selectbox("Choose compatible column", options=list(df.columns))
    model_col = model_candidates[0] if model_candidates else st.selectbox("Choose model column", options=list(df.columns))

    st.write("Sample rows:")
    st.dataframe(df[[model_col, compat_col]].head(10))

    query = st.text_input("🔍 Search a compatible model")
    split_checkbox = st.checkbox("Split compatible models by separators (comma | ; / )", value=True)

    if st.button("Search") or query:
        if not query:
            st.warning("Please type something to search.")
        else:
            results = search_model(df, model_col, compat_col, query, split=split_checkbox)
            if results.empty:
                st.warning("No match found.")
            else:
                st.write(f"### ✅ {len(results)} match(es):")
                st.dataframe(results)

if __name__ == "__main__":
    main()
