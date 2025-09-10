import os
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
import streamlit as st
from PIL import Image
from models.blip_model import extract_caption_with_blip
from models.groq_client import extract_item_name_groq
from services.product_service import fetch_prices_from_amazon_google, fetch_product_reviews
from services.youtube_service import fetch_youtube_videos
from utils.ui_helpers import apply_global_styles, render_video_grid



# ---------------- Step 1: Load Models ----------------    
def extract_item_name(image: Image.Image):
    # Try Groq first
    caption, source = extract_item_name_groq(image)
    if caption:
        return caption, source

    # Fallback → BLIP
    return extract_caption_with_blip(image)
 
# ---------------- Step 3: Streamlit UI ----------------
# Hide Streamlit's default toolbar and "Made with Streamlit" footer

st.set_page_config(
    page_title="Smart Price Finder",
    page_icon="🛒",
    layout="wide"
)
apply_global_styles()
st.title("🛒 Smart Price Finder from a Image")
st.write(
    """
    Upload **product image**, and I’ll do the rest:
    - 🔍 Detect and recognize the item automatically 
    - 💲 Fetch live prices from multiple sources   
    - ▶️ Show related YouTube demos and reviews 
    """
)

serp_api_key = api_key=st.secrets["serp_api_key"]
uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"], accept_multiple_files=False)

# ---------------- Step 4: Session State ----------------
if "products" not in st.session_state:
    st.session_state.products = []
if "user_query" not in st.session_state:
    st.session_state.user_query = ""
if "last_uploaded" not in st.session_state:
    st.session_state.last_uploaded = None

# Reset state when file changes or removed (cross clicked)
if uploaded_file != st.session_state.last_uploaded:
    st.session_state.last_uploaded = uploaded_file
    st.session_state.products = []
    st.session_state.user_query = ""

# ---------------- Step 5: Process uploaded image ----------------
if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Uploaded Image", width=300)

    # --- NEW: let user choose captioning method ---
        st.markdown(
        """
        **ℹ️ Captioning Methods**
        - 🔵 **Groq (Paid/Token-based)** → It may fail if quota is over.  
        - 🟢 **BLIP (Free)** → Always available.  
        """
    )

    caption_method = st.radio(
        "Select captioning method:",
        ["Result from Groq", "Result from Blip"],
        index=0,
        horizontal=True
    )

    method_map = {
        "Result from Groq": "groq",
        "Result from Blip": "blip"
    }
    selected_method = method_map[caption_method]

    # Detect item if not already set OR method changed
    if (
        not st.session_state.user_query
        or st.session_state.get("caption_source_method") != selected_method
    ):
        with st.spinner("🔍 Detecting item..."):
            if selected_method == "groq":
                detected_item, detected_source = extract_item_name_groq(image)
            elif selected_method == "blip":
                detected_item, detected_source = extract_caption_with_blip(image)
            else:  # auto
                detected_item, detected_source = extract_item_name(image)

            st.session_state.user_query = detected_item
            st.session_state.caption_source = detected_source
            st.session_state.caption_source_method = selected_method

    if "caption_source" in st.session_state:
        st.caption(f"✅ Detected using **{st.session_state.caption_source}**")

    # Allow user to refine
    user_query = st.text_area("✍️ Refine description", key="user_query")

    if st.button("🔎 Search Prices"):
        with st.spinner(f"💰 Fetching prices for {user_query}..."):
            st.session_state.products = fetch_prices_from_amazon_google(user_query, serp_api_key)

# ---------------- Step 6: Render Products ----------------
products = st.session_state.products
if products:
    st.subheader(f"Results for: {st.session_state.user_query}")

  # ✅ Sorting + Filter options
    col1, col2 = st.columns([1, 1])
    with col1:
        sort_order = st.radio(
            "Sort by price:",
            ["High → Low", "Low → High"],
            index=0,  # ✅ Default to High → Low
            horizontal=True
        )
  
    products = [p for p in products if p["price"] is not None]

    # ✅ Apply sorting
    if sort_order == "High → Low":
        products = sorted(products, key=lambda x: x["price"] if x["price"] is not None else 0, reverse=True)
    else:
        products = sorted(products, key=lambda x: x["price"] if x["price"] is not None else 0)

    
    for p_idx, p in enumerate(products):
        price_display = f"₹{p['price']}" if p['price'] else "N/A"
        st.markdown(
            f"**{p['title']}**\n\n"
            f"- Price: {price_display}\n"
            f"- Source: {p['source']}\n"
            f"- [Buy Here]({p['link']})"
        )

        # 🎥 YouTube Videos
        with st.expander("📺 Related YouTube Videos"):
            videos = fetch_youtube_videos(p['title'], serp_api_key)
            render_video_grid(videos, group=f"videos-{p_idx}") if videos else st.info("No related videos found.")

        # 📝 Reviews
        if p.get("product_id"):
            with st.expander("📝 Latest Reviews"):
                reviews = fetch_product_reviews(p["pageToken"], serp_api_key)
                if reviews:
                    for r in reviews:
                        st.markdown(
                            f"- ⭐ {r['rating']} | ({r['date']})\n"
                            f"  - {r['snippet']}"
                        )
                else:
                    st.info("No reviews found.")
