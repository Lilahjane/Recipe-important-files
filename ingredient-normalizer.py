import json
import logging
import sys
import re
from fractions import Fraction
from ingredient_parser import parse_ingredient
from ingredient_parser.dataclasses import IngredientAmount, CompositeIngredientAmount

# --- LOGGING SETUP ---
logging.basicConfig(stream=sys.stdout)
# Only show foundation-foods logs, not all the preprocessing logs
logging.getLogger("ingredient-parser").setLevel(logging.WARNING)
logging.getLogger("ingredient-parser.foundation-foods").setLevel(logging.WARNING)

OUTPUT_FILE = r"D:\just_mealplanner\source\normalized-ingredients.json"
INPUT_FILE = r"D:\just_mealplanner\source\ingredients.json"
# --- UTILITY FUNCTIONS ---
def safe_quantity_to_float(quantity):
    """
    Safely convert quantity to float, handling Fractions and string quantities.
    Extracts numeric part if string contains non-numeric characters.
    """
    try:
        # If it's already a number or Fraction, convert directly
        return float(quantity)
    except (ValueError, TypeError):
        # If it's a string with quotes or other chars, try to extract numeric part
        if isinstance(quantity, str):
            # Use regex to extract the first numeric value (including decimals/fractions)
            match = re.search(r'[\d.]+', quantity)
            if match:
                try:
                    return float(match.group())
                except ValueError:
                    return 0.0
            # If no numeric part found, return 0
            return 0.0
        return 0.0

# --- PRE-PROCESSING LAYER ---
def custom_pre_processor(ingredient_list):
    """
    Filters out section headers and non-ingredient metadata
    found in the sources (e.g., 'FOR THE GARLIC BUTTER' or 'la veille').
    """
    cleaned_list = []
    headers_to_skip = ["FOR THE", "la veille", "Le lendemain", "Confection"]
    
    for line in ingredient_list:
        # Skip empty lines or lines that are clearly section headers
        if not line or any(header in line for header in headers_to_skip):
            continue
        cleaned_list.append(line.strip())
    return cleaned_list

# --- MAIN LOGIC ---
def process_recipes(input_file):
    # Load the source JSON mirroring ingredients_json
    with open(input_file, 'r', encoding='utf-8') as f:
        recipes = json.load(f)

    output_data = []

    for recipe in recipes:
        recipe_entry = {
            "recipe_id": recipe.get("id"),
            "recipe_title": recipe.get("title"),
            "ingredients": []
        }

        # Step 1: Pre-process the list of strings
        cleaned_ingredients = custom_pre_processor(recipe.get("ingredients", []))

        for sentence in cleaned_ingredients:
            # Step 2: Use the tool to parse the string
            parsed = parse_ingredient(sentence, foundation_foods=True, volumetric_units_system="us_customary")

            # --- DEBUG OUTPUT ---
            # Handle Unicode characters for Windows console
            try:
                print(f"\n=== PARSING: {sentence} ===")
            except UnicodeEncodeError:
                print(f"\n=== PARSING: (Unicode characters present) ===")
            print(f"Type of parsed.foundation_foods: {type(parsed.foundation_foods)}")
            if parsed.foundation_foods:
                print(f"Foundation Food: {parsed.foundation_foods[0].text} (fdc_id: {parsed.foundation_foods[0].fdc_id})")

            # Step 3: Extract Canonical Ingredient (FDC Foundation Food)
            foundation_food = parsed.foundation_foods[0] if parsed.foundation_foods else None

            canonical_ingredient = None
            if foundation_food:
                canonical_ingredient = {
                    "fdc_id": foundation_food.fdc_id,
                    "canonical_name": foundation_food.text,
                    "confidence": foundation_food.confidence,
                    "category": foundation_food.category,
                    "data_type": foundation_food.data_type,
                    "fdc_url": foundation_food.url
                }

            # Step 4: Extract Preparation (separate from ingredient identity)
            preparation = parsed.preparation.text if parsed.preparation else None

            # Step 5: Process Amount Data (Composite and Simple)
            amount_data = None
            if parsed.amount:
                amt = parsed.amount[0]  # Handle first amount (recipes typically have one)

                if isinstance(amt, CompositeIngredientAmount):
                    # Extract individual components from composite amount
                    components = []
                    for component in amt.amounts:
                        components.append({
                            "quantity": safe_quantity_to_float(component.quantity),
                            "unit": str(component.unit),
                            "quantity_fraction": str(component.quantity)
                        })

                    # Pre-calculate metric total
                    try:
                        combined_qty = amt.combined()
                        metric_ml = combined_qty.to("ml").magnitude
                    except:
                        metric_ml = 0.0

                    amount_data = {
                        "type": "composite",
                        "components": components,
                        "join_text": getattr(amt, 'join', 'and'),
                        "metric_ml": metric_ml,
                        "is_approximate": getattr(amt, 'RANGE', False)
                    }
                else:  # Simple IngredientAmount
                    # Pre-calculate metric value
                    try:
                        metric_ml = amt.convert_to("ml").quantity
                    except:
                        metric_ml = 0.0

                    amount_data = {
                        "type": "simple",
                        "components": [{
                            "quantity": safe_quantity_to_float(amt.quantity),
                            "unit": str(amt.unit),
                            "quantity_fraction": str(amt.quantity)
                        }],
                        "join_text": None,
                        "metric_ml": metric_ml,
                        "is_approximate": getattr(amt, 'RANGE', False)
                    }

            # Step 6: Create Recipe Ingredient Object (Database Schema)
            recipe_ingredient = {
                "raw_text": parsed.sentence,
                "preparation": preparation,
                "canonical_ingredient": canonical_ingredient,
                "amount_data": amount_data,
                "standard_names": [n.text for n in parsed.name],
                "comment": parsed.comment.text if parsed.comment else None,
                "purpose": parsed.purpose.text if parsed.purpose else None,
                "size_modifier": parsed.size.text if parsed.size else None
            }

            recipe_entry["ingredients"].append(recipe_ingredient)

        output_data.append(recipe_entry)

    return output_data

if __name__ == "__main__":
    try:
        # Assumes your file is named 'ingredients.json'
        final_json = process_recipes(INPUT_FILE) 

        # Custom encoder to handle Fraction objects
        class FractionEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, Fraction):
                    return float(obj)
                return super().default(obj)

        # Write to output file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_json, f, indent=2, cls=FractionEncoder)

        print("[OK] Output saved to output.json")
    except FileNotFoundError:
        print("Error: Please create 'ingredients.json' in this directory.")
