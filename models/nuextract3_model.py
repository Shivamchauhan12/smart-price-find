import os
import torch
from transformers import pipeline
from PIL import Image

# Load the NuExtract3 model from HuggingFace
# Using the image-to-text pipeline. The model is large; we load it lazily.

# Environment variable to avoid HF hub symlinks issues (already set in main)

# Initialize pipeline once
_nuextract3_pipe = None

def _get_nuextract3_pipe():
    global _nuextract3_pipe
    if _nuextract3_pipe is None:
        # Use torch dtype float16 if GPU available for speed, else default
        device = 0 if torch.cuda.is_available() else -1
        _nuextract3_pipe = pipeline("image-to-text", model="numind/NuExtract3", device=device)
    return _nuextract3_pipe

def extract_caption_nuextract3(image: Image.Image):
    """Generate a caption for the given PIL image using NuExtract3.

    Returns a tuple (caption: str, source: str). If generation fails, returns ("", "").
    """
    try:
        pipe = _get_nuextract3_pipe()
        # The pipeline expects either a file path or a PIL Image
        result = pipe(image)
        # result is a list of dicts with 'generated_text'
        if isinstance(result, list) and len(result) > 0:
            caption = result[0].get('generated_text', '').strip()
            return caption, "NuExtract3"
    except Exception as e:
        # Log the exception if needed (streamlit will capture stdout)
        print(f"[NuExtract3] Error generating caption: {e}")
    return "", ""
