import os
from pathlib import Path
from moviepy.editor import VideoFileClip

from config import (
    OUTPUT_DIR, TEMP_DIR, GEMINI_API_KEY,
    AUTO_CLEANUP, REVIEW_CLIPS, GENERATE_THUMBNAILS, GENERATE_SUMMARY,
    SILENCE_GAP, SILENCE_KEEP, MUSIC_PATH, MUSIC_VOLUME, LOGO_PATH,
    INTRO_PATH, OUTRO_PATH,
)
from services.youtube_downloader import YouTubeDownloader
from services.whisper_transcriber import WhisperSingleton
from services.gemini_selector import GeminiSelector
from services.face_tracker import FaceTracker
from services.caption_maker import CaptionMaker
from services import editor
from utils.helpers import generate_random_clips, cleanup_temp_files


class VideoProcessor:
    """
    Orchestrates the entire video processing pipeline.

    This class initializes and manages all the services required for
    downloading, transcribing, selecting clips, tracking faces, and
    adding captions to a YouTube video.
    """
    def __init__(self, caption_style='clean_white'):
        """
        Initializes the VideoProcessor with a specific caption style.

        Args:
            caption_style (str, optional): The style of captions to use.
                                            Defaults to 'clean_white'.
        """
        self.downloader = YouTubeDownloader()
        self.transcriber = WhisperSingleton()
        self.ai_selector = GeminiSelector(api_key=GEMINI_API_KEY)
        self.face_tracker = FaceTracker()
        self.caption_maker = CaptionMaker(caption_style)

    def process_video(self, url, num_clips, min_duration, max_duration, review=None):
        """
        Processes a YouTube video to generate viral clips.

        Args:
            url (str): The URL of the YouTube video.
            num_clips (int): The number of clips to generate.
            min_duration (int): The minimum duration of each clip.
            max_duration (int): The maximum duration of each clip.

        Returns:
            tuple: A tuple containing a list of output file paths and the
                   title of the video.
        """
        # Accept either a local video file or a URL to download.
        if os.path.isfile(url):
            from utils.helpers import get_video_duration
            video_path = Path(url)
            title = video_path.stem
            author = ''
            duration = get_video_duration(video_path)
            print(f"📂 Using local video: {video_path.name} ({duration:.1f}s)")
        else:
            print("📥 Downloading video...")
            video_path, title, duration = self.downloader.download(url)
            author = getattr(self.downloader, 'video_author', '')
            print(f"✅ Download complete: {title} ({duration:.1f}s)")

        print("🎵 Starting transcription with Whisper...")
        words, transcript, segments = self.transcriber.transcribe(video_path)
        print(f"✅ Transcription processing complete")

        if not segments:
            print("❌ Transcription failed. Using random clips.")
            print("🎲 Generating random clips...")
            clip_specs = generate_random_clips(duration, num_clips, min_duration, max_duration)
            print(f"✅ Generated {len(clip_specs)} random clips")
        else:
            print("🧠 Using AI to select the most viral clips...")
            clip_specs = self.ai_selector.select_clips(
                segments, duration, num_clips, min_duration, max_duration,
                video_title=title, video_author=author
            )
            print(f"✅ AI selected {len(clip_specs)} viral clips")

        if not clip_specs:
            raise ValueError("Could not select any clips from the video.")

        # Optional: let the user trim / drop clips before rendering.
        do_review = REVIEW_CLIPS if review is None else review
        if do_review:
            clip_specs = editor.interactive_review(clip_specs, duration)
            if not clip_specs:
                print("🛑 No clips left after review - nothing to render.")
                self.face_tracker.close()
                cleanup_temp_files()
                return [], title

        # Optional: whole-video summary saved alongside the clips.
        if GENERATE_SUMMARY and segments:
            summary = self.ai_selector.summarize(segments, video_title=title)
            if summary:
                summary_path = OUTPUT_DIR / f"{Path(video_path).stem}_summary.txt"
                try:
                    with open(summary_path, 'w', encoding='utf-8') as fh:
                        fh.write(summary + "\n")
                    print(f"📝 Video summary saved to: {summary_path.name}")
                except Exception as e:
                    print(f"⚠️ Could not save summary: {e}")

        thumb_font = (self.caption_maker.font_paths.get('bold')
                      or self.caption_maker.font_paths.get('impact'))

        output_files = []
        print(f"\n🎬 Processing {len(clip_specs)} viral clips...")

        for i, clip_info in enumerate(clip_specs, 1):
            start = clip_info['start']
            end = clip_info['end']
            title_text = clip_info.get('title', f'Clip {i}')
            virality_score = clip_info.get('virality_score', 0)

            print(f"\n📹 Clip {i}/{len(clip_specs)}: {title_text}")
            print(f"    ⭐ Virality Score: {virality_score}/100")
            print(f"    ⏱️  Time: {start:.1f}s to {end:.1f}s")
            print(f"    🎨 Caption Style: {self.caption_maker.styles[self.caption_maker.selected_style]['name']}")

            try:
                with VideoFileClip(str(video_path)) as video:
                    clip = video.subclip(start, end)

                    # Words relative to this subclip (0-based) for cleanup + captions.
                    words_rel = []
                    for w in (words or []):
                        ws, we = w['start'] - start, w['end'] - start
                        if we <= 0 or ws >= clip.duration:
                            continue
                        words_rel.append({'word': w['word'],
                                          'start': max(0.0, ws),
                                          'end': min(clip.duration, we)})

                    # Auto-cleanup: remove fillers + long silences.
                    if AUTO_CLEANUP and words_rel:
                        print("    🧹 Auto-cleanup (removing fillers & silences)...")
                        clip, words_rel, removed = editor.auto_cleanup(
                            clip, words_rel, silence_gap=SILENCE_GAP,
                            silence_keep=SILENCE_KEEP)
                        print(f"    ✅ Tightened clip by {removed:.1f}s"
                              if removed > 0.3 else "    ✅ Nothing worth trimming")

                    print(f"    🎯 Applying intelligent face tracking...")
                    clip = self.face_tracker.track_and_crop(clip)
                    print(f"    ✅ Face tracking and cropping complete")

                    if words_rel:
                        print(f"    📝 Adding captions...")
                        clip = self.caption_maker.add_captions(clip, words_rel, 0.0)

                    # Branding: logo/watermark + background music (both optional).
                    clip = editor.add_logo(clip, LOGO_PATH)
                    clip = editor.add_background_music(clip, MUSIC_PATH, MUSIC_VOLUME)

                    filename = f"clip_{i}_{virality_score}pts_{Path(video_path).stem}.mp4"
                    output_path = OUTPUT_DIR / filename

                    # Cover image from the finished (captioned/branded) main clip.
                    if GENERATE_THUMBNAILS:
                        thumb_path = OUTPUT_DIR / f"{output_path.stem}_thumbnail.jpg"
                        if editor.make_thumbnail(clip, title_text, str(thumb_path), thumb_font):
                            print(f"    🖼️ Thumbnail saved: {thumb_path.name}")

                    # Optional intro/outro wraps the final clip.
                    final_clip = editor.add_intro_outro(clip, INTRO_PATH, OUTRO_PATH)

                    print(f"    🎥 Encoding with optimized settings...")
                    print(f"    ⏳ Starting video encoding (this may take a while)...")
                    final_clip.write_videofile(
                        str(output_path),
                        codec='libx264',
                        audio_codec='aac',
                        audio_bitrate='192k',
                        # 'medium' preset + CRF 18 gives noticeably crisper clips
                        # than the old 'faster'/CRF 20 for a small speed cost.
                        preset='medium',
                        ffmpeg_params=['-crf', '18', '-pix_fmt', 'yuv420p', '-threads', '2'],
                        verbose=True,  # Enable verbose output to show progress
                        logger=None,
                        temp_audiofile=str(TEMP_DIR / f'temp_audio_{i}.m4a'),
                        remove_temp=True,
                        # Use 2 threads for encoding to avoid overloading the system
                        threads=2
                    )
                    print(f"    ✅ Video encoding complete")
                    output_files.append(str(output_path))
                    print(f"    ✅ Saved: {filename}")

                    # Save the title + catchy story description together in one file.
                    description = clip_info.get('description', '').strip()
                    desc_path = OUTPUT_DIR / f"{output_path.stem}_description.txt"
                    try:
                        with open(desc_path, 'w', encoding='utf-8') as fh:
                            fh.write(f"🎬 TITLE:\n{title_text}\n\n")
                            fh.write(f"📝 DESCRIPTION:\n{description}\n")
                        print(f"    🎬 Title: {title_text}")
                        if description:
                            print(f"    📝 Description: {description}")
                        print(f"    💾 Saved title + description to: {desc_path.name}")
                    except Exception as write_err:
                        print(f"    ⚠️ Could not save title/description: {write_err}")

            except Exception as e:
                print(f"    ❌ Error processing clip {i}: {e}")
                continue

        self.face_tracker.close()
        cleanup_temp_files()

        return output_files, title
