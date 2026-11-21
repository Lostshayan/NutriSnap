"""Food Calorie Image Classifier – FastAPI backend with automatic dual-model detection."""

import json
from contextlib import asynccontextmanager
from pathlib import Path

import torch
import torch.nn as nn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from torchvision import models, transforms

# ── Paths ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# ── Globals populated at startup ─────────────────────────────────────────
nutrition_db: dict = {}
models_dict: dict[str, dict] = {}
transform: transforms.Compose | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load both models and reference nutrition data once on startup."""
    global nutrition_db, models_dict, transform

    # 1. Nutrition database (all 25 dishes)
    with open(BASE_DIR / "nutrition_db.json") as f:
        nutrition_db = json.load(f)

    # 2. Global Model (10 classes)
    with open(ARTIFACTS_DIR / "class_names.json") as f:
        global_classes = json.load(f)

    global_model = models.mobilenet_v2(weights=None)
    global_model.classifier[1] = nn.Linear(global_model.classifier[1].in_features, len(global_classes))
    global_model.load_state_dict(torch.load(ARTIFACTS_DIR / "food_model.pth", map_location="cpu"))
    global_model.eval()

    # 3. Indian Model (15 classes)
    with open(ARTIFACTS_DIR / "class_names (1).json") as f:
        indian_classes = json.load(f)

    indian_model = models.mobilenet_v2(weights=None)
    indian_model.classifier[1] = nn.Linear(indian_model.classifier[1].in_features, len(indian_classes))
    indian_model.load_state_dict(torch.load(ARTIFACTS_DIR / "food_model (1).pth", map_location="cpu"))
    indian_model.eval()

    models_dict = {
        "global": {"model": global_model, "classes": global_classes},
        "indian": {"model": indian_model, "classes": indian_classes},
    }

    # 4. Eval transforms (ImageNet-standard)
    transform = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ]
    )

    print(f"✅  Loaded 'global' model ({len(global_classes)} classes) & 'indian' model ({len(indian_classes)} classes)")
    yield
    print("🛑  Shutting down")


# ── App ──────────────────────────────────────────────────────────────────
app = FastAPI(title="Food Calorie Classifier", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_MIME = {"image/png", "image/jpeg", "image/webp"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """Accept an image upload, evaluate against both models, and return winning model predictions."""

    # ── Validate MIME ────────────────────────────────────────────────────
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type '{file.content_type}'. Accepted: PNG, JPEG, WebP.",
        )

    # ── Read & preprocess ────────────────────────────────────────────────
    try:
        image = Image.open(file.file).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Could not decode the uploaded file as an image.")

    input_tensor = transform(image).unsqueeze(0)  # (1, 3, 224, 224)

    # ── Run both models and compare top-1 raw logits ─────────────────────
    with torch.inference_mode():
        logits_global = models_dict["global"]["model"](input_tensor)
        logits_indian = models_dict["indian"]["model"](input_tensor)

        max_logit_global, _ = logits_global.max(dim=1)
        max_logit_indian, _ = logits_indian.max(dim=1)

        if max_logit_indian.item() >= max_logit_global.item():
            winning_key = "indian"
            winning_logits = logits_indian
        else:
            winning_key = "global"
            winning_logits = logits_global

        active_classes = models_dict[winning_key]["classes"]
        probs = torch.softmax(winning_logits, dim=1).squeeze()

    # ── Top-3 results ────────────────────────────────────────────────────
    top_k = min(3, len(active_classes))
    top_probs, top_idxs = probs.topk(top_k)
    results = []
    for prob, idx in zip(top_probs.tolist(), top_idxs.tolist()):
        name = active_classes[idx]
        nutrition = nutrition_db.get(name, {})
        results.append(
            {
                "class_name": name,
                "confidence": round(prob * 100, 2),
                "nutrition": nutrition,
            }
        )

    low_confidence_warning = results[0]["confidence"] < 50.0

    return JSONResponse(
        {
            "detected_cuisine": winning_key,
            "predictions": results,
            "low_confidence_warning": low_confidence_warning,
        }
    )


# ── Serve frontend (must come AFTER API routes) ─────────────────────────
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
