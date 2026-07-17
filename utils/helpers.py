import random
from config import TEMP_DIR, DOWNLOADS_DIR

VIDEO_EXTENSIONS = ('.mp4', '.mkv', '.webm', '.mov', '.avi', '.m4v')


def cleanup_temp_files():
    """
    Removes all files from the temporary directory.
    """
    print("🧹 Cleaning up temporary files...")
    try:
        for item in TEMP_DIR.iterdir():
            if item.is_file():
                item.unlink()
        print("✅ Cleanup complete.")
    except Exception as e:
        print(f"⚠️  Could not clean up all temporary files: {e}")


def get_video_duration(path):
    """Return a video file's duration in seconds (0.0 if it can't be read)."""
    try:
        from moviepy.editor import VideoFileClip
        with VideoFileClip(str(path)) as v:
            return float(v.duration or 0.0)
    except Exception as e:
        print(f"⚠️  Could not read video duration: {e}")
        return 0.0


def list_downloaded_videos(downloads_dir=DOWNLOADS_DIR):
    """Return a sorted list of downloaded video file Paths."""
    try:
        return sorted(
            (p for p in downloads_dir.iterdir()
             if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS),
            key=lambda p: p.stat().st_mtime, reverse=True)
    except FileNotFoundError:
        return []


def clear_downloads(downloads_dir=DOWNLOADS_DIR):
    """Delete all downloaded videos. Returns (count_deleted, bytes_freed)."""
    count, freed = 0, 0
    for p in list_downloaded_videos(downloads_dir):
        try:
            size = p.stat().st_size
            p.unlink()
            count += 1
            freed += size
            # Remove the sibling cached transcript, if any.
            cache = p.with_name(p.stem + '.transcript.json')
            if cache.exists():
                cache.unlink()
        except OSError as e:
            print(f"⚠️  Could not delete {p.name}: {e}")
    return count, freed


def generate_random_clips(duration, num_clips, min_duration, max_duration):
    """
    Generates random clip start and end times as a fallback.

    Args:
        duration (float): The total duration of the video.
        num_clips (int): The number of clips to generate.
        min_duration (int): The minimum duration of each clip.
        max_duration (int): The maximum duration of each clip.

    Returns:
        list: A list of dictionaries, each representing a random clip.
    """
    clips = []
    for i in range(num_clips):
        clip_duration = random.uniform(min_duration, max_duration)
        if duration - clip_duration <= 0:
            continue
        start = random.uniform(0, duration - clip_duration)
        clips.append({
            'start': start,
            'end': start + clip_duration,
            'title': f'🔥 Must-see moment {i+1} 👀',
            'virality_score': 30,
            'hook_type': 'general',
            'duration': clip_duration,
            'description': '🔥 Wild stream moment 😳 you had to be there 👀 #shorts #fyp #viral #twitch #clips'
        })
    return clips
