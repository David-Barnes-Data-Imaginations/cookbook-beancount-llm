import pandas as pd
import re
import json

# Input/Output
INPUT_FILE = "refined_data.json" # Or whatever your latest export is
OUTPUT_FILE = "ready_for_unsloth.json"

def clean_senior_output(text):
    # 1. REMOVE THE <think> BLOCK
    # We only want the final XML result
    if "<accounting_entry>" in text:
        # Split and take everything after the think block
        text = text.split("<accounting_entry>")[-1]
        text = "<accounting_entry>" + text
    
    # 2. REMOVE "REVIEWER VOICE"
    # We replace "Reviewer" phrases with neutral "Reasoning" phrases
    replacements = [
        (r"CRITICAL CORRECTION:", "Note:"),
        (r"I have standardized.*?:", "Standardized format:"),
        (r"I have spotted a critical discrepancy:", "Correction:"),
        (r"The Junior Accountant correctly identified", "Identified"),
        (r"Junior Accountant", "Agent"),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # 3. FIX THE SPACE BUG (Assets: Lloyds -> Assets:Lloyds)
    # Beancount prefers no spaces after the first colon usually
    text = re.sub(r'(Assets|Liabilities|Expenses|Income|Equity):\s+', r'\1:', text)

    return text.strip()

def main():
    # Load Data (Handling the Label Studio Export structure)
    try:
        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)
            
        print(f"🧹 Janitor starting on {len(data)} records...")
        
        training_pairs = []
        
        for task in data:
            try:
                # Extract Prompt
                prompt = task['data']['prompt']
                
                # Extract Response (The Senior's Annotation)
                # Note: Label Studio puts this in 'annotations' -> 'result' -> 'value' -> 'text'
                raw_response = task['annotations'][0]['result'][0]['value']['text'][0]
                
                # CLEAN IT
                clean_response = clean_senior_output(raw_response)
                
                training_pairs.append({
                    "prompt": prompt,
                    "response": clean_response
                })
            except Exception as e:
                print(f"⚠️ Skipping row: {e}")
                continue

        # Save as the flat format Unsloth likes
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(training_pairs, f, indent=2)
            
        print(f"✨ Done! Saved {len(training_pairs)} clean pairs to {OUTPUT_FILE}")
        print("🚀 You can load this directly into Unsloth now!")

    except FileNotFoundError:
        print(f"❌ Could not find {INPUT_FILE}")

if __name__ == "__main__":
    main()