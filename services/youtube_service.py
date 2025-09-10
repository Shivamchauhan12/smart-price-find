
import requests

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
