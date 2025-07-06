# utils.py

def escape_markdown(text):
    """
    Экранирует специальные символы для MarkdownV2 в Telegram.
    """
    escape_chars = r"\_*[]()~`>#+-=|{}.!"
    return ''.join(f'\\{c}' if c in escape_chars else c for c in str(text))
