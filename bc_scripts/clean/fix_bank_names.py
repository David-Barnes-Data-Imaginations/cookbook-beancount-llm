import json
import re

# --- CONFIGURATION ---
INPUT_FILE = "ready_for_labeling.json"
OUTPUT_FILE = "ready_for_labeling_FIXED.json"

# The EXACT name you want to appear in your dataset
CORRECT_BANK_ACCOUNT = "Assets:US:BofA:Checking"

def fix_xml_entry(xml_text):
    """
    Finds the line with a negative amount inside <entry> and enforces the bank account name.
    """
    lines = xml_text.split('\n')
    fixed_lines = []
    
    in_entry_block = False
    
    for line in lines:
        if "<entry>" in line:
            in_entry_block = True
            fixed_lines.append(line)
            continue
        
        if "</entry>" in line:
            in_entry_block = False
            fixed_lines.append(line)
            continue
            
        if in_entry_block:
            # Check if this line has a NEGATIVE amount (e.g., "-59.34 USD")
            # We look for a minus sign followed by digits
            if re.search(r'-\d+\.\d+\s+USD', line):
                # EXTRACT the amount part (e.g., "   -59.34 USD")
                # We want to preserve the amount but replace the account name
                amount_match = re.search(r'(\s+)(.*?)(-\d+\.\d+\s+USD)', line)
                
                if amount_match:
                    indentation = "  " # Force standard 2-space indentation
                    amount_part = amount_match.group(3) # The "-59.34 USD" part
                    
                    # CONSTRUCT the perfect line
                    new_line = f"{indentation}{CORRECT_BANK_ACCOUNT}      {amount_part}"
                    fixed_lines.append(new_line)
                else:
                    # Fallback if regex fails (rare)
                    fixed_lines.append(line)
            else:
                # This is the Payee line or the Expense line (positive), keep it as is
                fixed_lines.append(line)
        else:
            # Outside entry block (reasoning/plan), keep as is
            fixed_lines.append(line)
            
    return "\n".join(fixed_lines)

def run_fix():
    print(f"🔧 Reading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r') as f:
        data = json.load(f)
    
    count = 0
    for task in data:
        # Navigate to the annotation text
        try:
            # Label Studio structure is deep!
            annotation = task['annotations'][0]['result'][0]['value']['text'][0]
            
            # Run the fix
            fixed_xml = fix_xml_entry(annotation)
            
            # Save it back
            task['annotations'][0]['result'][0]['value']['text'][0] = fixed_xml
            count += 1
        except Exception as e:
            print(f"Skipping task due to error: {e}")

    print(f"✅ Fixed {count} records.")
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"💾 Saved to {OUTPUT_FILE}")
    print("🚀 Import this new file into Label Studio (Delete the old project first to be clean!)")

if __name__ == "__main__":
    run_fix()