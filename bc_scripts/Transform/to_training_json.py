import yaml
import json

INPUT_FILE = "human_edits.yaml"
OUTPUT_FILE = "final_train.json" # Load THIS into Unsloth

def main():
    try:
        print(f"📖 Reading {INPUT_FILE}...")
        with open(INPUT_FILE, 'r') as f:
            data = yaml.safe_load(f)
            
        print(f"📦 Converting {len(data)} records to strict JSON...")
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"✅ Success! Saved to {OUTPUT_FILE}")
        print("🚀 You are ready to train!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()