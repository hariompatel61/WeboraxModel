import requests
import json

base_url = "http://127.0.0.1:11434"

def diag():
    print(f"Testing connection to {base_url}...")
    try:
        r = requests.get(base_url)
        print(f"Root endpoint: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Root endpoint failed: {e}")

    print("\nTesting /api/tags...")
    try:
        r = requests.get(f"{base_url}/api/tags")
        print(f"Tags endpoint: {r.status_code}")
        print(json.dumps(r.json(), indent=2))
    except Exception as e:
        print(f"Tags endpoint failed: {e}")

    print("\nTesting /api/generate with first available model...")
    try:
        tags = requests.get(f"{base_url}/api/tags").json()
        if 'models' in tags and len(tags['models']) > 0:
            model = tags['models'][0]['name']
            print(f"Attempting to generate with model: {model}")
            payload = {
                "model": model,
                "prompt": "Say hi",
                "stream": False
            }
            r = requests.post(f"{base_url}/api/generate", json=payload)
            print(f"Generate endpoint: {r.status_code}")
            print(r.text)
        else:
            print("No models found to test generation.")
    except Exception as e:
        print(f"Generate test failed: {e}")

if __name__ == "__main__":
    diag()
