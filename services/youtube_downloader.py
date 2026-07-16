import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Replace pytube with pytubefix
from pytubefix import YouTube
from pytubefix.exceptions import PytubeFixError

from config import TEMP_DIR, YOUTUBE_USER_AGENT


class YouTubeDownloader:
    """
    Handles the downloading of YouTube videos.

    This class uses the pytubefix library to download a YouTube video
    and prepares it for further processing.
    """
    def __init__(self, temp_dir=TEMP_DIR):
        """
        Initializes the YouTubeDownloader.

        Args:
            temp_dir (Path, optional): The directory to save temporary files.
                                       Defaults to TEMP_DIR from config.
        """
        self.temp_dir = temp_dir
        self.video_author = ""

    def _sanitize_filename(self, filename):
        """
        Sanitizes a filename by removing invalid characters.

        Args:
            filename (str): The filename to sanitize.

        Returns:
            str: The sanitized filename.
        """
        if not filename:
            return "unknown_title"
            
        # Replace characters that are problematic in filenames
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in invalid_chars:
            filename = filename.replace(char, '_')
            
        # Limit filename length to avoid path too long errors
        if len(filename) > 100:
            filename = filename[:97] + '...'
            
        return filename

    @staticmethod
    def get_video_id(url):
        """
        Extracts the video ID from a YouTube URL.

        Handles all common forms:
          - youtube.com/watch?v=ID
          - youtu.be/ID
          - youtube.com/live/ID   (live streams / their VODs)
          - youtube.com/shorts/ID
          - youtube.com/embed/ID
          - youtube.com/v/ID

        Args:
            url (str): The YouTube URL.

        Returns:
            str: The video ID, or None if not found.
        """
        parsed = urlparse(url)
        host = parsed.netloc.lower()

        # Short youtu.be links: the id is the first path segment.
        if 'youtu.be' in host:
            first = [p for p in parsed.path.split('/') if p]
            return first[0] if first else None

        if 'youtube.com' in host or 'youtube-nocookie.com' in host:
            # Classic watch?v=ID
            v = parse_qs(parsed.query).get('v', [None])[0]
            if v:
                return v
            # Path-based forms: /live/ID, /shorts/ID, /embed/ID, /v/ID
            parts = [p for p in parsed.path.split('/') if p]
            if len(parts) >= 2 and parts[0] in ('live', 'shorts', 'embed', 'v'):
                return parts[1]

        return None

    def download(self, url):
        """
        Downloads a YouTube video from the given URL.

        Args:
            url (str): The URL of the YouTube video.

        Returns:
            tuple: A tuple containing the path to the downloaded video,
                   the video title, and its duration.
        """
        print(f"🔗 Processing YouTube URL: {url}")
        video_id = self.get_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL provided.")
        print(f"✅ Extracted video ID: {video_id}")

        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)
        print(f"✅ Temporary directory ready: {self.temp_dir}")
        
        # Set up output path - use absolute path to avoid any path issues
        output_path = os.path.abspath(str(self.temp_dir))
        output_filename = f"{video_id}.mp4"
        print(f"📂 Output will be saved to: {os.path.join(output_path, output_filename)}")
        
        try:
            # Create YouTube object with custom options
            # Note: pytube doesn't directly support setting user agent via class attributes
            # We'll just create the YouTube object normally
            
            print(f"Downloading YouTube video with ID: {video_id}")
            print(f"⏳ Fetching video metadata...")
            # Create YouTube object
            yt = YouTube(url)
            print(f"✅ Connected to YouTube API successfully")
            
            # Get video information and sanitize title
            title = self._sanitize_filename(yt.title)
            duration = yt.length
            try:
                self.video_author = yt.author or ""
            except Exception:
                self.video_author = ""
            
            print(f"Video title: {title}")
            print(f"Video duration: {duration} seconds ({duration//60}m {duration%60}s)")
            print(f"Video author: {yt.author}")
            print(f"⏳ Selecting best quality stream...")

            # Prefer a high-resolution adaptive video (up to 1080p) merged with
            # the best audio track. This is what makes the final clips sharp -
            # progressive streams alone are usually capped at 720p (often 360p).
            video_path = self._download_high_quality(yt, output_path, video_id)

            if not video_path:
                # Fallback: a single progressive (video+audio) mp4 file.
                print("⚠️ Falling back to a progressive stream (lower resolution).")
                stream = (
                    yt.streams
                    .filter(progressive=True, file_extension='mp4')
                    .order_by('resolution')
                    .desc()
                    .first()
                )
                if not stream:
                    print("⚠️ No progressive stream found, trying any mp4 stream")
                    stream = (
                        yt.streams
                        .filter(file_extension='mp4')
                        .order_by('resolution')
                        .desc()
                        .first()
                    )
                if not stream:
                    raise ValueError("No suitable video stream found")

                print(f"Selected stream: {stream.resolution}, {stream.mime_type}")
                print(f"⏳ Downloading video to {output_path}...")
                try:
                    video_path = stream.download(output_path=output_path, filename=output_filename)
                except OSError as e:
                    print(f"OS Error during download: {e}")
                    video_path = stream.download(output_path=output_path, filename=f"youtube_video_{video_id}.mp4")

            # Verify the file exists and has content
            if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
                raise FileNotFoundError(f"Downloaded file is missing or empty: {video_path}")

            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            print(f"✅ Download complete! File size: {file_size_mb:.2f} MB")

            video_path = Path(video_path)
            print(f"Download complete: {video_path}")

            return video_path, title, duration
            
        except PytubeFixError as e:
            print(f"PytubeFixError: {str(e)}")
            raise Exception(f"Failed to download video: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise Exception(f"Unexpected error during download: {str(e)}")

        # This should never be reached, but just in case
        video_path = Path(output_path) / output_filename
        if not video_path.exists():
            raise FileNotFoundError("Failed to download the video file.")

        return video_path, "Unknown Title", 0

    def _download_high_quality(self, yt, output_path, video_id):
        """
        Download the best adaptive video (up to 1080p) plus the best audio
        track and merge them with ffmpeg.

        Returns the merged file path on success, or None if a high-quality
        download/merge isn't possible (the caller then falls back to a
        progressive stream).
        """
        import shutil
        import subprocess

        if not shutil.which('ffmpeg'):
            print("⚠️ ffmpeg not on PATH - skipping high-quality merge.")
            return None

        def _res(stream):
            try:
                return int((stream.resolution or '0p').rstrip('p'))
            except (ValueError, AttributeError):
                return 0

        try:
            video_streams = [
                s for s in yt.streams.filter(
                    adaptive=True, only_video=True, file_extension='mp4')
                if 0 < _res(s) <= 1080
            ]
            if not video_streams:
                return None
            video_stream = max(video_streams, key=_res)

            audio_stream = (
                yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            )
            if not audio_stream:
                return None

            print(f"🎬 Best quality: {video_stream.resolution} video + "
                  f"{getattr(audio_stream, 'abr', '?')} audio (will be merged)")

            v_tmp = os.path.join(output_path, f"{video_id}_video.mp4")
            a_tmp = os.path.join(output_path, f"{video_id}_audio.mp4")
            print("⏳ Downloading video track...")
            video_stream.download(output_path=output_path,
                                  filename=f"{video_id}_video.mp4")
            print("⏳ Downloading audio track...")
            audio_stream.download(output_path=output_path,
                                  filename=f"{video_id}_audio.mp4")

            merged = os.path.join(output_path, f"{video_id}.mp4")
            print("⏳ Merging video + audio with ffmpeg...")
            result = subprocess.run(
                ['ffmpeg', '-y', '-i', v_tmp, '-i', a_tmp,
                 '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                 '-movflags', '+faststart', '-shortest', merged],
                capture_output=True, text=True
            )

            for tmp in (v_tmp, a_tmp):
                try:
                    if os.path.exists(tmp):
                        os.remove(tmp)
                except OSError:
                    pass

            if (result.returncode != 0 or not os.path.exists(merged)
                    or os.path.getsize(merged) == 0):
                tail = (result.stderr or '')[-300:]
                print(f"⚠️ ffmpeg merge failed, will fall back. {tail}")
                return None

            return merged
        except Exception as e:
            print(f"⚠️ High-quality download failed ({e}); will fall back.")
            return None
