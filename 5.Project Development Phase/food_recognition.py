from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
import base64
import json
import speech_recognition as sr
from pydub import AudioSegment
from PIL import Image
import io
import re
from groq import Groq
from dotenv import load_dotenv

from pathlib import Path

load_dotenv(
    Path(__file__).resolve().parents[1] / ".env",
    override=True
)

router = APIRouter(
    prefix="/api/food-recognition",
    tags=["Food Recognition"]
)

# --- CONFIG ---
# Initialize Groq Client
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None
 
MODEL_NAME = "qwen/qwen3.8-27b"

class NutritionInfo(BaseModel):
    calories: int
    protein: float
    carbs: float
    fats: float
    fiber: float

@router.get("/test")
def test_food_recognition():
    return {
        "message": "Food Recognition API is working!",
        "status": "success"
    }
@router.post("/upload")
async def upload_food_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload an image file"
        )

    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty"
        )

    if client is None:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is missing. Configure it in your .env file."
        )

    try:
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Identify the food in this image. "
                                "Give the likely food name, visible "
                                "ingredients if identifiable, and a "
                                "brief explanation. If uncertain, say so."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": (
                                    f"data:{file.content_type};base64,"
                                    f"{encoded_image}"
                                )
                            }
                        }
                    ]
                }
            ],
            temperature=0.2,
            max_tokens=400
        )

        recognition = response.choices[0].message.content

        return {
            "message": "Image analyzed successfully",
            "filename": file.filename,
            "food_recognition": recognition,
            "status": "success"
        }

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Food recognition failed: {str(e)}"
        )
@router.post("/nutrition")
async def estimate_nutrition(food_name: str):
    if not client:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is missing"
        )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Estimate nutrition for 100g of {food_name}. "
                        "Return only valid JSON with these fields: "
                        "dish_name, calories, protein, carbs, fats, "
                        "fiber, sugar, health_score, health_label, "
                        "reasoning, alternatives. "
                        "Use numeric values for nutrition and score. "
                        "health_score must be 0-100. "
                        "health_label must be Healthy, Moderate, or Unhealthy."
                    )
                }
            ],
            temperature=0.2,
            max_tokens=400
        )

        result = response.choices[0].message.content
        return {
            "status": "success",
            "nutrition": json.loads(result)
        }

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Nutrition estimation failed: {str(e)}"
        )
  