import base64
import json
import re
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image, ImageStat
import io

router = APIRouter(
    prefix="/api/hygiene",
    tags=["Restaurant Hygiene"]
)


def analyze_hygiene_image(image_bytes: bytes, context_text: str = ""):
    """Analyze basic image features and return a preliminary hygiene report."""

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image.load()

        width, height = image.size
        stats = ImageStat.Stat(image)
        brightness = round(sum(stats.mean) / 3, 2)

        # Basic rule-based baseline; this does not detect PPE or violations.
        return {
            "status": "success",
            "image_size": {"width": width, "height": height},
            "brightness": brightness,
            "context": context_text,
            "overall_score": 100,
            "floor_score": None,
            "violations": [],
            "ai_summary": (
                "Image loaded successfully. Automated detection of gloves, "
                "hairnets, phone use, and surface cleanliness is not enabled. "
                "A human inspection is required before assigning a real "
                "hygiene compliance score."
            ),
            "analysis_type": "image validation baseline"
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to process image: {str(e)}"
        )


@router.post("/analyze")
async def analyze_hygiene(
    file: UploadFile = File(...),
    context_text: Optional[str] = Form(default="")
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid image."
        )

    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    return analyze_hygiene_image(image_bytes, context_text or "")


@router.post("/score")
async def calculate_hygiene_score(
    violations: str = Form(default="")
):
    import json
    from fastapi import HTTPException

    raw = violations.strip()

    if not raw:
        items = []
    else:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                items = parsed
            else:
                items = [raw]
        except json.JSONDecodeError:
            # Swagger may send plain text instead of JSON.
            items = [item.strip() for item in raw.split(",") if item.strip()]

    if not all(isinstance(item, str) for item in items):
        raise HTTPException(
            status_code=400,
            detail="Each violation must be text."
        )

    weights = {
        "no gloves": 20,
        "hair net missing": 20,
        "dirty floor": 15,
        "phone use": 15,
        "unsafe food handling": 30
    }

    report = []
    deduction = 0

    for item in items:
        name = item.strip()
        weight = weights.get(name.lower(), 10)
        deduction += weight
        report.append({
            "violation": name,
            "severity": "High" if weight >= 20 else "Medium",
            "score_deduction": weight
        })

    return {
        "status": "success",
        "overall_score": max(0, 100 - deduction),
        "violations": report,
        "ai_summary": "Score calculated from supplied violations; automatic visual detection is not performed."
    }