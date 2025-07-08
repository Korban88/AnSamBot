def analyze_coin(data):
    return (
        data['rsi'] < 45 and
        data['price'] > data['ma200'] and
        -6 <= data['24h_change'] <= 0
    )
