import ccxt


def read_database():
    return 1, 2


# read only api keys
api_key, api_secret = read_database()
exchange = ccxt.binance({
    "enableRateLimit": True,
    "api_key": api_key,
    "api_secret": api_secret,
    "options": {
        "defaultType": "spot"
    }
})
