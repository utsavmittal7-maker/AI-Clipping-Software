"""
Lightweight, dependency-free-ish editing helpers used by the video pipeline:

- auto_cleanup: remove filler words and long silences from a clip and remap the
  word timings so captions stay in sync.
- add_background_music / add_logo / add_intro_outro: branding & music overlays.
- make_thumbnail: save a cover image for a clip.
- interactive_review / apply_edit_command: let the user trim/drop clips.

Everything is written defensively: any failure falls back to the original clip
so a single feature can never break the whole render.
"""
import os
import string

# MoviePy 1.0.3's clip.resize() references PIL.Image.ANTIALIAS, which Pillow 10+
# removed. Restore the alias so resize-based features (logo, intro/outro) work
# on modern Pillow.
from PIL import Image as _PILImage
if not hasattr(_PILImage, 'ANTIALIAS'):
    try:
        _PILImage.ANTIALIAS = _PILImage.Resampling.LANCZOS
    except AttributeError:
        _PILImage.ANTIALIAS = _PILImage.LANCZOS

from moviepy.editor import (
    VideoFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip,
    AudioFileClip, CompositeAudioClip,
)

# Common English filler / crutch words to drop when tightening a clip.
FILLER_WORDS = {
    'um', 'umm', 'ummm', 'uh', 'uhh', 'uhhh', 'erm', 'ah', 'ahh', 'eh',
    'hmm', 'mm', 'mhm', 'uhm', 'em',
}


def _clean(word):
    return word.lower().strip(string.punctuation + string.whitespace)


# --------------------------------------------------------------- auto cleanup
def compute_keep_intervals(words_rel, clip_duration, silence_gap=0.6,
                           silence_keep=0.15, remove_fillers=True):
    """
    Return a list of (start, end) intervals to KEEP after removing filler words
    and trimming silent gaps longer than ``silence_gap`` seconds.

    ``words_rel`` are word dicts with 'start'/'end' relative to the clip (0-based).
    """
    removes = []

    if remove_fillers:
        for w in words_rel:
            if _clean(w['word']) in FILLER_WORDS:
                removes.append((max(0.0, w['start'] - 0.02),
                                min(clip_duration, w['end'] + 0.02)))

    pts = sorted(words_rel, key=lambda w: w['start'])
    if pts:
        # leading silence
        if pts[0]['start'] > silence_gap:
            removes.append((silence_keep, pts[0]['start'] - silence_keep))
        # gaps between words
        for i in range(len(pts) - 1):
            gap_start, gap_end = pts[i]['end'], pts[i + 1]['start']
            if gap_end - gap_start > silence_gap:
                removes.append((gap_start + silence_keep, gap_end - silence_keep))
        # trailing silence
        if clip_duration - pts[-1]['end'] > silence_gap:
            removes.append((pts[-1]['end'] + silence_keep,
                            clip_duration - silence_keep))

    # clamp + drop tiny removes, then merge overlaps
    removes = [(max(0.0, a), min(clip_duration, b)) for a, b in removes if b - a > 0.05]
    removes.sort()
    merged = []
    for a, b in removes:
        if merged and a <= merged[-1][1] + 0.01:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))

    # invert removes -> keeps
    keeps, cursor = [], 0.0
    for a, b in merged:
        if a > cursor:
            keeps.append((cursor, a))
        cursor = max(cursor, b)
    if cursor < clip_duration:
        keeps.append((cursor, clip_duration))

    return [(a, b) for a, b in keeps if b - a > 0.12]


def remap_words(words_rel, keeps):
    """Map words into the concatenated (kept) timeline; drop removed words."""
    new_words, offset = [], 0.0
    for a, b in keeps:
        length = b - a
        for w in words_rel:
            s, e = max(w['start'], a), min(w['end'], b)
            if e - s > 0.05:
                new_words.append({
                    'word': w['word'],
                    'start': offset + (s - a),
                    'end': offset + (e - a),
                })
        offset += length
    return new_words


def auto_cleanup(subclip, words_rel, silence_gap=0.6, silence_keep=0.15,
                 min_result=3.0, max_remove_ratio=0.5):
    """
    Remove fillers + long silences from ``subclip``.

    Returns (clip, words_rel, removed_seconds). Falls back to the original clip
    (removed=0) when there's nothing worth cutting or cleanup would remove too
    much of the clip.
    """
    duration = subclip.duration
    keeps = compute_keep_intervals(words_rel, duration, silence_gap, silence_keep)
    if not keeps:
        return subclip, words_rel, 0.0

    kept = sum(b - a for a, b in keeps)
    removed = duration - kept
    if kept < min_result or removed <= 0.3 or (removed / duration) > max_remove_ratio:
        return subclip, words_rel, 0.0

    pieces = [subclip.subclip(a, b) for a, b in keeps]
    cleaned = concatenate_videoclips(pieces, method='compose')
    return cleaned, remap_words(words_rel, keeps), removed


# --------------------------------------------------------------- music/brand
def add_background_music(clip, music_path, volume=0.12):
    if not music_path or not os.path.exists(music_path):
        return clip
    try:
        music = AudioFileClip(music_path)
        if music.duration < clip.duration:
            try:
                import moviepy.audio.fx.all as afx
                music = afx.audio_loop(music, duration=clip.duration)
            except Exception:
                music = music.subclip(0, music.duration)
        else:
            music = music.subclip(0, clip.duration)
        music = music.volumex(volume)
        new_audio = (CompositeAudioClip([clip.audio, music])
                     if clip.audio is not None else music)
        print(f"    🎵 Added background music (vol {volume})")
        return clip.set_audio(new_audio)
    except Exception as e:
        print(f"    ⚠️ Could not add background music: {e}")
        return clip


def add_logo(clip, logo_path, rel_width=0.20, margin_ratio=0.035, opacity=0.85):
    if not logo_path or not os.path.exists(logo_path):
        return clip
    try:
        logo = ImageClip(logo_path)
        logo = logo.resize(width=int(clip.w * rel_width))
        margin = int(clip.h * margin_ratio)
        logo = (logo.set_duration(clip.duration)
                    .set_position(('center', margin))
                    .set_opacity(opacity))
        print("    🏷️ Added logo / watermark")
        return CompositeVideoClip([clip, logo])
    except Exception as e:
        print(f"    ⚠️ Could not add logo: {e}")
        return clip


def add_intro_outro(clip, intro_path='', outro_path=''):
    def _load(path):
        try:
            return VideoFileClip(path).resize(newsize=(clip.w, clip.h))
        except Exception as e:
            print(f"    ⚠️ Could not load {path}: {e}")
            return None

    parts = []
    if intro_path and os.path.exists(intro_path):
        ic = _load(intro_path)
        if ic:
            parts.append(ic)
    parts.append(clip)
    if outro_path and os.path.exists(outro_path):
        oc = _load(outro_path)
        if oc:
            parts.append(oc)

    if len(parts) == 1:
        return clip
    try:
        print("    🎬 Added intro/outro")
        return concatenate_videoclips(parts, method='compose')
    except Exception as e:
        print(f"    ⚠️ Could not add intro/outro: {e}")
        return clip


# ----------------------------------------------------------------- thumbnail
def make_thumbnail(clip, title, out_path, font_path=None):
    """Save a cover image (frame + title bar) for a clip. Returns True on success."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        t = min(max(0.5, clip.duration * 0.3), max(0.0, clip.duration - 0.1))
        frame = clip.get_frame(t)
        img = Image.fromarray(frame).convert('RGB')
        draw = ImageDraw.Draw(img, 'RGBA')
        W, H = img.size

        # translucent bar across the lower portion for legibility
        draw.rectangle([0, int(H * 0.7), W, H], fill=(0, 0, 0, 130))

        font_size = max(28, int(W * 0.075))
        try:
            font = ImageFont.truetype(font_path, font_size) if font_path \
                else ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        # wrap title to fit width
        words, lines, cur = (title or '').upper().split(), [], ''
        for w in words:
            trial = (cur + ' ' + w).strip()
            if cur and draw.textlength(trial, font=font) > W * 0.9:
                lines.append(cur)
                cur = w
            else:
                cur = trial
        if cur:
            lines.append(cur)
        lines = lines[:3]

        line_h = int(font_size * 1.2)
        y = H - int(H * 0.06) - line_h * len(lines)
        for line in lines:
            tw = draw.textlength(line, font=font)
            x = (W - tw) // 2
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255),
                      stroke_width=max(2, font_size // 12), stroke_fill=(0, 0, 0, 255))
            y += line_h

        img.save(out_path, quality=90)
        return True
    except Exception as e:
        print(f"    ⚠️ Could not create thumbnail: {e}")
        return False


# ------------------------------------------------------------------- review
def apply_edit_command(clip_specs, command, video_duration):
    """
    Apply a single review command to a list of clip specs (1-indexed for users).

    Supported:
      drop N [M ...]        remove clips
      set N START END       set clip N to START..END seconds
    Returns (new_specs, message).
    """
    parts = command.strip().split()
    if not parts:
        return clip_specs, ""
    action = parts[0].lower()

    if action in ('drop', 'remove', 'delete'):
        try:
            idxs = sorted({int(p) for p in parts[1:]}, reverse=True)
        except ValueError:
            return clip_specs, "⚠️ Usage: drop <clip number(s)>"
        specs = list(clip_specs)
        removed = []
        for i in idxs:
            if 1 <= i <= len(specs):
                removed.append(i)
                specs.pop(i - 1)
        if not removed:
            return clip_specs, "⚠️ No valid clip numbers to drop."
        return specs, f"🗑️ Dropped clip(s): {sorted(removed)}"

    if action in ('set', 'trim', 'edit'):
        try:
            idx = int(parts[1]); start = float(parts[2]); end = float(parts[3])
        except (ValueError, IndexError):
            return clip_specs, "⚠️ Usage: set <clip number> <start> <end>"
        if not (1 <= idx <= len(clip_specs)):
            return clip_specs, f"⚠️ No clip #{idx}."
        if start < 0 or end > video_duration or start >= end:
            return clip_specs, "⚠️ Invalid times for this video."
        specs = [dict(c) for c in clip_specs]
        specs[idx - 1]['start'] = start
        specs[idx - 1]['end'] = end
        specs[idx - 1]['duration'] = end - start
        return specs, f"✂️ Clip {idx} set to {start:.1f}s–{end:.1f}s"

    return clip_specs, "⚠️ Commands: 'drop N', 'set N START END', or Enter to render."


def _print_specs(clip_specs):
    print("\n✂️  Review clips before rendering:")
    for i, c in enumerate(clip_specs, 1):
        print(f"  {i}. {c.get('title', 'Clip')}  "
              f"[{c['start']:.1f}s–{c['end']:.1f}s, {c.get('duration', c['end']-c['start']):.0f}s]  "
              f"score {c.get('virality_score', 0)}")


def interactive_review(clip_specs, video_duration, input_fn=input):
    """Interactive trim/drop loop. Returns the possibly-edited clip specs."""
    specs = [dict(c) for c in clip_specs]
    _print_specs(specs)
    print("\n  Type a command and press Enter, or just press Enter to render all.")
    print("  • drop 2        (remove clip 2)")
    print("  • set 1 12 45   (set clip 1 to 12s–45s)")
    while True:
        try:
            cmd = input_fn("  ✏️  edit> ").strip()
        except EOFError:
            break
        if cmd == '' or cmd.lower() in ('done', 'render', 'go', 'ok'):
            break
        specs, msg = apply_edit_command(specs, cmd, video_duration)
        if msg:
            print("   " + msg)
        if not specs:
            print("   ⚠️ All clips removed - nothing to render.")
            break
        _print_specs(specs)
    return specs
