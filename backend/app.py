import os
import sys
sys.path.append(os.path.dirname(__file__))  # FIX 1: dynamic path, not hardcoded

import torch
from PIL import Image
from transformers import CLIPProcessor
import io

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from model import C2PModel, model
from metadata_generator import generate_metadata
from scoring import calculate_recency_score, calculate_utility_score, assign_tier

# FIX 2: correct static_folder to match your actual folder layout
app = Flask(__name__, static_folder=os.path.join("..", "frontend", "static"))
CORS(app)

ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}

print("Loading CLIP processor...")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")
print("Processor ready!")


# FIX 3: correct path for serving index.html
@app.route("/")
def home():
    ui_folder = os.path.join(os.path.dirname(__file__), "..", "frontend", "static", "ui")
    return send_from_directory(ui_folder, "index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if "image" not in request.files:
        return jsonify({"error": "No image received"}), 400

    image_file = request.files["image"]
    filename   = image_file.filename

    # FIX 4: validate file extension before opening
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Unsupported file type: {ext}"}), 400

    image_bytes = image_file.read()

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        return jsonify({"error": f"Could not open image: {str(e)}"}), 400

    ai_score, ai_label, model_error = detect_ai(image)

    metadata = generate_metadata(filename)
    recency_score, norm_factors = calculate_recency_score(metadata)
    utility_score = calculate_utility_score(recency_score, ai_score, ai_label)
    tier = assign_tier(utility_score)

    result = {
        "filename"      : filename,
        "ai_score"      : ai_score,
        "ai_label"      : ai_label,
        "metadata"      : metadata,
        "norm_factors"  : norm_factors,
        "recency_score" : recency_score,
        "utility_score" : utility_score,
        "tier"          : tier,
        "model_error"   : model_error   # FIX 5: surface errors to the caller
    }

    return jsonify(result)


def detect_ai(image):
    model_error = None
    ai_score = 0.0

    try:
        inputs = processor(images=image, return_tensors="pt")
        with torch.no_grad():
            output   = model.forward(inputs['pixel_values'])
            ai_score = torch.sigmoid(output).item()
        ai_score = round(ai_score, 4)

    except Exception as e:
        # FIX 5: log clearly and flag the error — don't silently default to "Real"
        print(f"[ERROR] Model inference failed: {e}")
        model_error = str(e)

    ai_label = "AI Generated" if ai_score > 0.5 else "Real"
    return ai_score, ai_label, model_error


if __name__ == "__main__":
    print("Utilex server running at http://localhost:5000")
    app.run(debug=True, port=5000)