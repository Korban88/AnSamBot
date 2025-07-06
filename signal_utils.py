from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Хранилище индексов топ-монет по пользователям
user_signal_index = {}

def reset_signal_index(user_id: int):
    """Сбросить индекс монеты для пользователя"""
    user_signal_index[user_id] = 0

def get_next_signal_message(user_id: int, top_cryptos: list) -> dict | None:
    """Получить следующий сигнал из top-3 монет для пользователя"""
    index = user_signal_index.get(user_id, 0)

    if index >= len(top_cryptos):
        return None

    coin = top_cryptos[index]
    user_signal_index[user_id] = index + 1

    text = (
        f"*Монета:* `{coin['name']}` \\(`{coin['symbol'].upper()}`\\)\n"
        f"*Цена входа:* `${coin['entry_price']}`\n"
        f"*Цель \\( +5% \\):* `${coin['target_price']}`\n"
        f"*Стоп\\-лосс:* `${coin['stop_loss']}`\n"
        f"*Вероятность роста:* `{coin['growth_probability']}%`\n"
        f"\n"
        f"_RSI:_ `{coin['rsi']}` | _MA:_ `{coin.get('ma', 'N/A')}` | _Изменение за 24ч:_ `{coin['change_24h']}%`"
    )

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("📊 Следить за монетой", callback_data=f"track_{coin['id']}")
    )

    return {
        "text": text,
        "keyboard": keyboard
    }
