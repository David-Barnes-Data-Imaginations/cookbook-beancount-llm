import json
import yaml

# CONFIG
INPUT_FILE = "data/json/final_train.json"  # Output from your Janitor script
OUTPUT_FILE = "data/yaml/human_edits_senior.yaml"

def str_presenter(dumper, data):
    """Configures YAML to use the '|' style for multi-line strings"""
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_presenter)

def main():
    try:
        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)
            
        with open(OUTPUT_FILE, 'w') as f:
            # allow_unicode=True ensures symbols like £ appear correctly
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
            
        print(f"✅ Converted to {OUTPUT_FILE}")
        print("👀 Open this file in your IDE. You will see nicely formatted text blocks!")
        
    except FileNotFoundError:
        print(f"❌ Could not find {INPUT_FILE}. Run janitor.py first!")

if __name__ == "__main__":
    main()