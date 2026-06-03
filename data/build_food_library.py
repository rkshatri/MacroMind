from usda_fdc import FdcClient
import os

api_key = os.getenv('FDC_API_KEY')
if api_key is None:
    raise RuntimeError("FDC_API_KEY environment variable is not set")

client = FdcClient(api_key=api_key)

def fetch_foods(query):
    
    search_results = client.search(query)
    results = [f.fdc_id for f in search_results.foods[:3]]

    return results

def extract_details(fdc_id, serving_size=100, num_servings=1):

    food = client.get_food(fdc_id)

    # USDA is per 100g, so multiply by serving_grams / 100
    serving_proportion = food.serving_size / 100.0 if food.serving_size else serving_size / 100
    serving_proportion *= num_servings

    food_details = {
        "name": food.description,
        "brand": food.brand_name,
        "fdc_id": fdc_id,
        "serving_size": food.serving_size,
        "calories": 0.0,
        "protein": 0.0,
        "carbs": 0.0,
        "fat": 0.0,
    }

    for nutrient in food.nutrients:

        name = nutrient.name.lower()
        if "energy" in name:
            food_details["calories"] = int(nutrient.amount * serving_proportion)
        elif "protein" in name:
            food_details["protein"] = int(nutrient.amount * serving_proportion)
    
        elif "carb" in name:
            food_details["carbs"] = int(nutrient.amount * serving_proportion)
    
        elif "fat" in name:
            food_details["fat"] = int(nutrient.amount * serving_proportion)
    
    return food_details

for id in fetch_foods("egg"):
    print(extract_details(id))
    


