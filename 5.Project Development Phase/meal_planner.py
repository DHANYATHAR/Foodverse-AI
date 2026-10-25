import os
import json
from typing import List, Dict, Optional

from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel, Field

from groq import Groq

router = APIRouter()

MODEL_NAME = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class UserProfile(BaseModel):
    age: int = Field(gt=0, le=120)
    height_cm: float = Field(gt=0, le=300)
    weight_kg: float = Field(gt=0, le=500)
    dietary_preferences: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    health_goals: List[str] = Field(default_factory=list)
    activity_level: str = "moderate"


class MealDetails(BaseModel):
    dish_name: str
    description: str
    ingredients: List[str]
    calories: int
    macros: Dict[str, str | int | float]
    reasoning: str
    portion_size: str
    prep_style: str


class MealAlternatives(BaseModel):
    original_dish: str
    alternatives: List[MealDetails]


class DailyMealPlan(BaseModel):
    breakfast: MealDetails
    mid_morning_snack: MealDetails
    lunch: MealDetails
    evening_snack: MealDetails
    dinner: MealDetails
    daily_totals: Dict[str, str]
    hydration_target: str


class WeeklyReport(BaseModel):
    adherence_score: int
    calorie_balance: str
    macro_balance: str
    consistency: str
    concern_areas: List[str]
    highlights: List[str]
    next_week_suggestions: List[str]
    motivation: str


class FullMealPlanResponse(BaseModel):
    user_profile_summary: str
    daily_plan: DailyMealPlan


@router.post("/profile", tags=["Personalized Meal Planner"])
async def process_user_profile(profile: UserProfile):
    return {
        "message": "User profile validated successfully",
        "profile": profile.model_dump(),
    }


@router.post("/generate-daily-plan", response_model=FullMealPlanResponse,
             tags=["Personalized Meal Planner"])
async def generate_daily_plan(profile: UserProfile):
    prompt = f"""
Create a one-day meal plan for this user:
{profile.model_dump_json()}

Respect all listed allergies and dietary preferences.
Return only valid JSON matching this structure:
{{
  "user_profile_summary": "brief summary",
  "daily_plan": {{
    "breakfast": {{"dish_name":"", "description":"", "ingredients":[],
      "calories":0, "macros":{{"protein":"", "carbs":"", "fats":""}},
      "reasoning":"", "portion_size":"", "prep_style":""}},
    "mid_morning_snack": {{"dish_name":"", "description":"", "ingredients":[],
      "calories":0, "macros":{{"protein":"", "carbs":"", "fats":""}},
      "reasoning":"", "portion_size":"", "prep_style":""}},
    "lunch": {{"dish_name":"", "description":"", "ingredients":[],
      "calories":0, "macros":{{"protein":"", "carbs":"", "fats":""}},
      "reasoning":"", "portion_size":"", "prep_style":""}},
    "evening_snack": {{"dish_name":"", "description":"", "ingredients":[],
      "calories":0, "macros":{{"protein":"", "carbs":"", "fats":""}},
      "reasoning":"", "portion_size":"", "prep_style":""}},
    "dinner": {{"dish_name":"", "description":"", "ingredients":[],
      "calories":0, "macros":{{"protein":"", "carbs":"", "fats":""}},
      "reasoning":"", "portion_size":"", "prep_style":""}},
    "daily_totals": {{"calories":"", "protein":"", "carbs":"", "fats":""}},
    "hydration_target":""
  }}
}}
Treat calorie and nutrition estimates as approximate.
Do not claim to provide medical advice.
"""
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a careful meal-planning assistant."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=3000,
        )
        data = json.loads(completion.choices[0].message.content)
        return FullMealPlanResponse(**data)

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Meal plan generation failed: {str(exc)}",
        )


@router.post("/alternatives", response_model=MealAlternatives,
             tags=["Personalized Meal Planner"])
async def suggest_alternatives(
    dish_name: str,
    profile: UserProfile,
):
    prompt = f"""
Suggest 3 alternatives to this dish: {dish_name}.
User profile: {profile.model_dump_json()}
Respect allergies and dietary preferences.
Return JSON with original_dish and alternatives.
Each alternative must have dish_name, description, ingredients,
calories, macros (protein, carbs, fats), reasoning, portion_size,
and prep_style. Use approximate nutrition estimates.
"""
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a careful meal-planning assistant."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=2000,
        )
        data = json.loads(completion.choices[0].message.content)
        return MealAlternatives(**data)

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Alternative generation failed: {str(exc)}",
        )
@router.post(
    "/generate",
    response_model=FullMealPlanResponse,
    tags=["Personalized Meal Planner"]
)
async def generate_comprehensive_plan(
    age: int = Form(...),
    gender: str = Form(...),
    height: float = Form(...),
    weight: float = Form(...),
    activity_level: str = Form("Moderate"),
    medical_conditions: str = Form("None"),
    goals: str = Form(...),
    diet_type: str = Form("Standard"),
    cuisine: str = Form("Global"),
    allergies: str = Form("None"),
    recent_history: str = Form("No data"),
    weight_change: str = Form("Stable"),
):
    prompt = f"""
You are a professional AI dietitian. Generate a personalized
one-day meal plan using the user's information.

USER PROFILE:
Age: {age}
Gender: {gender}
Height: {height} cm
Weight: {weight} kg
Activity level: {activity_level}
Medical conditions: {medical_conditions}
Goals: {goals}
Diet type: {diet_type}
Cuisine: {cuisine}
Allergies: {allergies}
Recent history: {recent_history}
Recent progress: {weight_change}

Respect all allergies and dietary restrictions.
Provide breakfast, mid-morning snack, lunch, evening snack,
and dinner. Include ingredients, approximate calories,
macros, reasoning, portion size, and preparation style.
Include daily nutrition totals and a hydration target.
Treat nutrition values as estimates, not medical advice.

Return only valid JSON with this structure:
{{
  "user_profile_summary": "summary",
  "daily_plan": {{
    "breakfast": {{
      "dish_name": "name",
      "description": "description",
      "ingredients": ["ingredient"],
      "calories": 300,
      "macros": {{
        "protein": "15g",
        "carbs": "40g",
        "fats": "10g"
      }},
      "reasoning": "reason",
      "portion_size": "one serving",
      "prep_style": "cooked"
    }},
    "mid_morning_snack": {{
      "dish_name": "name",
      "description": "description",
      "ingredients": ["ingredient"],
      "calories": 150,
      "macros": {{
        "protein": "5g",
        "carbs": "20g",
        "fats": "5g"
      }},
      "reasoning": "reason",
      "portion_size": "one serving",
      "prep_style": "fresh"
    }},
    "lunch": {{
      "dish_name": "name",
      "description": "description",
      "ingredients": ["ingredient"],
      "calories": 450,
      "macros": {{
        "protein": "20g",
        "carbs": "55g",
        "fats": "15g"
      }},
      "reasoning": "reason",
      "portion_size": "one serving",
      "prep_style": "cooked"
    }},
    "evening_snack": {{
      "dish_name": "name",
      "description": "description",
      "ingredients": ["ingredient"],
      "calories": 150,
      "macros": {{
        "protein": "5g",
        "carbs": "20g",
        "fats": "5g"
      }},
      "reasoning": "reason",
      "portion_size": "one serving",
      "prep_style": "fresh"
    }},
    "dinner": {{
      "dish_name": "name",
      "description": "description",
      "ingredients": ["ingredient"],
      "calories": 400,
      "macros": {{
        "protein": "20g",
        "carbs": "40g",
        "fats": "15g"
      }},
      "reasoning": "reason",
      "portion_size": "one serving",
      "prep_style": "cooked"
    }},
    "daily_totals": {{
      "calories": "1500 kcal (estimated)",
      "protein": "65g",
      "carbs": "175g",
      "fats": "50g"
    }},
    "hydration_target": "Individualized daily water goal"
  }}
}}
"""
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate structured, personalized meal plans. "
                        "Respect allergies and dietary restrictions."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=3000,
        )

        data = json.loads(completion.choices[0].message.content)
        return FullMealPlanResponse(**data)

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Comprehensive meal plan generation failed: {str(exc)}",
        )