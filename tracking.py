import asyncio
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# Хранилище задач отслеживания
tracking_tasks = {}

# Отслеживание монеты
async def track_coin_price(update, context, coin_id, query=None):
    user_id = update.effective_user.id

    # Отменяем предыдущее отслеживание этой монеты
    if user_id in tracking_tasks and coin_id in tracking_tasks[user_id]:
        tracking_tasks[user_id][coin_id].cancel()

    # Создаём задачу отслеживания
    task = asyncio.create_task(check_price_periodically(context, user_id, coin_id))

    # Сохраняем задачу
    if user_id not in tracking_tasks:
        tracking_tasks[user_id] = {}
    tracking_tasks[user_id][coin_id] = task

    msg = f"Вы начали отслеживание монеты *{coin_id}*. Я сообщу, если она вырастет на +3.5% или +5%."
    if query:
        await query.edit_message_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(msg, parse_mode="Markdown")

# Периодическая проверка цены
async def check_price_periodically(context, user_id, coin_id):
    from crypto_utils import get_current_prices

    initial_data = await get_current_prices([coin_id])
    if coin_id not in initial_data:
        return

    initial_price = initial_data[coin_id]["usd"]
    started_at = context.application.create_task_time

    while True:
        await asyncio.sleep(600)  # каждые 10 минут

        current_data = await get_current_prices([coin_id])
        if coin_id not in current_data:
            continue

        current_price = current_data[coin_id]["usd"]
        change = (current_price - initial_price) / initial_price * 100

        if change >= 5:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🚀 Монета *{coin_id}* выросла на *+5%*! С текущей ценой: {current_price}",
                parse_mode="Markdown"
            )
            break
        elif change >= 3.5:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🔔 Монета *{coin_id}* достигла +3.5% роста. Текущая цена: {current_price}",
                parse_mode="Markdown"
            )

        # Оповещение если 12 часов прошло без результата
        elapsed = (context.application.create_task_time - started_at).total_seconds() / 3600
        if elapsed > 12:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"⏱ Монета *{coin_id}* не показала роста +3.5% за 12 часов. Итоговая динамика: {change:.2f}%"
            )
            break

# Остановка всех отслеживаний
def stop_all_trackings():
    for user_tasks in tracking_tasks.values():
        for task in user_tasks.values():
            task.cancel()
    tracking_tasks.clear()
