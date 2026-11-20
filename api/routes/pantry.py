import json
import os
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()

PANTRY_PATH = "data/foods/pantry.json"


def get_pantry_path() -> str:
    """Get the absolute path to pantry.json."""
    if os.path.isabs(PANTRY_PATH):
        return PANTRY_PATH
    return os.path.join(os.getcwd(), PANTRY_PATH)


@router.get("/pantry")
async def get_pantry() -> Dict[str, Any]:
    """
    Read and return the pantry.json file.
    
    Returns:
    - Dictionary containing the pantry data (foods list)
    """
    try:
        pantry_file = get_pantry_path()
        if not os.path.exists(pantry_file):
            raise HTTPException(status_code=404, detail=f"Pantry file not found at {pantry_file}")
        
        with open(pantry_file, "r", encoding="utf-8") as f:
            pantry_data = json.load(f)
        
        return pantry_data
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error parsing pantry.json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading pantry: {str(e)}")


@router.post("/pantry")
async def update_pantry(pantry_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Write updated pantry data to disk.
    
    Expects:
    - Dictionary containing pantry data (foods list)
    
    Returns:
    - Success message
    """
    try:
        pantry_file = get_pantry_path()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(pantry_file), exist_ok=True)
        
        # Write to file
        with open(pantry_file, "w", encoding="utf-8") as f:
            json.dump(pantry_data, f, indent=2, ensure_ascii=False)
        
        return {"message": "Pantry updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating pantry: {str(e)}")
