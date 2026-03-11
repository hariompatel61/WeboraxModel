"""
Step 7: Video Editor & Assembler
Assembles scene images, voiceover, music, and text overlays into the final video.
"""

import os

from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
)

from app_config import Config


class VideoEditor:
    """Assemble generated media into a vertical final video."""

    def __init__(self):
        self.width = Config.VIDEO_WIDTH
        self.height = Config.VIDEO_HEIGHT
        self.fps = Config.VIDEO_FPS
        self.total_duration = Config.VIDEO_DURATION

    def assemble_video(
        self,
        storyboard,
        scene_image_paths,
        voiceover_paths,
        bgm_path=None,
        sfx_paths=None,
        hook_text=None,
        output_path=None,
        duration=None,
        output_dir=None,
    ):
        """Assemble all components into the final video."""
        if output_path is None:
            base_output_dir = output_dir or Config.OUTPUT_DIR
            output_path = os.path.join(base_output_dir, "video", "final_video.mp4")

        scene_clips = []
        audio_clips = []
        sfx_paths = sfx_paths or {}
        current_time = 0.0

        for index, scene in enumerate(storyboard):
            if not scene_image_paths:
                break

            img_path = scene_image_paths[min(index, len(scene_image_paths) - 1)]
            if not img_path or not os.path.exists(img_path):
                continue

            scene_duration = float(scene.get("duration_seconds", 4) or 4)
            camera_angle = scene.get("camera_angle", scene.get("shot_type", "wide"))

            img_clip = self._create_scene_clip(img_path, scene_duration, camera_angle)
            img_clip = img_clip.with_start(current_time)
            scene_clips.append(img_clip)

            dialogue = scene.get("dialogue", "")
            if isinstance(dialogue, list):
                dialogue = " ".join(str(part) for part in dialogue if part)
            if dialogue:
                sub_clip = self._create_subtitle(str(dialogue), scene_duration, current_time)
                if sub_clip:
                    scene_clips.append(sub_clip)

            if index < len(voiceover_paths) and voiceover_paths[index]:
                try:
                    vo_audio = AudioFileClip(voiceover_paths[index])
                    if vo_audio.duration > scene_duration:
                        vo_audio = vo_audio.subclipped(0, scene_duration)
                    audio_clips.append(vo_audio.with_start(current_time))
                except Exception:
                    pass

            sfx_type = scene.get("sfx", "silence")
            if sfx_type != "silence" and sfx_type in sfx_paths:
                try:
                    sfx_audio = AudioFileClip(sfx_paths[sfx_type]).with_start(current_time + 0.1)
                    audio_clips.append(sfx_audio.with_volume_scaled(0.5))
                except Exception:
                    pass

            current_time += scene_duration

        if not scene_clips:
            raise ValueError("No valid scene clips were generated for video assembly.")

        if hook_text:
            hook_clip = self._create_hook_overlay(hook_text)
            if hook_clip:
                scene_clips.append(hook_clip)

        target_duration = float(duration or current_time or self.total_duration)
        video = CompositeVideoClip(scene_clips, size=(self.width, self.height)).with_duration(target_duration)

        if bgm_path and os.path.exists(bgm_path):
            try:
                bgm = AudioFileClip(bgm_path)
                if bgm.duration > video.duration:
                    bgm = bgm.subclipped(0, video.duration)
                audio_clips.append(bgm.with_volume_scaled(0.15))
            except Exception:
                pass

        if audio_clips:
            video = video.with_audio(CompositeAudioClip(audio_clips))

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        video.write_videofile(
            output_path,
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=1,
            bitrate="2000k",
            logger=None,
            ffmpeg_params=[
                "-movflags",
                "+faststart",
                "-pix_fmt",
                "yuv420p",
            ],
        )

        video.close()
        for clip in scene_clips:
            try:
                clip.close()
            except Exception:
                pass
        for clip in audio_clips:
            try:
                clip.close()
            except Exception:
                pass

        return output_path

    def _create_scene_clip(self, image_path, duration, camera_angle="wide"):
        clip = ImageClip(image_path, duration=duration)
        zoom_factor = 0.12 if str(camera_angle).lower() in ("close_up", "extreme_close_up") else 0.08
        clip = clip.resized(lambda t: 1.0 + zoom_factor * (t / max(duration, 0.1)))
        return clip.with_position("center")

    def _create_subtitle(self, text, duration, start_time):
        try:
            words = text.split()
            lines = []
            current_line = []
            for word in words:
                current_line.append(word)
                if len(" ".join(current_line)) > 30:
                    lines.append(" ".join(current_line))
                    current_line = []
            if current_line:
                lines.append(" ".join(current_line))

            wrapped_text = "\n".join(lines)
            clip = TextClip(
                text=wrapped_text,
                font_size=44,
                color="white",
                font="Arial",
                stroke_color="black",
                stroke_width=2,
                method="caption",
                size=(self.width - 100, None),
                text_align="center",
            )
            return (
                clip.with_duration(duration)
                .with_start(start_time)
                .with_position(("center", self.height - 350))
            )
        except Exception:
            return None

    def _create_hook_overlay(self, text):
        try:
            clip = TextClip(
                text=text,
                font_size=56,
                color="yellow",
                font="Arial",
                stroke_color="red",
                stroke_width=3,
                method="caption",
                size=(self.width - 80, None),
                text_align="center",
            )
            return clip.with_duration(3).with_start(0).with_position(("center", 200))
        except Exception:
            return None
