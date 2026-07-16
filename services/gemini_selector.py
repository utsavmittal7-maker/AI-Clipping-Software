import json
import random
import google.generativeai as genai

class GeminiSelector:
    """
    Uses the Gemini AI model to select the most viral clips from a transcript.
    """
    def __init__(self, api_key):
        """
        Initializes the GeminiSelector with an API key.

        Args:
            api_key (str): The API key for the Gemini AI model.
        """
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        # Use the "-latest" alias so the app keeps working as Google retires
        # specific model versions (older pinned names 404 for new API keys).
        self.model = genai.GenerativeModel('gemini-flash-latest')

    def select_clips(self, segments, video_duration, n, min_dur, max_dur,
                     video_title="", video_author=""):
        """
        Selects the most viral clips from a transcript using the Gemini AI model
        and writes a catchy, streamer-aware description for each one.

        Args:
            segments (list): A list of transcript segments with timestamps.
            video_duration (float): The total duration of the video.
            n (int): The number of clips to select.
            min_dur (int): The minimum duration of each clip.
            max_dur (int): The maximum duration of each clip.
            video_title (str): Original video title (often lists the streamers).
            video_author (str): Original channel name.

        Returns:
            list: A list of dictionaries, each representing a selected clip.
        """
        segments_text = []
        for i, seg in enumerate(segments):
            segments_text.append(f"[{seg['start']:.1f}s-{seg['end']:.1f}s]: {seg['text']}")

        transcript_with_timestamps = "\n".join(segments_text)

        source_context = (
            f"ORIGINAL VIDEO TITLE: {video_title or 'unknown'}\n"
            f"ORIGINAL CHANNEL: {video_author or 'unknown'}\n"
        )

        prompt = f"""You are an expert at creating viral short-form content like Opus.pro. Analyze this transcript with precise timestamps and select the {n} BEST viral clips.

CRITICAL RULES:
1. Each clip MUST start at the EXACT beginning of a sentence/thought and end at the EXACT completion of that sentence/thought
2. Never cut off mid-sentence or mid-word - clips must be complete thoughts
3. Each clip must be {min_dur}-{max_dur} seconds long
4. Clips cannot overlap and must use the EXACT timestamps provided
5. Focus on complete viral moments: hooks, revelations, advice, stories, funny moments

SELECTION CRITERIA (prioritize):
- Complete engaging stories or thoughts
- Surprising facts or revelations
- Actionable advice or tips
- Emotional moments or reactions
- Quotable one-liners with context
- Question-answer pairs

For EACH clip also write a "description" - a caption for TikTok / Instagram Reels / YouTube Shorts:
- Voice: Gen-Z, punchy, playful, high-energy. Sound like a fan edit, not a press release.
- Identify the streamer(s) actually featured and name them. Use the ORIGINAL VIDEO TITLE and CHANNEL below as the source of truth for names/handles.
- ACCURACY IS CRITICAL: never invent or guess a streamer's name. If you are not sure who is speaking, say "this streamer" instead of guessing a wrong name.
- Keep it to 1-2 short sentences, add a few fitting emojis, and end with 3-5 relevant hashtags (include the streamer name as a hashtag when known, plus tags like #shorts #fyp #viral #twitch).

{source_context}
VIDEO DURATION: {video_duration} seconds

TRANSCRIPT WITH EXACT TIMESTAMPS:
{transcript_with_timestamps}

Return ONLY valid JSON with EXACT timestamps from the transcript:
{{
  "clips": [
    {{
      "start": 34.5,
      "end": 67.2,
      "title": "Complete thought or hook",
      "virality_score": 85,
      "hook_type": "story_reveal",
      "reason": "Complete engaging story with clear beginning and end",
      "description": "Bro really said that on stream 💀🔥 @streamer went crazy #streamer #shorts #fyp #twitch"
    }}
  ]
}}"""

        try:
            print("🤖 AI analyzing transcript for complete viral thoughts...")
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            data = json.loads(response.text)
            validated_clips = []

            for clip_data in data.get('clips', []):
                start = clip_data.get('start')
                end = clip_data.get('end')
                title = clip_data.get('title', 'Untitled')
                score = clip_data.get('virality_score', 0)
                hook_type = clip_data.get('hook_type', 'general')
                description = (clip_data.get('description') or '').strip()

                if start is None or end is None:
                    continue

                start, end = float(start), float(end)
                duration = end - start

                if duration > max_dur:
                    end = start + max_dur
                    duration = max_dur

                if min_dur <= duration <= max_dur and start < end and end <= video_duration:
                    validated_clips.append({
                        'start': start,
                        'end': end,
                        'title': title,
                        'virality_score': score,
                        'hook_type': hook_type,
                        'duration': duration,
                        'description': description or self._fallback_description(title, video_title)
                    })

            if not validated_clips:
                raise ValueError("AI did not return any valid clips.")

            validated_clips.sort(key=lambda x: x['virality_score'], reverse=True)
            print(f"✅ AI selected {len(validated_clips)} complete viral clips:")
            for i, clip in enumerate(validated_clips[:n], 1):
                print(f"  {i}. {clip['title']} (Score: {clip['virality_score']}, Type: {clip['hook_type']})")

            return validated_clips[:n]

        except Exception as e:
            print(f"❌ AI clip selection failed: {e}. Using fallback method.")
            return self._fallback_selection(segments, video_duration, n, min_dur, max_dur, video_title)

    @staticmethod
    def _fallback_description(clip_title, video_title):
        """A simple description used when the AI doesn't provide one."""
        base = (video_title or clip_title or 'Wild stream moment').strip()
        return f"🔥 {base} 😳 you had to be there 👀 #shorts #fyp #viral #twitch #clips"

    def _fallback_selection(self, segments, video_duration, n, min_dur, max_dur,
                            video_title=""):
        # Start each fallback clip at a real segment boundary (so it begins on a
        # sentence) but always give it a full min_dur..max_dur length. The old
        # logic used a single segment's length, which produced sub-second clips.
        clips = []
        used_starts = set()
        candidates = [
            seg['start'] for seg in segments
            if seg['start'] + min_dur <= video_duration
        ]
        random.shuffle(candidates)

        for start in candidates:
            if len(clips) >= n:
                break
            if start in used_starts:
                continue
            used_starts.add(start)

            duration = min(max_dur, video_duration - start)
            if duration < min_dur:
                continue

            clips.append({
                'start': start,
                'end': start + duration,
                'title': f'Fallback clip {len(clips) + 1}',
                'virality_score': 50,
                'hook_type': 'general',
                'duration': duration,
                'description': self._fallback_description('', video_title)
            })

        return clips
