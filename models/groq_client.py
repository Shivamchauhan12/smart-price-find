import streamlit as st
from groq import Groq
from PIL import Image
import io, base64

# Vision-capable models to try in order (most capable first)
_GROQ_VISION_MODELS = [
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "llama-3.2-11b-vision-preview",
    "llama-3.2-90b-vision-preview",
]

@st.cache_resource
def load_groq_client():
    return Groq(api_key=st.secrets["groq_api_key"])

def _image_to_b64(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def extract_item_name_groq(image: Image.Image):
    """Try to get caption from Groq API using available vision models."""
    client = load_groq_client()
    img_b64 = _image_to_b64(image)

    for model in _GROQ_VISION_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe the product in this image briefly (just the product name and brand if visible, no extra text)."
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
                temperature=0.1,
            )
            caption = response.choices[0].message.content.strip()
            print(f"✅ Groq succeeded with model: {model}")
            return caption, f"Groq ({model.split('/')[-1]})"

        except Exception as e:
            err_msg = str(e).lower()
            if "model_not_found" in err_msg or "not found" in err_msg or "404" in err_msg:
                print(f"⚠️ Groq model not available: {model}, trying next...")
                continue
            elif "rate limit" in err_msg or "quota" in err_msg or "429" in err_msg:
                print(f"⚠️ Groq rate limit/quota exceeded for {model}.")
                return None, "groq_rate_limit"
            else:
                print(f"❌ Groq error with {model}:", e)
                continue

    print("⚠️ No Groq vision model available, falling back to BLIP.")
    return None, "groq_unavailable"


