import json
import os
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()

PREFS_PATH = "data/user_prefs.json"


def get_prefs_path() -> str:
    """Get the absolute path to user_prefs.json."""
    if os.path.isabs(PREFS_PATH):
        return PREFS_PATH
    return os.path.join(os.getcwd(), PREFS_PATH)


@router.get("/prefs")
async def get_prefs() -> Dict[str, Any]:
    """
    Read and return user_prefs.json.
    
    Returns:
    - Dictionary containing user preferences (wake time, meal times, macro targets)
    """
    try:
        prefs_file = get_prefs_path()
        if not os.path.exists(prefs_file):
            raise HTTPException(status_code=404, detail=f"User preferences file not found at {prefs_file}")
        
        with open(prefs_file, "r", encoding="utf-8") as f:
            prefs_data = json.load(f)
        
        return prefs_data
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error parsing user_prefs.json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading preferences: {str(e)}")


@router.post("/prefs")
async def update_prefs(prefs_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Write updated user preferences to disk.
    
    Expects:
    - Dictionary containing preferences (wake_time, targets)
    
    Returns:
    - Success message
    """
    try:
        prefs_file = get_prefs_path()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(prefs_file), exist_ok=True)
        
        # Write to file
        with open(prefs_file, "w", encoding="utf-8") as f:
            json.dump(prefs_data, f, indent=2, ensure_ascii=False)
        
        return {"message": "Preferences updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating preferences: {str(e)}")
