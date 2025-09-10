import streamlit as st
from PIL import Image
from transformers.models.blip import BlipProcessor, BlipForConditionalGeneration

@st.cache_resource
def load_blip_model():
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base", use_fast=False)
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    return processor, model

def extract_caption_with_blip(image: Image.Image) -> str:
    processor, model = load_blip_model()
    inputs = processor(image, return_tensors="pt")
    out = model.generate(**inputs, max_new_tokens=50)
    caption = processor.decode(out[0], skip_special_tokens=True)
    return caption, "blip"
