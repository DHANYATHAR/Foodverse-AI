from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image, ImageFilter, ImageStat
import io
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/api/food-preprocessing",
    tags=["Food Preprocessing"]
)


@router.post("/analyze")
async def preprocess_food_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid image."
        )

    try:
        image_bytes = await file.read()

        if not image_bytes:
            raise HTTPException(
                status_code=400,
                detail="The uploaded image is empty."
            )

        # Load and standardize the image
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
        original_width, original_height = image.size
        image = image.convert("RGB")

        # Resize to a standard size
        resized = image.resize((224, 224))

        # Reduce noise
        denoised = resized.filter(ImageFilter.MedianFilter(size=3))

        # Extract color features
        stats = ImageStat.Stat(denoised)
        mean_rgb = [round(value, 2) for value in stats.mean]
        stddev_rgb = [round(value, 2) for value in stats.stddev]

        # Estimate brightness and contrast
        grayscale = denoised.convert("L")
        gray_stats = ImageStat.Stat(grayscale)
        brightness = round(gray_stats.mean[0], 2)
        contrast = round(gray_stats.stddev[0], 2)

        # Estimate texture using edge strength
        edges = grayscale.filter(ImageFilter.FIND_EDGES)
        edge_strength = round(ImageStat.Stat(edges).mean[0], 2)

        return {
            "status": "success",
            "filename": file.filename,
            "original_size": {
                "width": original_width,
                "height": original_height
            },
            "processed_size": {
                "width": 224,
                "height": 224
            },
            "preprocessing": [
                "RGB color conversion",
                "Image resizing",
                "Median-filter noise reduction"
            ],
            "features": {
                "mean_rgb": mean_rgb,
                "color_variation_rgb": stddev_rgb,
                "brightness": brightness,
                "contrast": contrast,
                "edge_strength": edge_strength
            },
            "note": (
                "These are basic visual features. "
                "They do not independently prove food freshness "
                "or safety."
            )
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Image preprocessing failed: {str(e)}"
        )
from collections import Counter


def classify_freshness(food_name: str, visual_signs: list = None):
    """
    Activity 3.2: Food Freshness Classification
    and Safety Recommendation Logic.
    """

    visual_signs = visual_signs or []
    signs = [str(sign).lower() for sign in visual_signs]

    spoiled_signs = [
        "mold", "mould", "rotten", "slimy",
        "decay", "black spots", "bad odor",
        "dark brown", "discoloration"
    ]

    moderate_signs = [
        "brown spots", "wrinkled", "slightly soft",
        "yellowing", "minor discoloration"
    ]

    if any(sign in item for sign in signs for item in spoiled_signs):
        freshness = "Spoiled"
        safety_status = "Unsafe"
        confidence = 90
        recommendation = (
            "Do not consume if spoilage is suspected. "
            "Discard the food safely."
        )

    elif any(sign in item for sign in signs for item in moderate_signs):
        freshness = "Moderate"
        safety_status = "Consume Soon"
        confidence = 75
        recommendation = (
            "Inspect carefully and store appropriately. "
            "Visual appearance alone cannot establish safety."
        )

    else:
        freshness = "Fresh"
        safety_status = "Safe to Eat"
        confidence = 60
        recommendation = (
            "No listed spoilage signs were provided. "
            "Check smell, texture, storage history and expiry. "
            "Appearance alone cannot confirm food safety."
        )

    return {
        "item_name": food_name,
        "freshness_level": freshness,
        "confidence": confidence,
        "safety_status": safety_status,
        "detected_signs": visual_signs,
        "reasoning": (
            "Classification based on the visual signs supplied; "
            "this is a preliminary estimate."
        ),
        "recommendation": recommendation
    }
class FreshnessRequest(BaseModel):
    food_name: str = Field(..., min_length=1)
    visual_signs: list[str] = Field(default_factory=list)


@router.post("/freshness")
async def check_food_freshness(request: FreshnessRequest):
    try:
        result = classify_freshness(
            food_name=request.food_name,
            visual_signs=request.visual_signs
        )
        return {
            "status": "success",
            "freshness_analysis": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Freshness classification failed: {str(e)}"
        )