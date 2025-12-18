import os
import json
import requests
from tqdm import tqdm
import re
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting
import anthropic

load_dotenv()

# ================= CONFIGURATION =================
INPUT_FILE = "training_data.json"   # The file from your Junior Agent
OUTPUT_FILE = "final_train.json"   # The file for Label Studio
LLM_API_URL = "http://localhost:1234/v1/chat/completions"
# Ideally use Qwen-2.5-Coder-7B-Instruct or similar strict model here
MODEL_NAME = "local-model" 
PROVIDER = os.getenv("SENIOR_ACCOUNTANT_PROVIDER", "lm-studio")
PROJECT_ID = "persona-forge-470514" # Extracted from key filename implication, but rely on creds mostly
LOCATION = "us-central1"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

def init_google():
    vertexai.init(location=LOCATION)

def call_google_gemini(system_instruction, prompt):
    model = GenerativeModel(
        "gemini-2.5-pro",
        system_instruction=[system_instruction]
    )
    responses = model.generate_content(
        [prompt],
        generation_config={
            "max_output_tokens": 2000,
            "temperature": 0.1,
        },
        safety_settings=[
            SafetySetting(
                category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            ),
            SafetySetting(
                category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            ),
            SafetySetting(
                category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            ),
            SafetySetting(
                category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            ),
        ],
        stream=False,
    )
    return responses.text 

def call_anthropic_claude(system_instruction, prompt):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=system_instruction,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text

# ================= SENIOR ACCOUNTANT LOGIC =================
def critique_and_fix(prompt, junior_xml):
    """
    Asks the Senior Model to review and fix the Junior's work.
    """
    review_prompt = f"""You are a Senior Accounting Auditor. 
Your job is to review the work of a Junior Accountant. The Junior AI Accountant will be trained on the output of the data you have checked and adjusted.

--- CONTEXT & TRANSACTION ---
{prompt}

--- JUNIOR ACCOUNTANT'S ATTEMPT ---
{junior_xml}

--- YOUR TASK ---
1. **Source Account Check:** Look at the 'Source Account' in the Transaction above. Does the <entry> code use EXACTLY that account name for the negative amount?
2. **Math Check:** Does the Double-Entry sum to zero?
3. **Reasoning Check:** Is the <plan> sound? Does the <reasoning> explain *why* we chose the expense account?
4. **Syntax:** Is it valid Beancount?

If there are errors (especially with the Source Account), FIX THEM.
CONTEXT HISTORY: The context history uses generic examples, use it as a guide for syntax opposed to using the exact company names from it.
IMPROVE the <reasoning> to be authoritative and educational.
IMPORTANT: When you label the document, make your edits as if they were the original written by the junior accountant as part of the SFT training data.

Output the FINAL CORRECTED XML block (starting with <accounting_entry>).
"""

    system_msg = "You are a Senior AI Accounting Auditor. You are a perfectionist. You strictly enforce that the Bank Account in the code matches the Source Account in the instructions."

    if PROVIDER == "google":
        try:
            return call_google_gemini(system_msg, review_prompt)
        except Exception as e:
            print(f"Google Error: {e}")
            return junior_xml

    if PROVIDER == "anthropic":
        try:
            return call_anthropic_claude(system_msg, review_prompt)
        except Exception as e:
            print(f"Anthropic Error: {e}")
            return junior_xml

    # Fallback / Default to LM Studio
    try:
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": review_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 2000
        }
        
        response = requests.post(LLM_API_URL, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"LM Studio Error: {e}")
        return junior_xml # Fallback to original if review fails

# ================= MAIN LOOP =================
def run_audit():
    if PROVIDER == "google":
        init_google()
        print("Using Google Vertex AI Provider")
    elif PROVIDER == "anthropic":
        print("Using Anthropic Claude Provider")
    else:
        print("Using LM Studio Provider")

    with open(INPUT_FILE, 'r') as f:
        data = json.load(f)
    
    print(f"🧐 Senior Accountant starting audit on {len(data)} records...")
    
    refined_data = []
    
    for task in tqdm(data):
        # 1. Extract what the Junior did
        # The Junior output is inside 'predictions'
        try:
            junior_output = task['predictions'][0]['result'][0]['value']['text'][0]
            original_prompt = task['data']['prompt']
        except (KeyError, IndexError):
            print(f"Skipping task {task.get('id', 'unknown')} - missing predictions.")
            continue

        # 2. The Senior Review (The "Thinking" Step)
        senior_output = critique_and_fix(original_prompt, junior_output)
        
        # 3. Clean up (Remove Markdown if Senior added it)
        # This removes ```xml and ``` wrappers
        senior_output = senior_output.replace("```xml", "").replace("```", "").strip()
        
        # 4. Create the Label Studio Structure
        # We create a new task object where the 'result' is inside 'annotations'
        
        # Copy the structure of the prediction result...
        annotation_result = task['predictions'][0]['result']
        # ...but update the text value with the Senior's output
        annotation_result[0]['value']['text'] = [senior_output]

        task_with_annotation = {
            "data": task['data'],
            "annotations": [{
                "result": annotation_result,
                "was_cancelled": False,
                "ground_truth": False,
                "model_version": "Senior-Auditor-Auto-Review"
            }]
            # Note: We do NOT include 'predictions' here, so Label Studio treats it as a draft
        }
        
        refined_data.append(task_with_annotation)
        
    # Save
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(refined_data, f, indent=2)
    print(f"✅ Audit complete. Import '{OUTPUT_FILE}' into Label Studio.")

if __name__ == "__main__":
    run_audit()