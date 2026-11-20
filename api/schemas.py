from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class TimeBlock(BaseModel):
    """A time block represented as start and end time strings."""
    start: str  # "9:00am"
    end: str    # "11:00am"


class MacroTargets(BaseModel):
    """Macro targets for the day."""
    calories: int
    protein: int
    carbs: int
    fat: int


class UserPrefs(BaseModel):
    """User preferences for meal planning."""
    wake_time: str  # "6:00am"
    targets: MacroTargets


class GenerateRequest(BaseModel):
    """Request to generate a meal plan."""
    busy_blocks: List[TimeBlock] = []
    workout_blocks: List[TimeBlock] = []
    user_prefs: Optional[UserPrefs] = None


class Meal(BaseModel):
    """A single meal or snack in the plan."""
    time: str
    type: str  # "snack" or "meal"
    food: str
    calories: float
    protein: float
    carbs: float
    fat: float


class GenerateResponse(BaseModel):
    """Response containing the generated meal plan."""
    schedule_type: str
    busy_blocks: List[str]
    workout_blocks: List[str]
    meals: List[Meal]
    totals: Dict[str, float]
    targets: Dict[str, float]
    hunger_curve: List[float]
    explanation: str