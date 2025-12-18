mport pandas as pd
import re
import json

# Input/Output
INPUT_FILE = "refined_data.json" # Or whatever your latest export is
OUTPUT_FILE = "final_post_clean.json"

def clean_senior_output(text):
    # 1. FIND THE XML BLOCK
    # We want exactly what is between <accounting_entry> and </accounting_entry>
    pattern = r"(<accounting_entry>.*?</accounting_entry>)"
    
    match = re.search(pattern, text, flags=re.DOTALL)
    
    if match:
        clean_xml = match.group(1)
    else:
        # Fallback if tags are missing (rare)
        clean_xml = text

    # 2. FIX THE SPACE BUG (Assets: Lloyds -> Assets:Lloyds)
    clean_xml = re.sub(r'(Assets|Liabilities|Expenses|Income|Equity):\s+', r'\1:', clean_xml)

    return clean_xml.strip()

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