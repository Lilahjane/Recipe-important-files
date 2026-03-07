import json

# --- CONFIGURATION ---
INPUT_FILE = r"D:\just_mealplanner\source\recipes-withID.json"
OUTPUT_FILE = r"D:\just_mealplanner\source\ingredients.json"

# --- FUNCTION 1: THE LOADER ---
def load_entire_json(path):
    """Opens the file and returns the full JSON dictionary."""
    with open(path, 'r', encoding='utf-8') as file:
        return json.load(file)

# --- FUNCTION 2: THE SAVER ---
def save_new_json(path, data_to_save):
    """Writes the new list/dict to a file."""
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data_to_save, file, indent=2)

# --- FUNCTION 3: THE TRANSFORMATION ---
def extract_recipes_with_ingredients(entire_json_dictionary):
    """Filters for recipes that actually have ingredients."""
    
    all_recipes_list = entire_json_dictionary.get('results', [])
    valid_recipes_found = []

    for single_recipe_object in all_recipes_list:
        # Get the ingredients list (default to empty list if missing)
        ingredients_list = single_recipe_object.get('ingredients', [])

        # Logic: If the list is NOT empty...
        if ingredients_list:
            # Create a clean version of the recipe object
            clean_recipe = {
                "id": single_recipe_object.get('id'),
                "title": single_recipe_object.get('title'),
                "url": single_recipe_object.get('url'),
                "ingredients": ingredients_list
            }
            # Add this clean object to our collector list
            valid_recipes_found.append(clean_recipe)
            
    return valid_recipes_found

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # 1. Load the big file
    raw_data = load_entire_json(INPUT_FILE)
    
    # 2. Extract only what we want
    processed_data = extract_recipes_with_ingredients(raw_data)
    
    # 3. Save the new file
    save_new_json(OUTPUT_FILE, processed_data)
    
    print(f"Success! Extracted {len(processed_data)} recipes with ingredients.")