async def get_top_signals():
    # Пример заглушки для топ-3 монет с вероятностью роста
    return [
        {
            "id": "bitcoin",
            "name": "Bitcoin",
            "probability": 75,
            "entry_price": 30000,
            "target_price": 31500,
            "stop_loss": 29000,
        },
        {
            "id": "ton",
            "name": "Toncoin",
            "probability": 68,
            "entry_price": 7,
            "target_price": 7.35,
            "stop_loss": 6.7,
        },
        {
            "id": "ethereum",
            "name": "Ethereum",
            "probability": 65,
            "entry_price": 2000,
            "target_price": 2100,
            "stop_loss": 1950,
        },
    ]
