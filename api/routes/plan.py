import os
import json
from fastapi import APIRouter, HTTPException
from typing import Set
from api.schemas import GenerateRequest, GenerateResponse, Meal
from environment.day_env import DayEnv
from agent.ppo_agent import run_episode_with_plan
from rag.explainer import explain_meal_plan
from rag.embedder import load_vector_store
from stable_baselines3 import PPO

router = APIRouter()

# Load model and vector store once at startup
MODEL_PATH = "models/ppo_macromind"
VECTOR_STORE_PATH = "rag/vector_store"

# Global cache for model and vector store
_model = None
_vector_store = None


def load_model():
    """Load PPO model lazily."""
    global _model
    if _model is None:
        model_path = MODEL_PATH
        # Check with and without .zip
        if not os.path.exists(model_path + ".zip") and not os.path.exists(model_path):
            raise RuntimeError(f"Model not found at {MODEL_PATH}. Please train the model first.")
        # Load without environment for inference only
        try:
            _model = PPO.load(model_path)
        except Exception as e:
            # Try with explicit path
            _model = PPO.load(os.path.abspath(model_path))
    return _model


def load_vector_store_cached():
    """Load vector store lazily."""
    global _vector_store
    if _vector_store is None:
        if not os.path.exists(VECTOR_STORE_PATH):
            raise RuntimeError(f"Vector store not found at {VECTOR_STORE_PATH}")
        _vector_store = load_vector_store(VECTOR_STORE_PATH)
    return _vector_store


def time_to_step(time_str: str, wake_hour: int, wake_minute: int) -> int:
    """
    Convert a time string (e.g., "9:00am") to a step integer.
    
    Args:
        time_str: Time string like "9:00am"
        wake_hour: Wake hour (0-23)
        wake_minute: Wake minute (0-59)
    
    Returns:
        Step integer (0-based)
    """
    # Parse time string
    time_str = time_str.lower().strip()
    
    # Extract hour, minute, and am/pm
    if "am" in time_str:
        time_part = time_str.replace("am", "").strip()
        is_am = True
    elif "pm" in time_str:
        time_part = time_str.replace("pm", "").strip()
        is_am = False
    else:
        raise ValueError(f"Invalid time format: {time_str}. Expected format like '9:00am' or '2:30pm'")
    
    # Parse hour and minute
    parts = time_part.split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time format: {time_str}. Expected format like '9:00am' or '2:30pm'")
    
    hour = int(parts[0])
    minute = int(parts[1])
    
    # Convert to 24-hour format
    if is_am and hour == 12:
        hour = 0
    elif not is_am and hour != 12:
        hour += 12
    
    # Calculate total minutes from midnight
    total_minutes = hour * 60 + minute
    
    # Calculate wake time in minutes
    wake_minutes = wake_hour * 60 + wake_minute
    
    # Calculate step (each step is 30 minutes)
    step = (total_minutes - wake_minutes) // 30
    
    # Clamp to valid range [0, 29]
    return max(0, min(step, 29))


def time_range_to_steps(start: str, end: str, wake_hour: int, wake_minute: int) -> Set[int]:
    """
    Convert a time range (e.g., "9:00am" to "11:00am") to all steps within it.
    
    Args:
        start: Start time string like "9:00am"
        end: End time string like "11:00am"
        wake_hour: Wake hour (0-23)
        wake_minute: Wake minute (0-59)
    
    Returns:
        Set of step integers
    """
    start_step = time_to_step(start, wake_hour, wake_minute)
    end_step = time_to_step(end, wake_hour, wake_minute)
    
    # If end_step < start_step, they may span midnight or the user reversed them
    if end_step < start_step:
        end_step = start_step
    
    return set(range(start_step, end_step + 1))


@router.post("/generate")
async def generate_meal_plan(request: GenerateRequest) -> GenerateResponse:
    """
    Generate a meal plan for the day based on user's schedule and preferences.
    
    Expects:
    - busy_blocks: List of TimeBlock objects (e.g., meetings, commitments)
    - workout_blocks: List of TimeBlock objects (e.g., exercise times)
    - user_prefs: Optional user preferences (wake time, meal times, macro targets)
    
    Returns:
    - GenerateResponse with complete meal plan, macros, hunger curve, and explanation
    """
    try:
        # Load model and vector store
        model = load_model()
        vector_store = load_vector_store_cached()
        
        # Extract user preferences or use defaults
        if request.user_prefs:
            prefs = request.user_prefs
        else:
            # Load default preferences
            prefs_path = "data/user_prefs.json"
            if os.path.exists(prefs_path):
                with open(prefs_path, "r") as f:
                    prefs_data = json.load(f)
                from api.schemas import UserPrefs, MacroTargets
                targets = MacroTargets(**prefs_data.get("targets", {}))
                prefs = UserPrefs(
                    wake_time=prefs_data.get("wake_time", "6:00am"),
                    targets=targets
                )
            else:
                raise HTTPException(status_code=400, detail="No user preferences provided and default prefs not found")
        
        # Parse wake time
        wake_time_str = prefs.wake_time.lower().replace("am", "").replace("pm", "").strip()
        wake_parts = wake_time_str.split(":")
        wake_hour = int(wake_parts[0])
        wake_minute = int(wake_parts[1]) if len(wake_parts) > 1 else 0
        if "pm" in prefs.wake_time.lower() and wake_hour != 12:
            wake_hour += 12
        elif "am" in prefs.wake_time.lower() and wake_hour == 12:
            wake_hour = 0
        
        # Create environment
        env = DayEnv(
            wake_hour=wake_hour,
            wake_minute=wake_minute,
        )
        
        # Override macro targets
        env.target_calories = prefs.targets.calories
        env.target_protein = prefs.targets.protein
        env.target_carbs = prefs.targets.carbs
        env.target_fat = prefs.targets.fat
        
        # Convert time blocks to steps and set on environment
        busy_steps: Set[int] = set()
        for block in request.busy_blocks:
            busy_steps.update(time_range_to_steps(block.start, block.end, wake_hour, wake_minute))
        
        workout_steps: Set[int] = set()
        for block in request.workout_blocks:
            workout_steps.update(time_range_to_steps(block.start, block.end, wake_hour, wake_minute))
        
        # Reset environment
        obs, info = env.reset()
        
        # Override busy_blocks and workout_steps with user input
        env.generated_busy_blocks = sorted(busy_steps)
        env.busy_blocks = sorted(busy_steps)
        env.workout_steps = sorted(workout_steps)
        
        # Run episode to generate meal plan without resetting the environment again,
        # so the user's busy/workout blocks remain in effect for planning.
        meal_plan = run_episode_with_plan(model, env, reset=False)
        
        # Generate explanation with fallback if Ollama is not available
        try:
            explanation = explain_meal_plan(meal_plan, vector_store)
        except Exception as e:
            # Fallback explanation if Ollama is not running
            meals_str = ", ".join([f"{m['food']}" for m in meal_plan["meals"]])
            totals = meal_plan["totals"]
            explanation = (
                f"Generated a meal plan with {len(meal_plan['meals'])} meals/snacks: "
                f"{meals_str}. "
                f"Daily macros: {totals['calories']}cal, {totals['protein']}g protein, "
                f"{totals['carbs']}g carbs, {totals['fat']}g fat. "
                f"(Note: Full explanation requires Ollama to be running. "
                f"Error: {str(e)[:100]})"
            )
        
        # Convert meals to Meal objects
        meals = [
            Meal(
                time=m["time"],
                type=m["type"],
                food=m["food"],
                calories=m["calories"],
                protein=m["protein"],
                carbs=m["carbs"],
                fat=m["fat"]
            )
            for m in meal_plan["meals"]
        ]
        
        # Build response
        response = GenerateResponse(
            schedule_type=meal_plan["schedule_type"],
            busy_blocks=meal_plan["busy_blocks"],
            workout_blocks=meal_plan["workout_blocks"],
            meals=meals,
            totals=meal_plan["totals"],
            targets=meal_plan["targets"],
            hunger_curve=meal_plan["hunger_curve"],
            explanation=explanation
        )
        
        return response
        
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating meal plan: {str(e)}")
