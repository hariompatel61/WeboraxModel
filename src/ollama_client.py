import requests
import json

class OllamaClient:
    def __init__(self, base_url="http://127.0.0.1:11434"):
        self.base_url = base_url

    def get_available_models(self):
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [m['name'].strip() for m in models]
        except:
            return []
        return []

    def generate_script(self, prompt, model=None):
        url = f"{self.base_url}/api/generate"
        
        # Auto-detect model if none provided or if it might be wrong
        available = self.get_available_models()
        if not available:
            return "Error: No Ollama models found. Run 'ollama pull gemma2:2b' first."
        
        if not model or model not in available:
            model = available[0] # Use first available (e.g., gemma2:2b)

        payload = {
            "model": model,
            "prompt": f"Write a short video script (3-5 scenes) for: {prompt}. For each scene, provide a visual description (image prompt) and the narration text. Format: Scene 1: Visual: [prompt] Narration: [text]",
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 404:
                return f"Error: Ollama endpoint not found (404). Model '{model}' might be missing or corrupted."
            response.raise_for_status()
            return response.json().get('response', '')
        except Exception as e:
            return f"Error generating script: {str(e)}"

if __name__ == "__main__":
    client = OllamaClient()
    print(client.generate_script("A futuristic city under the ocean"))
