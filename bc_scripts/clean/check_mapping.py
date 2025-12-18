from transformers import AutoModelForCausalLM, AutoConfig
from transformers.models.mistral3 import Mistral3Config
try:
    from transformers.models.mistral3.modeling_mistral3 import Mistral3ForConditionalGeneration
    print("Mistral3ForConditionalGeneration FOUND")
except ImportError as e:
    print(f"Mistral3ForConditionalGeneration NOT FOUND: {e}")

try:
    # Attempt to access the mapping directly
    from transformers.models.auto.modeling_auto import MODEL_FOR_CAUSAL_LM_MAPPING
    if Mistral3Config in MODEL_FOR_CAUSAL_LM_MAPPING:
        print("Mistral3Config IS in MODEL_FOR_CAUSAL_LM_MAPPING")
    else:
        print("Mistral3Config IS NOT in MODEL_FOR_CAUSAL_LM_MAPPING")
except Exception as e:
    print(f"Could not check mapping: {e}")
