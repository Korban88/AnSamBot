def escape_markdown(text: str) -> str:
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

def format_signal(coin_data: dict) -> str:
    return (
        f"*{escape_markdown(coin_data['symbol'].upper())}*\n"
        f"Price: `${escape_markdown(str(coin_data['price']))}\n"
        f"RSI: `{coin_data['rsi']}`\n"
        f"Trend: `{'↑' if coin_data['trend'] == 'up' else '↓'}`"
    )
