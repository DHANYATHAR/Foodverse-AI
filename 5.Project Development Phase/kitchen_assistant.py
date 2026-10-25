import os
import json
import base64
from typing import Optional

from fastapi import APIRouter, Form, File, UploadFile, HTTPException
from pydantic import BaseModel
from groq import Groq

router = APIRouter()

MODEL_NAME = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class RecipeGenerationResponse(BaseModel):
    dish_name: str
    ingredients: list[str]
    steps: list[str]


@router.post("/generate-recipe", response_model=RecipeGenerationResponse)
async def generate_recipe(
    text_input: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    temp_path = None

    try:
        if not text_input and not file:
            return RecipeGenerationResponse(
                dish_name="No Input",
                ingredients=[],
                steps=["Please provide ingredients or upload a food image."]
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI chef. Generate a recipe using the user's "
                    "ingredients or food image. Return valid JSON with exactly "
                    "these fields: dish_name, ingredients (list of strings), "
                    "and steps (list of strings). Do not invent certainty "
                    "about ingredients that cannot be identified."
                )
            }
        ]

        if file:
            if not file.content_type or not file.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=400,
                    detail="Please upload a valid image file."
                )

            image_bytes = await file.read()
            if not image_bytes:
                raise HTTPException(
                    status_code=400,
                    detail="The uploaded image is empty."
                )

            b64 = base64.b64encode(image_bytes).decode("utf-8")
            image_url = (
                f"data:{file.content_type};base64,{b64}"
            )

            user_content = [
                {
                    "type": "text",
                    "text": (
                        "Analyze the food or ingredients in this image "
                        "and generate a practical cooking recipe."
                    )
                },
                {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                }
            ]

            if text_input:
                user_content[0]["text"] += (
                    f" Additional instructions: {text_input}"
                )

            messages.append({
                "role": "user",
                "content": user_content
            })

        else:
            messages.append({
                "role": "user",
                "content": (
                    f"Generate a detailed recipe based on these ingredients "
                    f"or requirements: {text_input}"
                )
            })

        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=1200,
        )

        result = json.loads(
            completion.choices[0].message.content
        )

        return RecipeGenerationResponse(
            dish_name=result.get("dish_name", "Custom Recipe"),
            ingredients=result.get("ingredients", []),
            steps=result.get("steps", [])
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Recipe generation failed: {str(exc)}"
        )