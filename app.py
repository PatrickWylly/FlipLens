import io
import json
import statistics

import requests
import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

st.set_page_config(page_title="FlipLens | AI Resale Scanner", page_icon="F", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
/* FlipLens: warm cream, dusty rose and plum. */
:root { color-scheme: light; }
.stApp { background-color: #EDE0D7; color: #584B53; }
[data-testid="stHeader"] { background-color: #EDE0D7; }
.block-container { max-width: 1160px; padding-top: 2rem; padding-bottom: 4rem; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp p, .stApp label, .stApp li { color: #584B53; }
h1, h2, h3 { letter-spacing: -0.025em; }
.brand { color: #584B53; font-weight: 800; font-size: 1.35rem; }
.section-heading { color: #584B53; font-weight: 750; font-size: 1.32rem; margin: 8px 0 10px; }
.hero {
    background: #9D5C63;
    border: 1px solid #87505A;
    border-radius: 12px;
    padding: 30px 32px;
    margin: 12px 0 26px;
}
.hero .eyebrow { color: #FEF5EF; font-size: .78rem; letter-spacing: .15em; font-weight: 800; }
.hero .hero-title { color: #FEF5EF; font-size: clamp(2rem,4vw,3.2rem); font-weight: 800; letter-spacing: -.045em; margin: 8px 0; }
.hero .hero-copy { color: #FEF5EF; font-size: 1.02rem; max-width: 640px; }
/* Main cards: warm grey-plum rather than blue. */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: #F4EAE3;
    border-color: #A48D92 !important;
    border-radius: 12px !important;
}
[data-testid="stMetric"] {
    background: #D6C7C8;
    border: 1px solid #A48D92;
    border-radius: 10px;
    padding: 15px 17px;
}
[data-testid="stMetricLabel"] p { color: #584B53 !important; }
[data-testid="stMetricValue"] { color: #584B53 !important; }
/* Accessible primary buttons and eBay links. */
.stButton > button[kind="primary"] {
    background: #584B53 !important;
    border: 1px solid #584B53 !important;
    color: #FEF5EF !important;
    font-weight: 700;
    min-height: 48px;
}
.stButton > button[kind="primary"]:hover { background: #9D5C63 !important; border-color: #9D5C63 !important; }
.stButton > button[kind="primary"] p,
.stButton > button[kind="primary"]:hover p { color: #FEF5EF !important; }
.stLinkButton a { background: #E4BB97 !important; border: 1px solid #9D5C63 !important; color: #584B53 !important; }
.stLinkButton a p { color: #584B53 !important; }
/* Uploader: dark text on a pale background, readable upload control. */
[data-testid="stFileUploader"] {
    background: #F4EAE3 !important;
    border: 1px solid #A48D92;
    border-radius: 10px;
}
[data-testid="stFileUploaderDropzone"] {
    background: #F7F0EB !important;
    border: 1px dashed #9D5C63 !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploaderDropzone"] *,
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploaderDropzone"] p { color: #584B53 !important; }
[data-testid="stFileUploaderDropzone"] button {
    background: #584B53 !important;
    color: #FEF5EF !important;
    border: 1px solid #584B53 !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploaderDropzone"] button * { color: #FEF5EF !important; }
[data-testid="stFileUploaderDropzone"] button:hover { background: #9D5C63 !important; }
/* Explicit notice styling avoids Streamlit theme-dependent dark alerts. */
.fliplens-notice {
    background-color: #E4BB97 !important;
    color: #392E34 !important;
    border: 1px solid #9D5C63;
    border-radius: 10px;
    padding: 16px 18px;
    margin: 12px 0;
    font-weight: 550;
    line-height: 1.5;
}
.fliplens-positive {
    background-color: #F3DED2 !important;
    border-left: 5px solid #9D5C63;
}
/* Alerts: fix Streamlit's dark info box with low-contrast text. */
.stApp [data-testid="stAlert"] {
    background: #E4BB97 !important;
    color: #392E34 !important;
    border: 1px solid #9D5C63 !important;
    border-radius: 10px !important;
}
.stApp [data-testid="stAlert"] *,
.stApp [data-testid="stAlert"] p,
.stApp [data-testid="stAlert"] span { color: #392E34 !important; }
.stApp [data-testid="stCaptionContainer"] p { color: #806E74 !important; }
/* Gentle rounding, including form controls and photos. */
.stApp button, .stApp input, .stApp textarea,
.stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"],
.stApp [data-testid="stNumberInput"] input,
.stApp [data-testid="stImage"] img { border-radius: 8px !important; }
.stApp input { background: #FFFCF9 !important; color: #584B53 !important; }
hr { border-color: #B99CA0 !important; }
a { color: #9D5C63; }
</style>
""", unsafe_allow_html=True)


def get_ebay_access_token():
    response = requests.post(
        "https://api.ebay.com/identity/v1/oauth2/token",
        auth=(st.secrets["EBAY_CLIENT_ID"], st.secrets["EBAY_CLIENT_SECRET"]),
        data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def search_ebay(query):
    token = get_ebay_access_token()
    response = requests.get(
        "https://api.ebay.com/buy/browse/v1/item_summary/search",
        headers={"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"},
        params={"q": query, "limit": 20},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def identify_item(uploaded_file):
    image = Image.open(uploaded_file)
    image.thumbnail((1024, 1024))
    image = image.convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)

    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[
            types.Part.from_bytes(data=buffer.getvalue(), mime_type="image/jpeg"),
            """You are identifying a product for an online resale price search.
Carefully examine the image, including any visible text, logos, labels, and product packaging.
Identify the most specific product possible.
IMPORTANT RULES:
- item_name must be a specific, searchable product name.
- Include the brand and product type in item_name when known.
- Include the model name or number when clearly visible.
- Never use generic names like 'grill', 'camera', or 'shoes' when more specific information is visible.
- If packaging is shown, prioritize the product name printed on the packaging.
- Distinguish an electric cooking grill from an automotive grille.
- Do not invent details that are not supported by the image.
Return item_name, brand, model, category, and condition.
For condition, only describe what is visible in the image.
If a detail cannot be determined, use 'Unknown'.""",
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "item_name": {"type": "STRING"},
                    "brand": {"type": "STRING"},
                    "model": {"type": "STRING"},
                    "category": {"type": "STRING"},
                    "condition": {"type": "STRING"},
                },
                "required": ["item_name", "brand", "model", "category", "condition"],
            },
        ),
    )
    if not response.text:
        raise ValueError("Gemini did not return any information. Please try again.")
    return json.loads(response.text)


def filter_listings(items, item_info):
    excluded_words = ["manual", "instructions", "case only", "box only", "for parts", "repair"]
    brand = item_info.get("brand", "Unknown").lower().strip()
    model = item_info.get("model", "Unknown").lower().strip()
    filtered = []
    for item in items:
        title = item.get("title", "").lower()
        is_excluded = any(word in title for word in excluded_words)
        brand_matches = brand in ("", "unknown") or brand in title
        if not is_excluded and brand_matches:
            filtered.append(item)
    # Exact model matches appear first, without excluding broader brand matches.
    if model not in ("", "unknown"):
        filtered.sort(key=lambda item: model in item.get("title", "").lower(), reverse=True)
    return filtered


st.markdown('<div class="brand">FlipLens <span style="color:#9D5C63;font-weight:500;font-size:.85rem">/ AI Reselling Assistant</span></div>', unsafe_allow_html=True)
st.markdown('''<div class="hero"><div class="eyebrow">AI-POWERED RESALE RESEARCH</div>
<div class="hero-title">Find the profit in anything.</div>
<div class="hero-copy">Upload a photo, identify the item with AI, and explore its potential resale value using real eBay listings.</div></div>''', unsafe_allow_html=True)

left, right = st.columns([1.1, 0.9], gap="large")
with left:
    with st.container(border=True):
        st.markdown('<div class="section-heading">Scan an item</div>', unsafe_allow_html=True)
        st.caption("Start with a clear photo of the item, label, or packaging.")
        uploaded_file = st.file_uploader("Choose a photo", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Your item", use_container_width=True)
        purchase_price = st.number_input("What would you pay for this item? ($)", min_value=0.0, value=0.0, step=1.0, format="%.2f")
        analyze = st.button("Analyze resale potential", type="primary", use_container_width=True, disabled=uploaded_file is None)

with right:
    with st.container(border=True):
        st.markdown('<div class="section-heading">How FlipLens works</div>', unsafe_allow_html=True)
        st.markdown("**01 · Identify**  ")
        st.caption("Gemini reads the photo and identifies the product.")
        st.markdown("**02 · Compare**  ")
        st.caption("eBay returns current listings for similar items.")
        st.markdown("**03 · Estimate**  ")
        st.caption("See the median asking price and estimated profit after costs.")
        st.markdown(
            '<div class="fliplens-notice">Resale values are estimates based on active asking prices, not verified sold prices.</div>',
            unsafe_allow_html=True,
        )

# Keep results available if a Streamlit widget causes a rerun.
file_signature = (uploaded_file.name, uploaded_file.size) if uploaded_file is not None else None
if st.session_state.get("file_signature") != file_signature:
    st.session_state.pop("analysis", None)
    st.session_state["file_signature"] = file_signature

if analyze:
    try:
        with st.spinner("Identifying the item and searching eBay..."):
            info = identify_item(uploaded_file)
            search_query = info.get("item_name", "").strip()
            if not search_query or search_query.lower() == "unknown":
                search_query = " ".join(
                    part for part in [info.get("brand", ""), info.get("category", "")]
                    if part and part.lower() != "unknown"
                )
            if not search_query:
                raise ValueError("The product could not be identified well enough to search eBay.")
            results = search_ebay(search_query)
            filtered_items = filter_listings(results.get("itemSummaries", []), info)
            prices = []
            for item in filtered_items:
                price = item.get("price") or {}
                if price.get("currency") == "USD" and price.get("value") is not None:
                    try:
                        prices.append(float(price["value"]))
                    except (TypeError, ValueError):
                        pass
            # eBay data stays in memory for this session; it is not saved to disk.
            st.session_state["analysis"] = {
                "info": info, "query": search_query, "items": filtered_items, "prices": prices
            }
    except (requests.exceptions.RequestException, ValueError, json.JSONDecodeError, OSError) as exc:
        st.session_state.pop("analysis", None)
        st.error(f"Analysis failed: {exc}")
    except Exception:
        st.session_state.pop("analysis", None)
        st.error("Something went wrong during analysis. Please check your API configuration and try again.")

analysis = st.session_state.get("analysis")
if analysis:
    st.divider()
    st.markdown('<div class="section-heading">Your resale analysis</div>', unsafe_allow_html=True)
    info = analysis["info"]
    with st.container(border=True):
        st.markdown(f"### {info.get('item_name', 'Identified item')}")
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown("**Brand**")
        c1.write(info.get("brand", "Unknown"))
        c2.markdown("**Model**")
        c2.write(info.get("model", "Unknown"))
        c3.markdown("**Category**")
        c3.write(info.get("category", "Unknown"))
        c4.markdown("**Visible condition**")
        c4.write(info.get("condition", "Unknown"))
        st.caption(f"eBay search: {analysis['query']}")

    prices = analysis["prices"]
    if prices:
        estimated_resale_price = statistics.median(prices)
        ebay_fee_rate = 0.13
        estimated_shipping = 8.00
        selling_fees = estimated_resale_price * ebay_fee_rate
        estimated_profit = estimated_resale_price - purchase_price - selling_fees - estimated_shipping
        a, b, c = st.columns(3)
        a.metric("Median eBay asking price", f"${estimated_resale_price:,.2f}")
        b.metric("Estimated net profit", f"${estimated_profit:,.2f}")
        c.metric("Comparable listings", str(len(prices)))
        with st.container(border=True):
            st.markdown("**Estimated cost breakdown**")
            x, y, z = st.columns(3)
            x.write(f"Purchase: **${purchase_price:,.2f}**")
            y.write(f"Selling fees (13%): **${selling_fees:,.2f}**")
            z.write(f"Shipping: **${estimated_shipping:,.2f}**")
            if estimated_profit > 0:
                st.markdown(
                    '<div class="fliplens-notice fliplens-positive">Potentially profitable at these estimated prices and costs.</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="fliplens-notice">May not be profitable at these estimated prices and costs.</div>',
                    unsafe_allow_html=True,
                )
            st.caption("Rough estimate only. Excludes taxes, packaging, returns, and other costs. Asking prices are not confirmed sales.")
            if len(prices) < 3:
                st.warning("Low confidence: fewer than three comparable prices were found.")
    else:
        st.warning("Not enough comparable pricing information to estimate resale value.")

    st.markdown('<div class="section-heading">Similar items on eBay</div>', unsafe_allow_html=True)
    st.caption("Showing up to five listings. These are current offers, not completed sales.")
    items = analysis["items"]
    if items:
        for start in range(0, min(5, len(items)), 2):
            cols = st.columns(2, gap="medium")
            for col, item in zip(cols, items[start:start + 2]):
                with col:
                    with st.container(border=True):
                        image_url = (item.get("image") or {}).get("imageUrl")
                        if image_url:
                            st.image(image_url, use_container_width=True)
                        st.markdown(f"**{item.get('title', 'Unknown item')}**")
                        price = item.get("price") or {}
                        st.markdown(f"**Asking price:** ${price.get('value', 'N/A')}")
                        listing_url = item.get("itemWebUrl")
                        if listing_url:
                            st.link_button("View on eBay", listing_url, use_container_width=True)
    else:
        st.info("No matching listings passed the f ilters. Try another photo or a more recognizable product.")

st.divider()
st.caption("FlipLens · AI-assisted resale research · Not affiliated with eBay or Google")