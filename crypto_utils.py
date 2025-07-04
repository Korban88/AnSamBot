import requests

# Список монет Telegram Wallet (примерный)
TELEGRAM_COINS = [
    "btc", "eth", "ton", "usdt", "usdc", "bnb", "bch", "ltc", "matic", "trx",
    "uni", "link", "avax", "ada", "dot", "shib", "sol", "near", "atom", "apt",
    "dai", "fil", "xrp", "doge", "stx", "etc", "bsv", "xlm", "eos", "sand",
    "mana", "ftm", "aave", "cake", "chz", "rune", "crv", "zec", "algo", "comp",
    "dash", "lunc", "enj", "imx", "grt", "gala", "1inch", "snx", "yfi", "waves",
    "bnt", "hnt", "ar", "icp", "cvx", "sushi", "bat", "qtum", "zen", "zrx", "storj"
]

def get_top_coins():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "volume_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": "false"
    }
    response = requests.get(url, params=params)
    data = response.json()

    # Фильтрация по монетам Telegram Wallet
    filtered = [coin for coin in data if coin['symbol'].lower() in TELEGRAM_COINS]
    return filtered

def get_price(symbol):
    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": symbol.lower(),
        "vs_currencies": "usd"
    }
    try:
        response = requests.get(url, params=params).json()
        return response[symbol.lower()]["usd"]
    except:
        return None
