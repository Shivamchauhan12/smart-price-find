import streamlit as st
from groq import Groq
from PIL import Image

@st.cache_resource
def load_groq_client():
    return Groq(api_key=st.secrets["groq_api_key"])

def extract_item_name_groq(image: Image.Image):
    """Try to get caption from Groq API (llama-4-scout)."""
    client = load_groq_client()

    import io, base64
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    img_bytes = buf.getvalue()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe the product in this image briefly (just the product and brand name, no extra text)."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_b64}"
                            }
                        }
                    ],
                }
            ],
            max_tokens=100,
        )

        caption = response.choices[0].message.content.strip()
        return caption, "Groq"

    except Exception as e:
        err_msg = str(e).lower()
        if "rate limit" in err_msg or "quota" in err_msg or "429" in err_msg:
            print("⚠️ Groq quota/rate limit exceeded, falling back to BLIP.")
            return None, None
        else:
            print("❌ Groq error:", e)
            return None, None

