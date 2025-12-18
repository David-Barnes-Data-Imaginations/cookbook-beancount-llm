"""
Merge LoRA adapter with base model and push to Hugging Face Hub.
Uses latest transformers with float16 loading (no bitsandbytes) to avoid version conflicts.
"""
import os
import torch
from huggingface_hub import login
from peft import PeftModel, PeftConfig

# Configuration
CHECKPOINT_PATH = "outputs/checkpoint-180"
REPO_NAME = "david-barnes/ministral-3B-Beancount-v1"

# Login to Hugging Face
hf_token = os.getenv('HF_TOKEN')
if hf_token:
    login(token=hf_token)
    print("✅ Logged in with HF_TOKEN")
else:
    raise ValueError("❌ No HF_TOKEN found! Set it with: export HF_TOKEN=your_token")

# Step 1: Load the adapter config to find the base model
print("📂 Loading adapter config...")
peft_config = PeftConfig.from_pretrained(CHECKPOINT_PATH)
base_model_name = peft_config.base_model_name_or_path
print(f"   Base model: {base_model_name}")

# Step 2: Load the base model in float16 (no 4-bit quantization to avoid bitsandbytes)
print("🔧 Loading base model in float16 (this may take ~6GB VRAM)...")
# For Mistral3 models, we need to use AutoModel since it's a conditional generation model
from transformers import AutoModel, AutoTokenizer

model = AutoModel.from_pretrained(
    base_model_name,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True,
)

# Step 3: Load tokenizer
print("📝 Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)

# Step 4: Apply the adapter
print("🔗 Applying LoRA adapter...")
model = PeftModel.from_pretrained(model, CHECKPOINT_PATH)

# Step 5: Merge adapter weights into the base model
print("🔀 Merging adapter into base model...")
model = model.merge_and_unload()

# Step 6: Save locally first (for GGUF conversion)
local_path = "merged_model"
print(f"💾 Saving merged model locally to {local_path}...")
model.save_pretrained(local_path)
tokenizer.save_pretrained(local_path)

# Step 7: Push to Hub
print(f"🚀 Pushing to {REPO_NAME}...")
model.push_to_hub(REPO_NAME, token=hf_token)
tokenizer.push_to_hub(REPO_NAME, token=hf_token)

print(f"""
✅ Done! 
   - Local merged model: {local_path}/
   - Hub: https://huggingface.co/{REPO_NAME}
   
🔧 To convert to GGUF, run:
   python -m llama_cpp.convert {local_path} --outfile model.gguf
""")
