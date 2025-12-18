import os
import pandas as pd
import json
import time
from tqdm import tqdm
from dotenv import load_dotenv

# ================= CONFIGURATION =================
load_dotenv()
PROVIDER = os.getenv("JUNIOR_ACCOUNTANT_PROVIDER", "lm-studio")

# Unsloth must be imported BEFORE transformers (which brain imports)
if PROVIDER == "unsloth":
    try:
        from unsloth import FastLanguageModel
        import torch
    except ImportError:
        pass

from brain import ContextCompiler
import requests  # For calling Ollama or an API

# LM Studio settings
LLM_API_URL = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "local-model"

# Unsloth/HuggingFace settings
UNSLOTH_MODEL_PATH = os.getenv("UNSLOTH_MODEL_PATH", "./outputs/checkpoint-246")  # Your trained model

# Global model/tokenizer (loaded once for unsloth)
_model = None
_tokenizer = None

def init_unsloth():
    """Load the fine-tuned model once using Unsloth."""
    global _model, _tokenizer
    if _model is not None:
        return
    
    print(f"🔄 Loading model from {UNSLOTH_MODEL_PATH}...")
    from unsloth import FastLanguageModel
    import torch
    
    # Reload model + tokenizer using Unsloth
    # This automatically handles the base model + adapter logic
    _model, _tokenizer = FastLanguageModel.from_pretrained(
        model_name = UNSLOTH_MODEL_PATH,
        max_seq_length = 2048,
        dtype = None,
        load_in_4bit = True,
    )
    
    # Enable native 2x faster inference
    FastLanguageModel.for_inference(_model)
    
    print("✅ Model loaded!")

def call_unsloth(prompt):
    """Call the fine-tuned Unsloth model."""
    global _model, _tokenizer
    import torch
    
    # Format as simple instruction/response (matches training format)
    formatted_prompt = f"""### System:
You are a precise accounting agent that outputs XML.

### User:
{prompt}

### Assistant:
"""
    
    
    # Handle case where Unsloth/Transformers returns a Processor (for multimodal models)
    # This prevents "Incorrect image source" error when passing text as first arg
    if hasattr(_tokenizer, "image_processor") or "Processor" in type(_tokenizer).__name__:
        inputs = _tokenizer(
            text=formatted_prompt,
            return_tensors="pt",
            add_special_tokens=True
        ).to("cuda")
    else:
        inputs = _tokenizer(
            formatted_prompt,
            return_tensors="pt",
            add_special_tokens=True
        ).to("cuda")
    
    outputs = _model.generate(
        **inputs,
        max_new_tokens=2000,
        temperature=0.1,
        do_sample=True,
        pad_token_id=_tokenizer.eos_token_id,
    )
    
    # Decode response
    # If it's a processor, we might need to use _tokenizer.tokenizer.decode() or similar
    # But usually tokenizer methods are exposed or we can access the underlying tokenizer
    decoder = _tokenizer
    if hasattr(_tokenizer, "tokenizer"):
         decoder = _tokenizer.tokenizer
         
    response = decoder.decode(outputs[0], skip_special_tokens=True)
    
    # Extract just the assistant's response
    if "### Assistant:" in response:
        response = response.split("### Assistant:")[-1].strip()
    
    return response

# ================= THE AGENT =================
class JuniorAccountant:
    def __init__(self, brain_file):
        self.brain = ContextCompiler(brain_file)
        self.results = []

    def construct_prompt(self, row):
        # 1. Clean Data handling
        payee = str(row['Payee']) if pd.notna(row['Payee']) else "Unknown"
        desc = str(row['Description']) if pd.notna(row['Description']) else ""
        
        # 2. Get Context from Brain
        context_xml = self.brain.retrieve_context(payee, desc)
        
        # 3. Dynamic Source Account (The Magic Fix)
        # We ensure it looks like a valid account if the CSV just says "Lloyds"
        raw_source = row.get('Source_Account', 'Unknown')
        
        # PRO TIP: If your CSV just says "Lloyds", let's help the agent by adding "Assets:"
        # If your CSV already has "Assets:...", this line won't hurt.
        if "Assets" not in raw_source and raw_source != "Unknown":
             source_account = f"Assets:{raw_source}:Checking"
        else:
             source_account = raw_source

        # 4. The Prompt
        prompt = f"""You are an expert accountant. Categorize this transaction into strict Beancount syntax.

        <context>
        {context_xml}
        </context>

        <transaction>
        Date: {row['Date']}
        Payee: {payee}
        Description: {desc}
        Amount: {row['Amount']} {row['Currency']}
        Source Account: {source_account}
        </transaction>

        Instructions:
        1. **Analyze:** Look at the Payee and Description. Check the <context> for history.
        2. **Plan:** Decide the Account (e.g., Expenses:Food).
        - If the Description is empty/nan, INFER it from the Payee (e.g., "Uber" -> "Taxi Ride").
        - If you are unsure, use the '!' flag instead of '*'.
        3. **Reasoning:** Explain your logic step-by-step.
        4. **Entry:** Write the Beancount code.
        - CRITICAL: The negative amount MUST go to: {source_account}
        - The positive amount MUST go to the Expense/Income account.

        <example_output_structure>
        <accounting_entry>
            <thought_process>
                <plan>
                    1. Nature: Payment for internet.
                    2. Double Entry: Credit {source_account}, Debit Expenses:Home:Internet.
                </plan>
                <reasoning>
                    <step1>Payee is Comcast. History confirms 'Expenses:Home:Internet'.</step1>
                    <step2>Math: -50.00 from Bank, +50.00 to Expense.</step2>
                </reasoning>
            </thought_process>
            <entry>
                2023-01-20 * "Comcast" "Internet Bill"
                Expenses:Home:Internet     50.00 {row['Currency']}
                {source_account}          -50.00 {row['Currency']}
            </entry>
        </accounting_entry>
        </example_output_structure>

        IMPORTANT: 
        - Do not output Markdown formatting (no ```xml blocks). 
        - Output ONLY the raw XML starting with <accounting_entry>.
        - IMPORTANT: The context history uses generic examples, use it as a guide for syntax opposed to using the exact company names from it.
        """
        return prompt

    def call_llm(self, prompt):
        """
        Swappable function to call your LLM. 
        Supports: lm-studio, unsloth
        """
        if PROVIDER == "unsloth":
            try:
                return call_unsloth(prompt)
            except Exception as e:
                print(f"⚠️ Unsloth Error: {e}")
                return f"Error calling Unsloth: {e}"
        
        # Default: LM Studio
        try:
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are a precise accounting agent that outputs XML."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 2000
            }
            
            headers = {"Content-Type": "application/json"}
            response = requests.post(LLM_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
            
        except Exception as e:
            print(f"⚠️ LM Studio Error: {e}")
            return f"Error calling LLM: {e}"

        # --- GEMINI / OPENAI EXAMPLE (Commented Out) ---
        # import openai
        # client = openai.Client(api_key="...")
        # response = client.chat.completions.create(...)
        # return response.choices[0].message.content

    def process_batch(self, csv_file, limit=10):
        """Runs the loop."""
        df = pd.read_csv(csv_file)
        
        # --- FIX: Clean up sloppy CSV headers ---
        df.columns = df.columns.str.strip() 
        # ----------------------------------------

        # Just take the first N rows for the test run
        work_queue = df.head(limit)

        print(work_queue)
        
        print(f"🤖 Agent starting work on {len(work_queue)} transactions...")
        
        for index, row in tqdm(work_queue.iterrows(), total=len(work_queue)):
            prompt = self.construct_prompt(row)
            
            # The "Thinking" Phase
            llm_output = self.call_llm(prompt)
            
            # Save for Label Studio
            self.results.append({
                "data": {
                    "prompt": prompt,  # The input for the annotator to see
                    "transaction_id": row.get('Beancount_Id', str(index))
                },
                "predictions": [{
                    "model_version": MODEL_NAME,
                    "result": [
                        {
                            "from_name": "response",
                            "to_name": "prompt",
                            "type": "textarea",
                            "value": {
                                "text": [llm_output] # Pre-fill the editor!
                            }
                        }
                    ]
                }]
            })
            
            # Be nice to your spare PC
            time.sleep(0.5)

    def save_for_label_studio(self, filename="label_studio_import.json"):
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"💾 Saved {len(self.results)} tasks to {filename}")

if __name__ == "__main__":
    # Initialize model if using unsloth
    if PROVIDER == "unsloth":
        init_unsloth()
        print("Using Unsloth/HuggingFace Provider")
    else:
        print("Using LM Studio Provider")
    
    # 1. Initialize
    agent = JuniorAccountant(data/my_accounts.beancount")
    
    # 2. Run on your CSV
    # Only doing 5 for the first test!
    agent.process_batch("bank_statement_sft_randomized.csv", limit=10000)
    
    # 3. Export
    agent.save_for_label_studio("pre_senior_accountant.json")