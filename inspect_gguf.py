import sys
from gguf import GGUFReader

def main():
    reader = GGUFReader("src/backend/AI/llm/final_lora_adapter/model.gguf")
    for tensor in reader.tensors:
        if "embd" in tensor.name or "output" in tensor.name:
            print(f"{tensor.name}: {tensor.shape}")

if __name__ == "__main__":
    main()
