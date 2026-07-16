"""
Configuration for the YouTube Viral Clipper application.

This module loads environment variables and sets up default configurations
for the application. It includes settings for API keys, directories,
and model configurations.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Load from environment or use defaults
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'YOUR_API_KEY_HERE')
OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', './clips'))
TEMP_DIR = Path(os.getenv('TEMP_DIR', './temp'))
# Whisper model size (options: tiny, base, small, medium, large-v2)
# Using medium model for better performance while maintaining good accuracy
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'medium')
# YOUTUBE_COOKIES_CONTENT is no longer used as we've switched to pytube
YOUTUBE_USER_AGENT = os.getenv('YOUTUBE_USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')


def _flag(name, default):
    """Read a boolean-ish env var ('true'/'1'/'yes' -> True)."""
    return os.getenv(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


def _float(name, default):
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return float(default)


# --- Editing feature toggles ---
# Remove filler words ("um", "uh", ...) and long silent gaps to tighten clips.
AUTO_CLEANUP = _flag('AUTO_CLEANUP', True)
# Ask you to review / trim / drop clips before rendering.
REVIEW_CLIPS = _flag('REVIEW_CLIPS', False)
# Save a cover image (.jpg) for each clip.
GENERATE_THUMBNAILS = _flag('GENERATE_THUMBNAILS', True)
# Save a short AI summary of the whole video.
GENERATE_SUMMARY = _flag('GENERATE_SUMMARY', True)

# Auto-cleanup tuning.
SILENCE_GAP = _float('SILENCE_GAP', 0.6)      # gap (s) longer than this is trimmed
SILENCE_KEEP = _float('SILENCE_KEEP', 0.15)   # keep this much of a trimmed gap

# --- Branding / music assets (optional; used only if the file exists) ---
MUSIC_PATH = os.getenv('MUSIC_PATH', '').strip()
MUSIC_VOLUME = _float('MUSIC_VOLUME', 0.12)   # 0.0-1.0, background music level
LOGO_PATH = os.getenv('LOGO_PATH', '').strip()
INTRO_PATH = os.getenv('INTRO_PATH', '').strip()
OUTRO_PATH = os.getenv('OUTRO_PATH', '').strip()

# Create directories
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

if "YOUR_API_KEY_HERE" in GEMINI_API_KEY:
    print("⚠️ WARNING: Please replace 'YOUR_API_KEY_HERE' with your actual Google AI Studio API key in your .env file.")
