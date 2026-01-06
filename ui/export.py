import streamlit as st
import pandas as pd
from io import BytesIO


def render_export_block(df: pd.DataFrame):
    st.subheader("💾 Export Data")
    col1, col2, col3 = st.columns(3)

    with col1:
        csv = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="scraped_data.csv",
            mime="text/csv",
            width='stretch',
        )

    with col2:
        json_data = df.to_json(orient="records", force_ascii=False, indent=2)
        st.download_button(
            label="📥 Download JSON",
            data=json_data,
            file_name="scraped_data.json",
            mime="application/json",
            width='stretch',
        )

    with col3:
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Data")
        excel_data = output.getvalue()
        st.download_button(
            label="📥 Download Excel",
            data=excel_data,
            file_name="scraped_data.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            width='stretch',
        )
