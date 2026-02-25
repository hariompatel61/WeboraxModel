import os
import torch
import numpy as np
from bark import SAMPLE_RATE, generate_audio, preload_models
from scipy.io.wavfile import write as write_wav
from app_config import Config

class BarkClient:
    def __init__(self, use_small_models=True):
        # Set environment variable for small models if needed
        if use_small_models:
            os.environ["SUNO_USE_SMALL_MODELS"] = "True"
        
        # PyTorch 2.6+ fix: Force weights_only=False during model loading
        # because the original Bark weights contain non-standard globals.
        original_load = torch.load
        def patched_load(*args, **kwargs):
            if 'weights_only' not in kwargs:
                kwargs['weights_only'] = False
            return original_load(*args, **kwargs)
        
        torch.load = patched_load
        
        print("Preloading Bark models (this might take a while on first run)...")
        preload_models()
        
        # Restore original load if needed, or just leave it
        torch.load = original_load

    def generate_narration(self, text, output_path):
        """
        Generates audio from text and saves to output_path.
        """
        try:
            audio_array = generate_audio(text)
            write_wav(output_path, SAMPLE_RATE, audio_array)
            return True
        except Exception as e:
            print(f"Error generating audio with Bark: {str(e)}")
            return False

if __name__ == "__main__":
    # Test
    # client = BarkClient()
    # client.generate_narration("Hello, this is a test of the local AI voice system.", "./outputs/audio/test.wav")
    pass
