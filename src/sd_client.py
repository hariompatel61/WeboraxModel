from app_config import Config

class SDClient:
    def __init__(self, base_url=None):
        self.base_url = base_url or "http://127.0.0.1:7860"

    def generate_animation(self, prompt, output_path, neg_prompt="", steps=20, frames=16):
        url = f"{self.base_url}/sdapi/v1/txt2img"
        
        # AnimateDiff payload structure
        payload = {
            "prompt": prompt,
            "negative_prompt": neg_prompt,
            "steps": steps,
            "width": 512,
            "height": 512,
            "alwayson_scripts": {
                "AnimateDiff": {
                    "args": [
                        {
                            "model": "mm_sd_v15_v2.ckpt", # Default AnimateDiff model
                            "format": ["GIF"],
                            "enable": True,
                            "video_length": frames,
                            "fps": 8
                        }
                    ]
                }
            }
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            r = response.json()
            
            # Save the result (usually returned as base64 images/gifs)
            # WebUI API returns a list of images
            for i, img_data in enumerate(r['images']):
                with open(os.path.join(output_path, f"anim_{i}.gif"), "wb") as f:
                    f.write(base64.b64decode(img_data))
            return True
        except Exception as e:
            print(f"Error generating animation: {str(e)}")
            return False

if __name__ == "__main__":
    client = SDClient()
    # Note: Requires SD WebUI running with --api and AnimateDiff installed
    # client.generate_animation("A cyberpunk cat flying a drone", "./outputs/images")
