import os
import asyncio
from dotenv import load_dotenv

from app_config import Config
from modules.topic_generator import TopicGenerator
from modules.script_writer import ScriptWriter
from modules.storyboard import StoryboardCreator
from modules.seo_metadata import SEOMetadataGenerator
from modules.image_engine import ImageEngine
from modules.thumbnail import ThumbnailGenerator
from modules.voiceover import VoiceoverGenerator
from modules.music_sfx import MusicSFXManager
from modules.video_editor import VideoEditor
from modules.excel_tracker import ExcelTracker

def main():
    load_dotenv()
    Config.ensure_directories()
    
    print("🎬 Initializing High-Retention YouTube Pipeline...")
    
    topic_gen = TopicGenerator()
    script_gen = ScriptWriter()
    storyboard_gen = StoryboardCreator()
    seo_gen = SEOMetadataGenerator()
    image_engine = ImageEngine()
    thumb_gen = ThumbnailGenerator()
    voice_gen = VoiceoverGenerator()
    audio_mgr = MusicSFXManager()
    editor = VideoEditor()
    tracker = ExcelTracker()

    USER_PROMPT = input("\nEnter your video topic/prompt (or press Enter to auto-generate from trends): ").strip()

    # 1. Topic Generation
    print("\n[1/7] Generating Topics...")
    if USER_PROMPT:
        best_topic = {"topic": USER_PROMPT, "title": USER_PROMPT, "premise": "User generated", "suggested_duration": 60}
    else:
        topics = topic_gen.generate_topics(count=3)
        best_topic = topics[0] if topics else {"topic": "AI Mystery", "title": "The AI Mystery", "premise": "A mystery", "suggested_duration": 60}
    
    print(f"      Selected Topic: {best_topic.get('title')}")

    # 2. Script Writing
    print("\n[2/7] Writing High-Retention Script...")
    script = script_gen.write_script(best_topic)
    script_text = script_gen.get_full_text(script)
    print(f"      Script Style: {script.get('applied_style', 'default')}")
    print(f"      Hook: {script.get('hook', '')}")

    # 3. Storyboarding & SEO
    print("\n[3/7] Creating Storyboard & SEO Metadata...")
    storyboard = storyboard_gen.create_storyboard(script, best_topic.get('suggested_duration', 60))
    metadata = seo_gen.generate_metadata(best_topic, script)
    
    print(f"      SEO Title: {metadata.get('title')}")
    print(f"      Tags: {', '.join(metadata.get('tags', [])[:3])}...")

    # 4. Voiceover & Audio
    print("\n[4/7] Generating Voiceover & SFX...")
    # Using asyncio to run the async generator
    voiceovers = asyncio.run(voice_gen.generate_all_voiceovers(storyboard, Config.OUTPUT_DIR))
    bgm_path = audio_mgr.generate_background_music(Config.OUTPUT_DIR, mood="suspenseful")
    print(f"      Voiceovers generated: {len(voiceovers)}")

    # 5. Visuals & Scenes
    print("\n[5/7] Generating Cinematic Scenes & Thumbnail...")
    scene_images = []
    for i, scene in enumerate(storyboard):
        img_path = image_engine.generate_cinematic_image(scene, i+1, os.path.join(Config.OUTPUT_DIR, "images"))
        scene_images.append(img_path)
    
    thumbnail_data = thumb_gen.generate_thumbnail_metadata(best_topic, script)
    thumb_path = thumb_gen.create_thumbnail(thumbnail_data, Config.OUTPUT_DIR)
    print(f"      Thumbnail saved to: {thumb_path}")

    # 6. Video Editing
    print("\n[6/7] Editing Final Video...")
    final_video_path = editor.assemble_video(
        storyboard,
        scene_images,
        voiceovers,
        bgm_path=bgm_path,
        hook_text=script.get("hook", ""),
        output_dir=Config.OUTPUT_DIR,
        duration=best_topic.get("suggested_duration", Config.VIDEO_DURATION),
    )
    
    # 7. Tracking
    print("\n[7/7] Logging to Tracker...")
    tracker.log_run(topic_data=best_topic, script_data=script, video_path=final_video_path, status="Completed")

    print(f"\n✅ Pipeline Complete! Video saved to: {final_video_path}")

if __name__ == "__main__":
    main()
