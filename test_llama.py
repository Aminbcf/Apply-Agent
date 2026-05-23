import sys
from pathlib import Path
sys.path.append(str(Path("src/backend").absolute()))

from AI.llm.llm_interface import LlamaCppAdapter

def main():
    print("Initializing adapter...")
    adapter = LlamaCppAdapter()
    print("Adapter initialized. Generating text...")
    try:
        res = adapter.generate("Hello, how are you?")
        print("Response:", res)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
