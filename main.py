import os
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
import streamlit as st
import requests
from PIL import Image
import torch
from transformers.models.blip import BlipProcessor, BlipForConditionalGeneration


# ---------------- Step 1: Load Models ----------------
@st.cache_resource
def load_blip_model():
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base", use_fast=False)
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    return processor, model

def extract_item_name(image: Image.Image) -> str:
    processor, model = load_blip_model()
    inputs = processor(image, return_tensors="pt")
    out = model.generate(**inputs, max_new_tokens=50)
    caption = processor.decode(out[0], skip_special_tokens=True)
    return caption

def fetch_youtube_videos(query: str, serp_api_key: str, max_results=3):
    params = {"engine": "youtube", "search_query": query, "api_key": serp_api_key, "hl": "en", "gl": "in"}
    resp = requests.get("https://serpapi.com/search.json", params=params).json()
    videos = []
    if "video_results" in resp:
        for v in resp["video_results"][:max_results]:
            thumb = v.get("thumbnail")
            if isinstance(thumb, list) and len(thumb) > 0:
                thumb_url = thumb[0].get("url")
            elif isinstance(thumb, dict):
                thumb_url = thumb.get("url")
            else:
                thumb_url = None
            videos.append({"title": v.get("title"), "link": v.get("link"), "thumbnail": thumb_url})
    return videos

def fetch_product_reviews(product_id: str, serp_api_key: str, max_reviews=5):
    params = {
        "engine": "google_immersive_product",
        "page_token": product_id,
        "api_key": serp_api_key,
        "reviews": "true",
        "hl": "en",
        "gl": "in"
    }
    try:
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print("❌ Error fetching reviews:", e)
        return []

    product_results = data.get("product_results") or data.get("product_result") or {}
    review_candidates = []
    if isinstance(product_results, dict):
        review_candidates = product_results.get("user_reviews") or product_results.get("reviews") or []

    if not review_candidates:
        review_candidates = data.get("user_reviews") or data.get("reviews_results") or data.get("reviews") or []

    if isinstance(review_candidates, dict):
        review_candidates = review_candidates.get("reviews") or review_candidates.get("user_reviews") or []

    if not isinstance(review_candidates, list):
        review_candidates = []

    reviews = []
    for r in review_candidates[:max_reviews]:
        reviews.append({
            "title": r.get("title") or None,
            "rating": r.get("rating") or r.get("stars") or None,
            "snippet": r.get("text") or r.get("snippet") or r.get("review_text") or None,
            "date": r.get("date") or None,
            "user": r.get("user_name") or r.get("user") or None,
            "source": r.get("source") or None,
            "icon": r.get("icon") or r.get("profile_photo") or None,
            "raw": r
        })
    return reviews

def fetch_prices_from_amazon_google(query: str, serp_api_key: str):
    results = []
    g_params = {"engine": "google_shopping", "q": query, "hl": "en", "gl": "in", "currency": "INR", "api_key": serp_api_key}
    g_resp = requests.get("https://serpapi.com/search.json", params=g_params).json()
    if "shopping_results" in g_resp:
        for item in g_resp["shopping_results"][:5]:
            results.append({
                "title": item.get("title"),
                "price": item.get("extracted_price"),
                "source": item.get("source"),
                "pageToken": item.get("immersive_product_page_token"),
                "link": item.get("product_link") or item.get("link"),
                "product_id": item.get("product_id")
            })
    return results

# ---------------- Step 3: Streamlit UI ----------------
# Hide Streamlit's default toolbar and "Made with Streamlit" footer
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}    /* hides the menu */
    header {visibility: hidden;}       /* hides the top header */
    footer {visibility: hidden;}       /* hides the footer */
    [data-testid="stToolbar"] {display: none;}  /* hides deploy/share/toolbar icons */
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
st.set_page_config(
    page_title="Smart Price Finder",
    page_icon="🛒",
    layout="wide"
)
st.title("🛒 Smart Price Finder from a Single Image")
st.write(
    """
    Upload **product image**, and I’ll do the rest:
    - 🔍 Detect and recognize the item automatically  
    - ✍️ refine text automatically  
    - 💲 Fetch live prices from multiple sources   
    - ▶️ Show related YouTube reviews and demos 
    - 🖼️ display product reviews  
    """
)

serp_api_key = st.secrets["serp_api_key"]

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

    if not st.session_state.user_query:
        with st.spinner("🔍 Detecting item..."):
            detected_item = extract_item_name(image)
            st.session_state.user_query = detected_item

    user_query = st.text_area("✍️ Refine description", key="user_query")

    if st.button("🔎 Search Prices"):
        with st.spinner(f"💰 Fetching prices for {user_query}..."):
            st.session_state.products = fetch_prices_from_amazon_google(user_query, serp_api_key)

# ---------------- Step 6: Render Products ----------------
products = st.session_state.products
if products:
    st.subheader(f"Results for: {st.session_state.user_query}")
    
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
            if videos:
                # Build a card grid with hover and play overlay
                html = """
                <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fancyapps/ui/dist/fancybox.css" />
                <script src="https://cdn.jsdelivr.net/npm/@fancyapps/ui/dist/fancybox.umd.js"></script>

                <style>
                    .video-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
                        gap: 16px;
                        margin-top: 12px;
                    }
                    .video-card {
                        position: relative;
                        border-radius: 12px;
                        overflow: hidden;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                        transition: transform 0.2s ease, box-shadow 0.2s ease;
                        background: #fff;
                    }
                    .video-card:hover {
                        transform: translateY(-4px);
                        box-shadow: 0 8px 18px rgba(0,0,0,0.25);
                    }
                    .video-card img {
                        width: 100%;
                        height: 160px;
                        object-fit: cover;
                        display: block;
                    }
                    .video-title {
                        padding: 10px;
                        font-size: 14px;
                        font-weight: 600;
                        line-height: 1.3;
                        color: #333;
                        height: 46px;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    }
                    .play-overlay {
                        position: absolute;
                        top: 0; left: 0; right: 0; bottom: 0;
                        background: rgba(0,0,0,0.4);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        opacity: 0;
                        transition: opacity 0.2s ease;
                    }
                    .video-card:hover .play-overlay {
                        opacity: 1;
                    }
                    .play-overlay span {
                        font-size: 50px;
                        color: #fff;
                        text-shadow: 0 2px 8px rgba(0,0,0,0.5);
                    }
                </style>

                <div class="video-grid">
                """

                for idx, v in enumerate(videos):
                    video_url = v.get("link") or ""
                    vid = ""
                    if "watch?v=" in video_url:
                        vid = video_url.split("watch?v=")[1].split("&")[0]
                    elif "youtu.be/" in video_url:
                        vid = video_url.split("youtu.be/")[1].split("?")[0]
                    else:
                        vid = video_url.rstrip("/").split("/")[-1] if video_url else ""

                    embed_url = f"https://www.youtube.com/watch?v={vid}" if vid else video_url
                    thumbnail = v.get("thumbnail") or (f"https://img.youtube.com/vi/{vid}/hqdefault.jpg" if vid else "")
                    title = (v.get("title") or "").replace('"', "&quot;")
                    modal_group = f"videos-{p_idx}"

                    html += f'''
                    <a data-fancybox="{modal_group}" data-type="iframe" data-src="{embed_url}" href="javascript:;" class="video-card">
                        <img src="{thumbnail}" alt="{title}" />
                        <div class="play-overlay"><span>▶</span></div>
                        <div class="video-title">{title}</div>
                    </a>
                    '''

                html += "</div>"
                st.components.v1.html(html, height=520, scrolling=True)
            else:
                st.info("No related YouTube videos found.")

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
