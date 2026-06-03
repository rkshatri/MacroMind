import json
import random
import os
from typing import List, Dict, Optional


class FoodLibrary:
	"""Simple food lookup and scoring helper.

	Responsibilities:
	- load pantry.json into memory
	- precompute total macros per food item
	- filter foods by meal type
	- pick the best food given remaining macros
	"""

	def __init__(self, pantry_path: str, *,
				 target_calories: int = 2400,
				 target_protein: int = 150,
				 target_carbs: int = 200,
				 target_fat: int = 65):
		# load pantry
		path = pantry_path
		if not os.path.isabs(path):
			# make relative to repository root if needed
			path = os.path.join(os.getcwd(), path)

		with open(path, "r", encoding="utf-8") as fh:
			payload = json.load(fh)

		self.foods: List[Dict] = payload.get("foods", [])

		# store macro targets for penalty calculations
		self.target_calories = target_calories
		self.target_protein = target_protein
		self.target_carbs = target_carbs
		self.target_fat = target_fat

		# precompute totals so callers don't need to multiply
		for f in self.foods:
			qty = f.get("default_quantity", 1) or 1
			f["total_calories"] = float(f.get("calories_per_unit", 0)) * qty
			f["total_protein"] = float(f.get("protein_per_unit", 0)) * qty
			f["total_carbs"] = float(f.get("carbs_per_unit", 0)) * qty
			f["total_fat"] = float(f.get("fat_per_unit", 0)) * qty

	def get_foods_by_type(self, meal_type: str) -> List[Dict]:
		"""Return foods matching `meal_type` or marked as 'any'.

		Accepts 'breakfast', 'snack', or 'any'.
		"""
		mt = meal_type.lower()
		if mt == "breakfast":
			# During breakfast period, only breakfast foods should be considered
			return [f for f in self.foods if f.get("meal_type", "any") == "breakfast"]

		# For other meal types (snack/any), allow items marked as the requested
		# type or as 'any'. Snacks remain available alongside 'any' items.
		return [f for f in self.foods if f.get("meal_type", "any") in (mt, "any")]

	def get_best_match(self, cal_remaining: float, protein_remaining: float,
					   carbs_remaining: float, fat_remaining: float,
					   meal_type: str) -> Optional[Dict]:
		"""Score eligible foods and return the best-scoring item.

		Scoring heuristic follows the user's specification: reward contribution
		toward unmet macros and penalize overshooting already-met macros.
		"""
		candidates = self.get_foods_by_type(meal_type)
		if not candidates:
			return None

		best = None
		best_score = -float("inf")

		for f in candidates:
			score = 0.0

			# calories
			food_cal = f.get("total_calories", 0.0)
			if cal_remaining > 0:
				score += min(food_cal, cal_remaining) / (cal_remaining or 1)
			else:
				score -= food_cal / max(1.0, self.target_calories)

			# protein
			food_p = f.get("total_protein", 0.0)
			if protein_remaining > 0:
				score += min(food_p, protein_remaining) / (protein_remaining or 1)
			else:
				score -= food_p / max(1.0, self.target_protein)

			# carbs
			food_c = f.get("total_carbs", 0.0)
			if carbs_remaining > 0:
				score += min(food_c, carbs_remaining) / (carbs_remaining or 1)
			else:
				score -= food_c / max(1.0, self.target_carbs)

			# fat
			food_f = f.get("total_fat", 0.0)
			if fat_remaining > 0:
				score += min(food_f, fat_remaining) / (fat_remaining or 1)
			else:
				score -= food_f / max(1.0, self.target_fat)

			# small tie-breaker: prefer lower calorie option if scores equal
			if score > best_score:
				best_score = score
				best = f
			elif score == best_score and best is not None:
				# choose the lower calorie option to avoid massive overshoots
				if f.get("total_calories", 0) < best.get("total_calories", 0):
					best = f

		return best

	def get_meal_type_for_step(self, current_step: int, total_steps: int) -> str:
		"""Return 'breakfast' for the first 8 steps, otherwise 'any'."""
		return "breakfast" if current_step < 8 else "any"

	def sample_random(self, meal_type: str) -> Optional[Dict]:
		c = self.get_foods_by_type(meal_type)
		if not c:
			return None
		return random.choice(c)


__all__ = ["FoodLibrary"]

