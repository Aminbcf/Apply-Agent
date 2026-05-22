"""
Script to merge a LoRA adapter with its base model and convert it to GGUF format for llama.cpp.
"""

import os
import subprocess
import shutil
import sys
from pathlib import Path
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import json

def main():
    base_dir = Path(os.path.abspath(__file__)).parent.parent
    adapter_dir = base_dir / "src" / "backend" / "AI" / "llm" / "final_lora_adapter"
    merged_dir = adapter_dir / "merged_model"
    gguf_output = adapter_dir / "model.gguf"
    
    if gguf_output.exists():
        print(f"GGUF model already exists at {gguf_output}. Exiting.")
        return

    # 1. Read base model name
    config_path = adapter_dir / "adapter_config.json"
    if not config_path.exists():
        print(f"Error: {config_path} not found.")
        return
        
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    base_model_name = config.get("base_model_name_or_path", "Qwen/Qwen2.5-1.5B-Instruct")
    
    print(f"Loading base model: {base_model_name}")
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        device_map="cpu",
        torch_dtype=torch.float16,
        trust_remote_code=True
    )
    
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
    
    print(f"Loading PEFT adapter from {adapter_dir}")
    peft_model = PeftModel.from_pretrained(base_model, adapter_dir)
    
    print("Merging weights...")
    merged_model = peft_model.merge_and_unload()
    
    print(f"Saving merged model to {merged_dir}")
    merged_dir.mkdir(parents=True, exist_ok=True)
    merged_model.save_pretrained(merged_dir, safe_serialization=True)
    tokenizer.save_pretrained(merged_dir)
    print("Merge complete!")
    
    # Download llama.cpp convert script if not present
    llama_cpp_dir = base_dir / "llama.cpp"
    if not llama_cpp_dir.exists():
        print("Cloning llama.cpp to convert to GGUF...")
        subprocess.run(["git", "clone", "https://github.com/ggerganov/llama.cpp.git", str(llama_cpp_dir)], check=True)
        
    print("Converting to GGUF using llama.cpp...")
    convert_script = llama_cpp_dir / "convert_hf_to_gguf.py"
    
    cmd = [
        sys.executable, str(convert_script),
        str(merged_dir),
        "--outfile", str(gguf_output),
        "--outtype", "q8_0" # Quantize to 8-bit during export for speed/memory efficiency
    ]
    
    subprocess.run(cmd, check=True)
    
    print(f"Done! GGUF model saved to {gguf_output}")
    print("Cleaning up merged model directory...")
    shutil.rmtree(merged_dir)

if __name__ == "__main__":
    main()
