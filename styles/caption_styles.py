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
# The list is intentionally broad so emojis show up often - tune to taste.
EMOJI_MAP = {
    # money / success
    'money': '💰', 'cash': '💰', 'dollars': '💰', 'dollar': '💰', 'rich': '🤑',
    'profit': '💰', 'paid': '💸', 'pay': '💸', 'bank': '🏦', 'broke': '📉',
    'free': '🆓', 'win': '🏆', 'winner': '🏆', 'won': '🏆', 'winning': '🏆',
    'gold': '🥇', 'diamond': '💎', 'expensive': '💸', 'millionaire': '🤑',
    'million': '💰', 'billion': '🤑', 'thousand': '💵', 'hundred': '💯',

    # hype / emphasis / reactions
    'fire': '🔥', 'lit': '🔥', 'flames': '🔥', 'heat': '🔥', 'goated': '🐐',
    'goat': '🐐', 'insane': '🤯', 'crazy': '🤯', 'mind': '🤯', 'unreal': '🤯',
    'wild': '🤯', 'nuts': '🤯', 'shocking': '😱', 'shocked': '😱', 'wow': '😮',
    'omg': '😱', 'bruh': '💀', 'dead': '💀', 'dying': '💀', 'died': '💀',
    'rip': '💀', 'skull': '💀', 'sheesh': '🥶', 'cold': '🥶', 'freezing': '🥶',
    'sus': '🤨', 'suspicious': '🤨', 'cap': '🧢', 'lying': '🧢', 'lie': '🧢',
    'facts': '💯', 'fact': '💯', 'real': '💯', 'truth': '💯', 'true': '✅',
    'slay': '💅', 'vibe': '😌', 'vibes': '😌', 'based': '😤', 'rizz': '😏',
    'clean': '✨', 'magic': '✨', 'sparkle': '✨', 'shiny': '✨',

    # love / feelings
    'love': '❤️', 'heart': '❤️', 'crush': '😍', 'cute': '🥰', 'kiss': '😘',
    'amazing': '🤩', 'incredible': '🤩', 'beautiful': '😍', 'gorgeous': '😍',
    'best': '🔥', 'perfect': '👌', 'nice': '👌', 'clutch': '🎯',
    'happy': '😄', 'excited': '🤩', 'hype': '🥳', 'hyped': '🥳', 'party': '🥳',
    'sad': '😢', 'cry': '😭', 'crying': '😭', 'tears': '😭', 'hurt': '😣',
    'angry': '😡', 'mad': '😡', 'rage': '😡', 'furious': '🤬', 'annoyed': '😤',
    'scared': '😨', 'scary': '😱', 'creepy': '👻', 'ghost': '👻', 'fear': '😨',
    'gross': '🤢', 'nasty': '🤢', 'disgusting': '🤮', 'ew': '🤢',
    'cool': '😎', 'awesome': '😎', 'dope': '😎', 'boring': '😴', 'tired': '😴',
    'sleep': '😴', 'shy': '😳', 'embarrassing': '😳', 'awkward': '😬',

    # brains / smarts
    'genius': '🧠', 'smart': '🧠', 'brain': '🧠', 'idea': '💡', 'think': '💡',
    'thinking': '🤔', 'confused': '😵', 'question': '❓', 'why': '❓', 'how': '❓',

    # laughter
    'laugh': '😂', 'funny': '😂', 'lol': '😂', 'lmao': '😂', 'hilarious': '😂',
    'joke': '😂', 'comedy': '😂',

    # actions / attention
    'secret': '🤫', 'quiet': '🤫', 'stop': '✋', 'wait': '✋', 'hold': '✋',
    'listen': '👂', 'hear': '👂', 'look': '👀', 'watch': '👀', 'see': '👀',
    'eyes': '👀', 'point': '👉', 'clap': '👏', 'wave': '👋', 'pray': '🙏',
    'please': '🙏', 'thanks': '🙏', 'ok': '👍', 'okay': '👍', 'yes': '✅',
    'good': '👍', 'no': '❌', 'wrong': '❌', 'bad': '👎', 'never': '🚫',
    'right': '✅', 'correct': '✅', 'done': '✅', 'finished': '🏁',

    # power / effort
    'power': '💪', 'strong': '💪', 'muscle': '💪', 'gym': '💪', 'work': '💼',
    'grind': '💪', 'fight': '🥊', 'punch': '🥊', 'boxing': '🥊', 'kick': '🦵',

    # speed / time
    'time': '⏰', 'clock': '⏰', 'late': '⏰', 'fast': '⚡', 'quick': '⚡',
    'speed': '⚡', 'zoom': '💨', 'run': '🏃', 'running': '🏃',

    # tech / gaming / stream
    'game': '🎮', 'gaming': '🎮', 'gamer': '🎮', 'play': '🎮', 'stream': '📺',
    'streamer': '📺', 'live': '🔴', 'twitch': '🟣', 'youtube': '▶️',
    'subscribe': '🔔', 'follow': '➕', 'like': '👍', 'chat': '💬', 'clip': '🎬',
    'phone': '📱', 'computer': '💻', 'internet': '🌐', 'music': '🎵',
    'song': '🎵', 'dance': '🕺', 'camera': '📸', 'video': '🎥',

    # numbers / trends
    'up': '📈', 'growth': '📈', 'rising': '📈', 'down': '📉', 'first': '🥇',
    'number': '🔢', 'level': '🆙', 'boom': '💥', 'explode': '💥', 'bomb': '💣',

    # world / people / things
    'car': '🚗', 'cars': '🚗', 'world': '🌍', 'earth': '🌍', 'king': '👑',
    'queen': '👑', 'star': '⭐', 'stars': '⭐', 'sun': '☀️', 'rain': '🌧️',
    'snow': '❄️', 'food': '🍔', 'eat': '🍔', 'hungry': '🍔', 'pizza': '🍕',
    'coffee': '☕', 'drink': '🥤', 'dog': '🐶', 'cat': '🐱', 'baby': '👶',
    'girl': '👧', 'boy': '👦', 'birthday': '🎂', 'gift': '🎁', 'trophy': '🏆',
    'crown': '👑', 'rocket': '🚀', 'gun': '🔫', 'sword': '⚔️', 'blood': '🩸',
}
