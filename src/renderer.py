import subprocess
import os

class VideoRenderer:
    def __init__(self, ffmpeg_path="ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def merge_video_audio(self, video_path, audio_path, output_path):
        """
        Merges a video file (e.g., GIF/MP4) with an audio file (WAV/MP3).
        """
        # Command to loop video if it's shorter than audio, or just merge
        # For simplicity, we assume they are similar or we just merge them.
        cmd = [
            self.ffmpeg_path,
            "-y", # Overwrite output
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "libx264", # Re-encode to mp4
            "-c:a", "aac",
            "-strict", "experimental",
            "-pix_fmt", "yuv420p", # Compatibility
            "-shortest", # End when the shortest stream ends
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return True
            else:
                print(f"FFmpeg Error: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error running FFmpeg: {str(e)}")
            return False

    def combine_clips(self, clip_list, output_path):
        """
        Combines multiple video clips into one.
        Expects a list of absolute paths.
        """
        # Create a temporary file for ffmpeg concat
        with open("clips.txt", "w") as f:
            for clip in clip_list:
                f.write(f"file '{clip}'\n")
        
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", "clips.txt",
            "-c", "copy",
            output_path
        ]
        
        try:
            subprocess.run(cmd)
            os.remove("clips.txt")
            return True
        except:
            return False

if __name__ == "__main__":
    renderer = VideoRenderer()
    # renderer.merge_video_audio("input.gif", "input.wav", "output.mp4")
