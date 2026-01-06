import streamlit as st
import pandas as pd
from scraper.core import AutoScraper
from ui.layout import render_sidebar, render_results, render_info_block
from ui.export import render_export_block


def main():
    st.set_page_config(
        page_title="Auto Web Scraper",
        page_icon="🕷️",
        layout="wide",
    )

    st.title("🕷️ Auto Product List Scraper")
    st.markdown("*Automatically finds and extracts data from web pages*")

    sidebar_state = render_sidebar()
    url = sidebar_state["url"]
    use_hasdata = sidebar_state["use_hasdata"]
    api_key = sidebar_state["api_key"]
    scrape_config = sidebar_state["scrape_config"]
    force_generic = sidebar_state["force_generic"]
    scrape_button = sidebar_state["scrape_button"]

    if scrape_button and url:
        if use_hasdata and not api_key:
            st.error("❌ Please provide HasData API key")
            return

        with st.spinner("🔍 Analyzing page..."):
            try:
                scraper = AutoScraper(url, api_key=api_key, scrape_config=scrape_config)
                result = scraper.scrape(force_generic=force_generic)

                if not result:
                    st.error("❌ Could not find repeating structures on the page")
                    return

                st.session_state["scraper"] = scraper
                st.session_state["result"] = result
                st.session_state["force_generic"] = force_generic
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback

                st.code(traceback.format_exc())
                return

    if "result" in st.session_state:
        scraper = st.session_state["scraper"]
        result = st.session_state["result"]
        force_generic = st.session_state.get("force_generic", False)

        df = render_results(scraper, result, force_generic)
        if df is not None:
            render_export_block(df)
    else:
        render_info_block()


if __name__ == "__main__":
    main()
