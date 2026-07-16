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
    Creates and adds styled word-by-word captions (outline, highlight box,
    shadow and optional emoji) to a video clip.
    """
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
            # Heavy display font for punchy captions.
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

        # Fall back through the chain so every type resolves to *something*.
        fallback = found.get('bold') or found.get('regular') or found.get('impact')
        for key in ('impact', 'bold', 'bolditalic', 'regular'):
            if not found.get(key):
                found[key] = fallback
        return found

    def find_emoji_font(self):
        """Locate a color emoji font; returns None if none is available."""
        candidates = [
            _windows_font('seguiemj.ttf'),          # Windows (scalable, ideal)
            '/System/Library/Fonts/Apple Color Emoji.ttc',  # macOS
            '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',  # Linux
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
        # Apple/Noto color fonts are bitmap strikes and only render at fixed
        # sizes; try the requested size first, then a couple of known strikes.
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

    # --------------------------------------------------------------- drawing
    def create_word_image(self, word, video_size, font_size,
                          is_highlighted=False, emoji_char=None):
        """Render one word (with optional box/outline/shadow/emoji) full-frame."""
        width, height = video_size
        style = self.styles.get(self.selected_style, self.styles['bold_white'])
        font = self.get_font(style['font_type'], font_size)

        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        stroke_w = int(font_size * style.get('stroke_ratio', 0.0)) \
            if style.get('stroke_color') else 0

        bbox = draw.textbbox((0, 0), word, font=font, stroke_width=stroke_w)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # Position: lower third, centered, with a safe margin from the edge.
        x = (width - text_w) // 2 - bbox[0]
        y = int(height * 0.72)

        text_color = style['text_color']
        box_color = style.get('box_color')
        if box_color:
            text_color = style.get('box_text_color') or text_color
            pad_x = int(font_size * 0.28)
            pad_y = int(font_size * 0.16)
            radius = int(font_size * 0.22)
            box = [x - pad_x, y - pad_y, x + text_w + pad_x, y + text_h + pad_y]
            draw.rounded_rectangle(box, radius=radius, fill=box_color)
        if is_highlighted and not box_color:
            # emphasise keyword by tinting it warm yellow
            text_color = (255, 214, 10, 255)

        # Soft drop shadow.
        if style.get('shadow'):
            offset = max(2, font_size // 22)
            draw.text((x + offset, y + offset), word, font=font,
                      fill=(0, 0, 0, 160), stroke_width=stroke_w,
                      stroke_fill=(0, 0, 0, 160))

        draw.text((x, y), word, font=font, fill=text_color,
                  stroke_width=stroke_w,
                  stroke_fill=style.get('stroke_color') or text_color)

        # Emoji sits above the word.
        if emoji_char:
            emoji_img = self.get_emoji_image(emoji_char, int(font_size * 1.15))
            if emoji_img is not None:
                ex = (width - emoji_img.width) // 2
                ey = y - emoji_img.height - int(font_size * 0.18)
                if ey < 0:
                    ey = 0
                img.alpha_composite(emoji_img, (ex, ey))

        return np.array(img)

    @staticmethod
    def _emoji_for(word):
        cleaned = word.lower().strip(string.punctuation + string.whitespace)
        return EMOJI_MAP.get(cleaned)

    # ---------------------------------------------------------------- public
    def add_captions(self, clip, words, clip_start_time):
        if not words:
            return clip

        clip_words = []
        for word in words:
            rel_start = max(0, word['start'] - clip_start_time)
            rel_end = min(clip.duration, word['end'] - clip_start_time)
            if word['end'] - clip_start_time <= 0 or \
                    word['start'] - clip_start_time >= clip.duration:
                continue
            duration = rel_end - rel_start
            if duration <= 0.05:
                continue
            clip_words.append({
                'raw': word['word'].strip(),
                'word': word['word'].strip().upper(),
                'start': rel_start,
                'duration': duration,
            })

        if not clip_words:
            return clip

        video_width, video_height = clip.size
        base_font_size = max(54, int(min(video_width, video_height) * 0.085))

        caption_clips = []
        for wd in clip_words:
            is_hl = any(k.upper() in wd['word'] for k in self.highlight_keywords)
            emoji_char = self._emoji_for(wd['raw'])
            word_img = self.create_word_image(
                wd['word'], (video_width, video_height), base_font_size,
                is_highlighted=is_hl, emoji_char=emoji_char)
            word_clip = (ImageClip(word_img, duration=wd['duration'],
                                   transparent=True)
                         .set_start(wd['start']).fadein(0.05).fadeout(0.05))
            caption_clips.append(word_clip)

        if caption_clips:
            return CompositeVideoClip([clip] + caption_clips)
        return clip
