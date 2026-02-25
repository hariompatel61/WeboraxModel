import sys
import os

# Fix path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from config import Config
    from modules.llm_client import LLMClient
    
    print("Initializing LLMClient...")
    llm = LLMClient()
    print(f"Provider: {llm.provider}, Model: {llm.model}")
    
    print("Testing generation...")
    res = llm.generate("Say hello")
    print(f"Response: {res}")
except Exception as e:
    import traceback
    print("CRASHED:")
    traceback.print_exc()
