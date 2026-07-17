import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from services.video_processor import VideoProcessor
from styles.caption_styles import CAPTION_STYLES
from config import OUTPUT_DIR, TEMP_DIR

# Ensure output is not buffered
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# Function to print with immediate flush
def log(message):
    """Prints a message to the console with immediate flushing."""
    print(message, flush=True)

def display_caption_styles():
    """Displays the available caption styles to the user."""
    styles = CAPTION_STYLES
    log("\n🎨 Available Caption Styles (No Strokes):")
    log("=" * 50)
    for i, (key, value) in enumerate(styles.items(), 1):
        log(f"{i}. {key} - {value['name']}")
    log("=" * 50)
    return list(styles.keys())

def validate_youtube_url(url):
    """
    Validates that the provided URL is a valid YouTube URL.

    Args:
        url (str): The URL to validate.

    Returns:
        bool: True if the URL is a valid YouTube URL, False otherwise.
    """
    if not url:
        return False
        
    # Basic validation
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return False
        
    # Check if it's a YouTube domain
    if not ('youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc):
        return False

    return True


def resolve_source(raw):
    """
    Turn raw user input into a usable source. Handles:
      - 'clear'  -> delete all downloaded videos, then abort this run
      - 'list'   -> pick from already-downloaded videos
      - a local video file path
      - a YouTube URL

    Returns the resolved source string, or None to abort.
    """
    from utils.helpers import list_downloaded_videos, clear_downloads

    raw = (raw or "").strip().strip('"').strip("'")
    if not raw:
        log("❌ Error: Nothing entered.")
        return None
    low = raw.lower()

    if low == 'clear':
        vids = list_downloaded_videos()
        if not vids:
            log("📁 No downloaded videos to delete.")
            return None
        confirm = input(
            f"🗑️  Delete ALL {len(vids)} downloaded video(s)? (y/N): ").strip().lower()
        if confirm in ('y', 'yes'):
            count, freed = clear_downloads()
            log(f"✅ Deleted {count} video(s), freed {freed/(1024*1024):.1f} MB.")
        else:
            log("Cancelled - nothing deleted.")
        return None

    if low == 'list':
        vids = list_downloaded_videos()
        if not vids:
            log("📁 No downloaded videos yet. Paste a YouTube URL to download one.")
            return None
        log("\n📂 Already-downloaded videos:")
        for i, p in enumerate(vids, 1):
            log(f"  {i}. {p.name} ({p.stat().st_size/(1024*1024):.1f} MB)")
        choice = input(f"🎯 Select a video to clip (1-{len(vids)}): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(vids):
                return str(vids[idx])
        except ValueError:
            pass
        log("❌ Invalid selection.")
        return None

    # A local video file the user pointed us at.
    if os.path.isfile(raw):
        return raw

    # Otherwise treat it as a YouTube URL.
    if validate_youtube_url(raw):
        return raw

    log("❌ Error: Not a valid YouTube URL or an existing local video file.")
    return None


def main(url=None):
    """
    The main function of the YouTube Viral Clipper application.

    Args:
        url (str, optional): The YouTube URL to process. Defaults to None.
    """
    log("🚀 === YOUTUBE VIRAL CLIPPER === 🚀")
    log("✨ Features: AI Clip Selection | Smart Face Tracking | Word-by-Word Captions")
    log("")

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # Ensure temp directory exists
    os.makedirs(TEMP_DIR, exist_ok=True)
    log(f"📁 Output directory: {OUTPUT_DIR}")
    log(f"📁 Temp directory: {TEMP_DIR}")

    # Resolve the source. Keep asking until we get a valid URL / local file so a
    # stray 'list'/'clear'/typo never drops the user back to the shell.
    source = resolve_source(url) if url else None
    if not source:
        log("🔗 Enter a YouTube URL, or the path to a local video file.")
        log("   • type 'list'  to clip from an already-downloaded video")
        log("   • type 'clear' to delete all downloaded videos")
        log("   • type 'quit'  to exit")
        while not source:
            raw = input("👉 ").strip()
            if raw.lower() in ('quit', 'exit', 'q'):
                log("👋 Exiting.")
                return
            source = resolve_source(raw)
    url = source

    try:
        num_clips = int(input("📊 Number of viral clips [3]: ") or "3")
        max_duration = int(input("⏱️  Max seconds per clip [60]: ") or "60")
        min_duration = int(input("⏱️  Min seconds per clip [20]: ") or "20")

        if min_duration >= max_duration:
            log("❌ Error: Min duration must be less than max duration.")
            return

        style_keys = display_caption_styles()
        style_choice = input(f"🎨 Select caption style (1-{len(style_keys)}) [1]: ").strip() or "1"

        try:
            style_index = int(style_choice) - 1
            if 0 <= style_index < len(style_keys):
                selected_style = style_keys[style_index]
            else:
                selected_style = 'clean_white'
                log("⚠️  Invalid choice, using default: Clean White")
        except:
            selected_style = 'clean_white'
            log("⚠️  Invalid input, using default: Clean White")

        review_choice = input(
            "✂️  Review & trim clips before rendering? (y/N): ").strip().lower()
        review = review_choice in ('y', 'yes')

        save_choice = input(
            "💾 Save clips to: (1) This PC  (2) Google Drive [1]: ").strip() or "1"
        upload = save_choice == "2"
        if upload:
            log("☁️  Clips will be uploaded to Google Drive.")
        else:
            log("💻 Clips will be saved locally in the 'clips' folder.")

        log("\n" + "="*70)
        log("🎬 STARTING VIDEO PROCESSING...")
        log("="*70)

        log("⏳ Initializing video processor...")
        processor = VideoProcessor(caption_style=selected_style)
        log("✅ Video processor initialized")

        # Add a small delay to ensure logs are displayed
        time.sleep(0.5)

        outputs, title = processor.process_video(
            url, num_clips, min_duration, max_duration, review=review, upload=upload)

        log("\n" + "="*70)
        log("🎉 VIRAL CLIPS GENERATED!")
        log("="*70)
        log(f"📹 Source: '{title}'")
        log(f"📁 Location: {OUTPUT_DIR.resolve()}")
        log(f"🎨 Caption Style: {processor.caption_maker.styles[selected_style]['name']}")

        total_size = 0
        log("\n📋 Generated Clips:")
        for f in outputs:
            path = Path(f)
            try:
                if path.exists():
                    size_bytes = path.stat().st_size
                    size_mb = size_bytes / (1024 * 1024)
                    total_size += size_mb
                    log(f"  - {path.name} ({size_mb:.2f} MB)")
            except Exception as e:
                log(f"  - {path.name} (size unknown: {e})")
        log(f"\n💾 Total Size: {total_size:.2f} MB")
        log("\n✅ Done! Enjoy your viral clips!")

    except ValueError as e:
        log(f"\n❌ Input Error: {e}")
    except FileNotFoundError as e:
        log(f"\n❌ File Error: {e}")
    except Exception as e:
        log(f"\n❌ An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        log("\nPlease check the error message above and try again.")

if __name__ == "__main__":
    try:
        # Check if a URL / path was provided as a command-line argument.
        # resolve_source() handles URLs, local file paths, and 'list'/'clear'.
        url = sys.argv[1].strip() if len(sys.argv) > 1 else None
        
        # Create necessary directories
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(Path("./temp"), exist_ok=True)
        
        main(url)
    except KeyboardInterrupt:
        print("\n\n🛑 Process interrupted by user. Exiting gracefully.")
    except Exception as e:
        print(f"\n\n❌ Critical error: {e}")
        print("Please report this issue if it persists.")
