import json
import yaml

# CONFIG
INPUT_FILE = "data/json/old_training_data.json"
OUTPUT_FILE = "data/yaml/old_training_data_readable.yaml"

# Function to clean tokenizer artifacts recursively
def clean_text(obj):
    if isinstance(obj, str):
        # specific unsloth/mistral artifact cleaning
        s = obj.replace('\u010a', '\n').replace('\u0120', ' ')
        # remove carriage returns
        s = s.replace('\r', '')
        # remove trailing spaces from each line to encourage block style
        s = '\n'.join([line.rstrip() for line in s.split('\n')])
        return s
    elif isinstance(obj, list):
        return [clean_text(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: clean_text(v) for k, v in obj.items()}
    return obj

class IndentedDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentedDumper, self).increase_indent(flow, False)

def str_presenter(dumper, data):
    """Configures YAML to use the '|' style for multi-line strings"""
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_presenter, Dumper=IndentedDumper)

def main():
    try:
        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)

        cleaned_data = clean_text(data)

        with open(OUTPUT_FILE, 'w') as f:
            # use the custom dumper to ensure our representer is used
            yaml.dump(cleaned_data, f, Dumper=IndentedDumper, allow_unicode=True, sort_keys=False, default_flow_style=False, width=120)
            
        print(f"✅ Converted to {OUTPUT_FILE}")
        print("👀 Open this file in your IDE. You will see nicely formatted text blocks!")
        
    except FileNotFoundError:
        print(f"❌ Could not find {INPUT_FILE}. Please check the file path!")

if __name__ == "__main__":
    main()