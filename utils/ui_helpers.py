# utils/ui_helpers.py
import streamlit as st

def apply_global_styles():
    hide_style = """
        <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stToolbar"] {display: none;}
        </style>
    """
    st.markdown(hide_style, unsafe_allow_html=True)


def render_video_grid(videos, group="videos"):
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

    for v in videos:
        video_url = v.get("link") or ""
        vid = ""
        if "watch?v=" in video_url:
            vid = video_url.split("watch?v=")[1].split("&")[0]
        elif "youtu.be/" in video_url:
            vid = video_url.split("youtu.be/")[1].split("?")[0]

        embed_url = f"https://www.youtube.com/watch?v={vid}" if vid else video_url
        thumbnail = v.get("thumbnail") or f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"
        title = (v.get("title") or "").replace('"', "&quot;")

        html += f"""
        <a data-fancybox="{group}" data-type="iframe" data-src="{embed_url}" href="javascript:;" class="video-card">
            <img src="{thumbnail}" alt="{title}" />
            <div class="play-overlay"><span>▶</span></div>
            <div class="video-title">{title}</div>
        </a>
        """

    html += "</div>"
    st.components.v1.html(html, height=520, scrolling=True)
