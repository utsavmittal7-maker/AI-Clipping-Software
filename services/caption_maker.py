import os
import string
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, CompositeVideoClip

from styles.caption_styles import CAPTION_STYLES, HIGHLIGHT_KEYWORDS, EMOJI_MAP


def _windows_font(name):
    """Absolute path to a font in the Windows Fonts directory."""
    windir = os.environ.get('WINDIR', 'C:\\Windows')
    return os.path.join(windir, 'Fonts', name)


class CaptionMaker:
    """
    Creates and adds styled, phrase-by-phrase captions (outline, highlight box,
    shadow and optional emoji) to a video clip. Words are grouped into short
    readable phrases that stay on screen for the whole phrase instead of
    flashing one word at a time.
    """

    # Phrase grouping tuning.
    MAX_WORDS = 5          # words per caption line-group
    MAX_CHARS = 30         # characters before forcing a new phrase
    MAX_GAP = 0.7          # seconds of silence that ends a phrase
    MAX_DURATION = 3.2     # seconds before forcing a new phrase
    MIN_DURATION = 1.1     # keep short phrases on screen at least this long

    def __init__(self, selected_style='bold_white'):
        self.styles = CAPTION_STYLES
        if selected_style not in self.styles:
            selected_style = next(iter(self.styles))
        self.selected_style = selected_style
        self.highlight_keywords = HIGHLIGHT_KEYWORDS
        self.font_paths = self.find_available_fonts()
        self.emoji_font_path = self.find_emoji_font()
        self._font_cache = {}

    # ------------------------------------------------------------------ fonts
    def find_available_fonts(self):
        """Resolve one real font file per logical font type, per platform."""
        font_collections = {
            'impact': [
                _windows_font('impact.ttf'),
                '/System/Library/Fonts/Supplemental/Impact.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
            ],
            'bold': [
                _windows_font('arialbd.ttf'),
                _windows_font('calibrib.ttf'),
                '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
                '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
            ],
            'bolditalic': [
                _windows_font('arialbi.ttf'),
                '/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf',
            ],
            'regular': [
                _windows_font('arial.ttf'),
                '/System/Library/Fonts/Supplemental/Arial.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/TTF/DejaVuSans.ttf',
            ],
        }

        found = {}
        for font_type, paths in font_collections.items():
            found[font_type] = None
            for path in paths:
                if path and Path(path).exists():
                    found[font_type] = path
                    print(f"    📝 Found {font_type} font: {Path(path).name}")
                    break

        fallback = found.get('bold') or found.get('regular') or found.get('impact')
        for key in ('impact', 'bold', 'bolditalic', 'regular'):
            if not found.get(key):
                found[key] = fallback
        return found

    def find_emoji_font(self):
        """Locate a color emoji font; returns None if none is available."""
        candidates = [
            _windows_font('seguiemj.ttf'),
            '/System/Library/Fonts/Apple Color Emoji.ttc',
            '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',
            '/usr/share/fonts/noto/NotoColorEmoji.ttf',
        ]
        for path in candidates:
            if path and Path(path).exists():
                print(f"    😀 Found emoji font: {Path(path).name}")
                return path
        print("    😀 No color emoji font found - captions will render without emojis")
        return None

    def get_font(self, font_type, font_size):
        key = (font_type, font_size)
        if key in self._font_cache:
            return self._font_cache[key]
        try:
            path = self.font_paths.get(font_type) or self.font_paths.get('bold')
            font = ImageFont.truetype(path, font_size) if path else ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()
        self._font_cache[key] = font
        return font

    def get_emoji_image(self, emoji_char, size):
        """Render a single emoji to an RGBA image, or None if not possible."""
        if not self.emoji_font_path:
            return None
        for trial in (size, 137, 109, 96):
            try:
                font = ImageFont.truetype(self.emoji_font_path, trial)
                img = Image.new('RGBA', (trial * 2, trial * 2), (0, 0, 0, 0))
                d = ImageDraw.Draw(img)
                d.text((trial // 2, trial // 2), emoji_char, font=font,
                       embedded_color=True)
                bbox = img.getbbox()
                if not bbox:
                    continue
                img = img.crop(bbox)
                if img.width != size:
                    ratio = size / img.width
                    img = img.resize((size, max(1, int(img.height * ratio))),
                                     Image.LANCZOS)
                return img
            except Exception:
                continue
        return None

    @staticmethod
    def _emoji_for(word):
        cleaned = word.lower().strip(string.punctuation + string.whitespace)
        return EMOJI_MAP.get(cleaned)

    # ------------------------------------------------------------- phrasing
    def _group_into_phrases(self, words, clip_duration):
        """Group timed words into short, readable phrases."""
        groups, current = [], []
        for i, w in enumerate(words):
            current.append(w)
            text = ' '.join(x['raw'] for x in current)
            ends_sentence = w['raw'].endswith(('.', '!', '?', ',', ':', ';'))
            gap_next = (words[i + 1]['start'] - w['end']) if i + 1 < len(words) else 999
            span = w['end'] - current[0]['start']
            if (len(current) >= self.MAX_WORDS or len(text) >= self.MAX_CHARS
                    or ends_sentence or gap_next > self.MAX_GAP
                    or span >= self.MAX_DURATION):
                groups.append(current)
                current = []
        if current:
            groups.append(current)

        phrases = []
        for idx, group in enumerate(groups):
            start = group[0]['start']
            end = group[-1]['end']
            next_start = (groups[idx + 1][0]['start']
                          if idx + 1 < len(groups) else clip_duration)
            # keep short phrases readable without overlapping the next one
            if end - start < self.MIN_DURATION:
                end = min(start + self.MIN_DURATION, next_start, clip_duration)
            text = ' '.join(w['raw'] for w in group).upper().strip()
            emoji = None
            for w in group:
                emoji = self._emoji_for(w['raw'])
                if emoji:
                    break
            phrases.append({
                'text': text,
                'start': start,
                'duration': max(0.1, end - start),
                'emoji': emoji,
            })
        return phrases

    def _wrap_lines(self, text, font, max_width):
        """Wrap a phrase into centered lines that fit within max_width."""
        measure = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
        lines, current = [], ''
        for word in text.split():
            trial = (current + ' ' + word).strip()
            if current and measure.textlength(trial, font=font) > max_width:
                lines.append(current)
                current = word
            else:
                current = trial
        if current:
            lines.append(current)
        return lines or ['']

    # --------------------------------------------------------------- drawing
    def create_phrase_image(self, lines, video_size, font_size, emoji_char=None):
        """Render a (multi-line) phrase centered in the lower third."""
        width, height = video_size
        style = self.styles.get(self.selected_style, self.styles['bold_white'])
        font = self.get_font(style['font_type'], font_size)

        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        stroke_w = int(font_size * style.get('stroke_ratio', 0.0)) \
            if style.get('stroke_color') else 0
        line_height = int(font_size * 1.34)

        text_color = style['text_color']
        box_color = style.get('box_color')
        if box_color:
            text_color = style.get('box_text_color') or text_color

        # Vertically center the block of lines a bit below middle.
        block_center_y = int(height * 0.76)
        first_center_y = block_center_y - (len(lines) - 1) * line_height // 2
        cx = width // 2

        top_line_top = None
        for li, line in enumerate(lines):
            cy = first_center_y + li * line_height
            bbox = draw.textbbox((cx, cy), line, font=font, anchor='mm',
                                 stroke_width=stroke_w)
            if top_line_top is None:
                top_line_top = bbox[1]

            if box_color:
                pad_x = int(font_size * 0.30)
                pad_y = int(font_size * 0.14)
                radius = int(font_size * 0.24)
                draw.rounded_rectangle(
                    [bbox[0] - pad_x, bbox[1] - pad_y,
                     bbox[2] + pad_x, bbox[3] + pad_y],
                    radius=radius, fill=box_color)

            if style.get('shadow'):
                off = max(2, font_size // 20)
                draw.text((cx + off, cy + off), line, font=font, anchor='mm',
                          fill=(0, 0, 0, 150), stroke_width=stroke_w,
                          stroke_fill=(0, 0, 0, 150))

            draw.text((cx, cy), line, font=font, anchor='mm', fill=text_color,
                      stroke_width=stroke_w,
                      stroke_fill=style.get('stroke_color') or text_color)

        # Emoji centered above the whole block.
        if emoji_char and top_line_top is not None:
            emoji_img = self.get_emoji_image(emoji_char, int(font_size * 1.1))
            if emoji_img is not None:
                ex = (width - emoji_img.width) // 2
                ey = top_line_top - emoji_img.height - int(font_size * 0.14)
                if ey < 0:
                    ey = 0
                img.alpha_composite(emoji_img, (ex, ey))

        return np.array(img)

    # ---------------------------------------------------------------- public
    def add_captions(self, clip, words, clip_start_time):
        if not words:
            return clip

        clip_words = []
        for word in words:
            rel_start = word['start'] - clip_start_time
            rel_end = word['end'] - clip_start_time
            if rel_end <= 0 or rel_start >= clip.duration:
                continue
            clip_words.append({
                'raw': word['word'].strip(),
                'start': max(0.0, rel_start),
                'end': min(clip.duration, rel_end),
            })
        clip_words = [w for w in clip_words if w['raw']]
        if not clip_words:
            return clip

        phrases = self._group_into_phrases(clip_words, clip.duration)

        video_width, video_height = clip.size
        font_size = max(46, int(min(video_width, video_height) * 0.072))
        font = self.get_font(
            self.styles.get(self.selected_style, self.styles['bold_white'])['font_type'],
            font_size)
        max_line_width = int(video_width * 0.88)

        caption_clips = []
        for ph in phrases:
            lines = self._wrap_lines(ph['text'], font, max_line_width)
            phrase_img = self.create_phrase_image(
                lines, (video_width, video_height), font_size,
                emoji_char=ph['emoji'])
            phrase_clip = (ImageClip(phrase_img, duration=ph['duration'],
                                     transparent=True)
                           .set_start(ph['start']).fadein(0.06).fadeout(0.06))
            caption_clips.append(phrase_clip)

        if caption_clips:
            return CompositeVideoClip([clip] + caption_clips)
        return clip
