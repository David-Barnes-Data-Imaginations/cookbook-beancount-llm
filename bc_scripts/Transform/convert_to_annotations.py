import json
import os

# --- CONFIGURATION ---
INPUT_FILE = "training_data.json"       # Your current file (with predictions)
OUTPUT_FILE = "ready_for_labeling.json" # The new file (with annotations)

def clean_nans(obj):
    """
    Recursively replace 'NaN' values with None (which becomes null in JSON)
    or an empty string, because SQLite hates NaNs.
    """
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None  # Becomes null in JSON
    elif isinstance(obj, dict):
        return {k: clean_nans(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nans(v) for v in obj]
    return obj
    
def convert_predictions_to_annotations():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: Could not find '{INPUT_FILE}'")
        return

    print(f"📂 Reading {INPUT_FILE}...")
    
    with open(INPUT_FILE, 'r') as f:
        data = json.load(f)
    
    converted_data = []
    count = 0

    for task in data:
        # Check if this task actually has predictions
        if 'predictions' in task and len(task['predictions']) > 0:
            
            # 1. Grab the useful info from the Prediction
            # We take the first prediction (since you only have one per task)
            prediction = task['predictions'][0]
            result_content = prediction['result']
            model_ver = prediction.get('model_version', "GPT-OSS-20B")
            
            # 2. Build the new structure with 'annotations'
            new_task = {
                "data": task['data'], # Keep the input data (prompt, id, etc)
                "annotations": [{
                    "result": result_content,
                    "was_cancelled": False,
                    "ground_truth": False,
                    "model_version": model_ver
                }]
            }
            
            converted_data.append(new_task)
            count += 1
        else:
            # If there was no prediction, just keep the data so you can do it manually
            print(f"⚠️ Warning: Task {task['data'].get('transaction_id')} had no predictions. Keeping as empty task.")
            converted_data.append({"data": task['data']})

    # 3. Save the new file
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(converted_data, f, indent=2)
        
    print(f"✅ Success! Converted {count} tasks.")
    print(f"💾 Saved to: {OUTPUT_FILE}")
    print("🚀 You can now drag this new file into Label Studio.")

if __name__ == "__main__":
    convert_predictions_to_annotations()