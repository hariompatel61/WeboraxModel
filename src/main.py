import os
import re
from ollama_client import OllamaClient
from sd_client import SDClient
from bark_client import BarkClient
from renderer import VideoRenderer

def parse_script(script_text):
    """
    Rudimentary parser for the Ollama output.
    Expected format: Scene X: Visual: [prompt] Narration: [text]
    """
    scenes = []
    # Find all matches for Scene X blocks
    scene_blocks = re.split(r'Scene \d+:', script_text)[1:]
    
    for i, block in enumerate(scene_blocks):
        try:
            visual = re.search(r'Visual:\s*(.*?)(?=\s*Narration:|$)', block, re.DOTALL).group(1).strip()
            narration = re.search(r'Narration:\s*(.*)', block, re.DOTALL).group(1).strip()
            scenes.append({"id": i+1, "visual": visual, "narration": narration})
        except:
            continue
    return scenes

def main():
    # Configuration
    USER_PROMPT = input("Enter your video topic/prompt: ")
    
    # Initialize Clients
    ollama = OllamaClient()
    sd = SDClient()
    # Note: Bark initialization is slow, consider lazy loading
    print("Initializing Bark (Voice)...")
    bark = BarkClient() 
    renderer = VideoRenderer()

    # 1. Generate Script
    print(f"Generating script for: {USER_PROMPT}...")
    script_raw = ollama.generate_script(USER_PROMPT)
    print("\n--- GENERATED SCRIPT ---")
    print(script_raw)
    
    scenes = parse_script(script_raw)
    if not scenes:
        print("Failed to parse scenes from script. Check Ollama output format.")
        return

    final_clips = []

    # 2. Process Scenes
    for scene in scenes:
        print(f"\nProcessing Scene {scene['id']}...")
        
        # Paths
        image_dir = f"outputs/images/scene_{scene['id']}"
        os.makedirs(image_dir, exist_ok=True)
        audio_path = f"outputs/audio/scene_{scene['id']}.wav"
        video_clip_path = f"outputs/video/clip_{scene['id']}.mp4"

        # Generate Animation
        print(f"  Generating Animation: {scene['visual'][:50]}...")
        # sd.generate_animation(scene['visual'], image_dir)
        # Note: In a real run, this would save a GIF. For this script, we assume success.
        
        # Generate Audio
        print(f"  Generating Audio: {scene['narration'][:50]}...")
        bark.generate_narration(scene['narration'], audio_path)

        # Merge Audio/Video (assuming SD saved a GIF at outputs/images/scene_X/anim_0.gif)
        # gif_path = os.path.join(image_dir, "anim_0.gif")
        # if os.path.exists(gif_path):
        #     renderer.merge_video_audio(gif_path, audio_path, video_clip_path)
        #     final_clips.append(video_clip_path)

    # 3. Final Merge
    if final_clips:
        print("\nMerging all scenes into final video...")
        renderer.combine_clips(final_clips, "outputs/video/final_video.mp4")
        print("Success! Final video at outputs/video/final_video.mp4")
    else:
        print("\nNo clips were generated. Check SD/AnimateDiff and Bark status.")

if __name__ == "__main__":
    main()
