import streamlit as st
import pandas as pd
from scraper.core import UNIVERSAL_PRODUCT_RULES


def render_sidebar():
    st.markdown(
        """
        <style>
            .css-1lcbmhc.e1fqkh3o0 {
                width: 300px !important;  /* Fixed sidebar width */
            }
            .css-1lcbmhc.e1fqkh3o0 .stTextInput,
            .css-1lcbmhc.e1fqkh3o0 .stCheckbox,
            .css-1lcbmhc.e1fqkh3o0 .stSelectbox,
            .css-1lcbmhc.e1fqkh3o0 .stButton {
                width: 100% !important;  /* Inputs fill the sidebar width */
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.sidebar:
        st.header("⚙️ Settings")
        url = st.text_input(
            "Page URL",
            value="https://scrapeme.live/shop/",
            help="Enter the URL of the page to scrape",
        )

        use_hasdata = st.checkbox("Use HasData API", value=False)
        api_key = None
        scrape_config = {}

        if use_hasdata:
            st.markdown("---")
            st.subheader("🔑 HasData API")
            api_key = st.text_input(
                "API Key",
                type="password",
                help="Your HasData API key",
            )

            with st.expander("🛠️ Scraping Options", expanded=False):
                scrape_config["jsRendering"] = st.checkbox("JS Rendering", value=True)
                scrape_config["screenshot"] = st.checkbox(
                    "Take Screenshot", value=False
                )
                scrape_config["extractEmails"] = st.checkbox(
                    "Extract Emails", value=False
                )
                scrape_config["extractLinks"] = st.checkbox(
                    "Extract Links", value=False
                )

                use_universal_ai = st.checkbox(
                    "Use AI product extraction",
                    value=False,
                    help="Send universal product schema as aiExtractRules",
                )

                
                scrape_config["blockResources"] = st.checkbox(
                    "Block Resources", value=True
                )
                scrape_config["blockAds"] = st.checkbox("Block Ads", value=True)
                
                scrape_config["proxyType"] = st.selectbox(
                    "Proxy Type",
                    ["datacenter", "residential", "mobile"],
                    index=0,
                )
                scrape_config["proxyCountry"] = st.text_input(
                    "Proxy Country", value="US"
                )

                if use_universal_ai:
                    scrape_config["aiExtractRules"] = UNIVERSAL_PRODUCT_RULES
        else:
            scrape_config = {
                "jsRendering": True,
                "blockResources": True,
                "blockAds": True,
            }


        st.markdown("---")
        force_generic = st.checkbox(
            "Use generic method",
            value=False,
            help="Disable platform auto-detection",
        )

        scrape_button = st.button(
            "Start Scraping", type="primary", width='stretch'
        )

    return {
        "url": url,
        "use_hasdata": use_hasdata,
        "api_key": api_key,
        "scrape_config": scrape_config,
        "force_generic": force_generic,
        "scrape_button": scrape_button,
    }


def render_results(scraper, result, force_generic):
    hasdata_extras = scraper.get_hasdata_extras()
    if hasdata_extras:
        _render_hasdata_extras(hasdata_extras)

    platform_emoji = {
        "woocommerce": "🛒",
        "shopify": "🛍️",
        "generic": "🌐",
    }
    platform_name = {
        "woocommerce": "WooCommerce",
        "shopify": "Shopify",
        "generic": "Generic",
    }

    platform = result.get("platform", "generic")
    st.success(
        f"{platform_emoji[platform]} Detected platform: **{platform_name[platform]}**"
    )

    df = None

    if platform in ["woocommerce", "shopify"] and not force_generic:
        if result["data"]:
            try:
                st.success(f"✅ Extracted {result['count']} items")
            except Exception as e:
                count = len(result["data"])
                st.success(f"✅ Extracted {count} items")
            df = pd.DataFrame(result["data"])
            st.subheader("📊 Data")
            st.dataframe(df, width='stretch', height=400)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows", len(df))
            with col2:
                st.metric("Columns", len(df.columns))
            with col3:
                st.metric("Platform", platform_name[platform])
    else:
        st.success(f"✅ Found {len(result['candidates'])} container groups")
        st.subheader("📦 Select container group")

        options = []
        for i, candidate in enumerate(result["candidates"][:10]):
            tag = candidate["signature"].split(".")[0]
            classes = ".".join(candidate["signature"].split(".")[1:3])
            if len(classes) > 40:
                classes = classes[:40] + "..."
            label = (
                f"{i+1}. <{tag} class='{classes}'> × "
                f"{candidate['count']} (score: {candidate['score']})"
            )
            options.append(label)

        selected_option = st.selectbox(
            "Group",
            options,
            index=result["selected_index"],
            help="Select element group to extract data from",
        )
        selected_index = options.index(selected_option)

        if selected_index != result["selected_index"]:
            with st.spinner("⚙️ Extracting data..."):
                new_result = scraper.scrape(
                    container_index=selected_index,
                    force_generic=force_generic,
                )
                st.session_state["result"] = new_result

        if result["data"]:
            st.subheader(f"📊 Extracted {len(result['data'])} records")
            df = pd.DataFrame(result["data"])
            st.dataframe(df, width='stretch', height=400)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows", len(df))
            with col2:
                st.metric("Columns", len(df.columns))
            with col3:
                st.metric("Container", result["selected"]["signature"].split(".")[0])
        else:
            st.warning("⚠️ Could not extract data from selected group")

    return df


def _render_hasdata_extras(extras):
    tabs = []
    tab_content = {}

    if extras.get("aiResponse"):
        tabs.append("🤖 AI Response")
        tab_content["ai"] = extras["aiResponse"]
    if extras.get("screenshot"):
        tabs.append("📸 Screenshot")
        tab_content["screenshot"] = extras["screenshot"]
    if extras.get("emails"):
        tabs.append("📧 Emails")
        tab_content["emails"] = extras["emails"]
    if extras.get("links"):
        tabs.append("🔗 Links")
        tab_content["links"] = extras["links"]

    if not tabs:
        return

    with st.expander("🎁 HasData Extras", expanded=True):
        tab_objects = st.tabs(tabs)
        for idx, tab_name in enumerate(tabs):
            with tab_objects[idx]:
                if tab_name == "🤖 AI Response":
                    products_data = tab_content.get("ai", {}).get("products", [])

                    if isinstance(products_data, list) and len(products_data) > 0 and all(isinstance(item, dict) for item in products_data):
                        df_products = pd.DataFrame(products_data)
                        df_products = df_products.fillna("N/A").replace("", "N/A")

                        columns_order = [
                            "name", "price", "originalPrice", "currency", "availability",
                            "rating", "reviewCount", "url", "image", "brand",
                            "category", "description", "sku"
                        ]
                        columns_order = [col for col in columns_order if col in df_products.columns]
                        df_products = df_products[columns_order]

                        st.write(f"Found {len(df_products)} products")
                        st.dataframe(df_products, width='stretch', height=300)
                    else:
                        st.warning("No valid product data found in tab_content['ai']['products']")
                        st.json(tab_content)  


                elif tab_name == "📸 Screenshot":
                    st.image(
                        tab_content["screenshot"],
                        caption="Page Screenshot",
                        width='stretch',
                    )
                elif tab_name == "📧 Emails":
                    st.write("Found emails:")
                    for email in tab_content["emails"]:
                        st.code(email)
                elif tab_name == "🔗 Links":
                    st.write(f"Found {len(tab_content['links'])} links")
                
                    df_links = pd.DataFrame({"Link": tab_content["links"]})
                    st.dataframe(df_links, width='stretch', height=300)


def render_info_block():
    st.info("👈 Enter a URL in the sidebar and click 'Start Scraping'")
    st.markdown("---")
    st.markdown("### 🎯 How it works:")
    st.markdown(
        """
1. **Finds repeating containers** - automatically identifies product cards or list items on category pages
2. **Extracts data** - gets text, links, images from each container  
3. **Groups fields** - groups similar fields  
"""
    )
    st.markdown("### 📝 Example sites:")
    st.markdown("**WooCommerce:**")
    st.code("https://scrapeme.live/shop/")
    st.markdown("**Book store:**")
    st.code("https://books.toscrape.com")
    st.markdown("**Real store:**")
    st.code("https://www.vinted.com/catalog/32-costumes-et-blazers")
