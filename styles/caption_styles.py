"""
Caption styles and emoji mapping for the word-by-word captions.

Each style is a dict describing how a single (currently-spoken) word is drawn:

    text_color        : RGBA fill of the word
    stroke_color      : RGBA outline color, or None for no outline
    stroke_ratio      : outline thickness as a fraction of the font size
    box_color         : RGBA rounded-rectangle drawn behind the word, or None
    box_text_color    : text color to use when a box is present (overrides
                        text_color so the word stays readable on the box)
    shadow            : draw a soft drop shadow behind the word
    font_type         : one of the font types resolved in CaptionMaker
    name              : human friendly label shown in the menu
"""

CAPTION_STYLES = {
    'bold_white': {
        'text_color': (255, 255, 255, 255),
        'stroke_color': (0, 0, 0, 255),
        'stroke_ratio': 0.11,
        'box_color': None,
        'box_text_color': None,
        'shadow': True,
        'font_type': 'impact',
        'name': 'Bold White (outlined)'
    },
    'neon_cyan': {
        'text_color': (0, 240, 255, 255),
        'stroke_color': (0, 0, 0, 255),
        'stroke_ratio': 0.11,
        'box_color': None,
        'box_text_color': None,
        'shadow': True,
        'font_type': 'impact',
        'name': 'Neon Cyan (outlined)'
    },
    'fire_red': {
        'text_color': (255, 45, 45, 255),
        'stroke_color': (0, 0, 0, 255),
        'stroke_ratio': 0.11,
        'box_color': None,
        'box_text_color': None,
        'shadow': True,
        'font_type': 'bolditalic',
        'name': 'Fire Red (italic)'
    },
    'sunny_yellow': {
        'text_color': (255, 214, 10, 255),
        'stroke_color': (0, 0, 0, 255),
        'stroke_ratio': 0.12,
        'box_color': None,
        'box_text_color': None,
        'shadow': True,
        'font_type': 'impact',
        'name': 'Sunny Yellow (outlined)'
    },
    'green_pop': {
        'text_color': (57, 255, 20, 255),
        'stroke_color': (0, 0, 0, 255),
        'stroke_ratio': 0.12,
        'box_color': None,
        'box_text_color': None,
        'shadow': True,
        'font_type': 'bolditalic',
        'name': 'Green Pop (italic)'
    },
    'purple_box': {
        'text_color': (255, 255, 255, 255),
        'stroke_color': None,
        'stroke_ratio': 0.0,
        'box_color': (138, 43, 226, 255),
        'box_text_color': (255, 255, 255, 255),
        'shadow': True,
        'font_type': 'bold',
        'name': 'Purple Highlight Box'
    },
    'pink_box': {
        'text_color': (255, 255, 255, 255),
        'stroke_color': None,
        'stroke_ratio': 0.0,
        'box_color': (233, 30, 99, 255),
        'box_text_color': (255, 255, 255, 255),
        'shadow': True,
        'font_type': 'bold',
        'name': 'Pink Highlight Box'
    },
    'clean_white': {
        'text_color': (255, 255, 255, 255),
        'stroke_color': (0, 0, 0, 200),
        'stroke_ratio': 0.06,
        'box_color': None,
        'box_text_color': None,
        'shadow': False,
        'font_type': 'bold',
        'name': 'Clean White (subtle outline)'
    },
}

# Words that get emphasised (uppercase already; matched case-insensitively).
HIGHLIGHT_KEYWORDS = [
    'amazing', 'incredible', 'secret', 'important', 'shocking', 'exclusive',
    'never', 'always', 'only', 'must', 'best', 'worst',
    'first', 'last', 'biggest', 'most', 'why', 'how',
    'money', 'free', 'easy', 'truth',
]

# Map spoken words to an emoji that is drawn above the word. Keys are matched
# case-insensitively against the word with surrounding punctuation stripped.
# Keep this list broad but conservative so emojis feel relevant, not random.
EMOJI_MAP = {
    # money / success
    'money': '💰', 'cash': '💰', 'dollars': '💰', 'rich': '🤑', 'profit': '💰',
    'free': '🆓', 'win': '🏆', 'winner': '🏆', 'won': '🏆', 'gold': '🥇',
    # emphasis / reactions
    'fire': '🔥', 'lit': '🔥', 'insane': '🤯', 'crazy': '🤯', 'mind': '🤯',
    'shocking': '😱', 'shocked': '😱', 'wow': '😮', 'omg': '😱',
    'love': '❤️', 'heart': '❤️', 'amazing': '🤩', 'incredible': '🤩',
    'best': '🔥', 'perfect': '👌', 'genius': '🧠', 'smart': '🧠', 'brain': '🧠',
    'laugh': '😂', 'funny': '😂', 'lol': '😂', 'hilarious': '😂',
    # actions / topics
    'secret': '🤫', 'stop': '✋', 'wait': '✋', 'listen': '👂', 'look': '👀',
    'watch': '👀', 'see': '👀', 'time': '⏰', 'fast': '⚡', 'quick': '⚡',
    'power': '💪', 'strong': '💪', 'work': '💼', 'idea': '💡', 'think': '💡',
    'yes': '✅', 'no': '❌', 'wrong': '❌', 'right': '✅', 'true': '✅',
    'food': '🍔', 'eat': '🍔', 'game': '🎮', 'music': '🎵', 'phone': '📱',
    'up': '📈', 'growth': '📈', 'down': '📉', 'car': '🚗', 'world': '🌍',
    'king': '👑', 'queen': '👑', 'star': '⭐', 'boom': '💥',
}
