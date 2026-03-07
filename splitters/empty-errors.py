import json
from pathlib import Path

# Use a Raw String (r"") for Windows paths to avoid backslash errors
INPUT_FILE_PATH = r"D:\just_mealplanner\source\recipes-withID.json"
OUTPUT_FILE_PATH = r"D:\just_mealplanner\source\empties-and-uglies.json"

def process_recipes():
    # 1. OPEN & LOAD
    with open(INPUT_FILE_PATH, 'r', encoding='utf-8') as file:
        # 'entire_json_dictionary' holds EVERYTHING in the file
        entire_json_dictionary = json.load(file)
        

    # 2. ACCESS THE ARRAY
    # 'all_recipes_list' holds the array/list found inside "results"
    all_recipes_list = entire_json_dictionary.get('results', [])
    
    # this array will hold all the recipes with empty ingredients lists and their error values
    empties_and_uglies = []

    # 3. LOOP THROUGH INDIVIDUAL OBJECTS
    for single_recipe_object in all_recipes_list:
     
        # Pulling specific values
        recipe_id = single_recipe_object.get('id')
        error_val = single_recipe_object.get('error')
        ingredients_val = single_recipe_object.get('ingredients', [])
        url_val = single_recipe_object.get('url')
        
            
        # if ingredients is empty that means the recipe is an empty but error val could be null or have something in it so i need to pull any recipe with an empty ingredients list and then check if the error val is null or not and save them with recipe id url and error no matter null empty or otherwise in a new json file 
        
        if not ingredients_val:
            # Create a new dictionary for this recipe with only the required fields
            empty_object = {
                "id": recipe_id,
                "url": url_val,
                "error": error_val
            }
            empties_and_uglies.append(empty_object)
 


    # 4. SAVE CHANGES
    # We save 'entire_json_dictionary' because it contains the 
    # updated 'all_recipes_list' inside it.
    with open(OUTPUT_FILE_PATH, 'w', encoding='utf-8') as file:
        json.dump(empties_and_uglies, file, indent=2)

if __name__ == "__main__":
    process_recipes()