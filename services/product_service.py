
import requests

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
        for item in g_resp["shopping_results"][:8]:
            results.append({
                "title": item.get("title"),
                "price": item.get("extracted_price"),
                "source": item.get("source"),
                "pageToken": item.get("immersive_product_page_token"),
                "link": item.get("product_link") or item.get("link"),
                "product_id": item.get("product_id")
            })
    return results
