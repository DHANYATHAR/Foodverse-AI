from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers.food_recognition import router as food_recognition_router
from backend.routers.food_preprocessing import router as food_preprocessing_router
from backend.routers.hygiene_monitor import router as hygiene_monitor_router
from backend.routers.kitchen_assistant import router as kitchen_assistant_router
from backend.routers.meal_planner import router as meal_planner_router


app = FastAPI(title="Foodverse AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(food_recognition_router)
app.include_router(food_preprocessing_router)
app.include_router(hygiene_monitor_router)
app.include_router(kitchen_assistant_router,
    prefix="/api/kitchen-assistant",
    tags=["Kitchen Assistant"]
)
app.include_router(
    meal_planner_router,
    prefix="/api/meal-planner",
    tags=["Personalized Meal Planner"]
)

@app.get("/")
def home():
    return {
        "message": "Welcome to Foodverse AI!",
        "status": "Backend is running"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
