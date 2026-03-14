import requests

API_KEY = "b045b9f024b9499ab046b5394330d4b7"

BASE_URL = "https://pro-api.coinmarketcap.com"

HEADERS = {
    "X-CMC_PRO_API_KEY": API_KEY,
    "Accept": "application/json",
}

CURRENCIES = ["EUR", "BTC", "ETH", "USDT", "BNB", "XRP", "ADA", "SOL", "DOT", "MATIC"]


def convert_price(amount, from_symbol, to_symbol):
    """Convert an amount from one currency to another at the current market price."""
    url = f"{BASE_URL}/v2/tools/price-conversion"
    params = {
        "amount": amount,
        "symbol": from_symbol,
        "convert": to_symbol,
    }
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    data = response.json()
    converted = data["data"][0]["quote"][to_symbol]["price"]
    return converted


def get_price_in_eur(symbol, amount=1):
    """Return the EUR value of a given amount of a cryptocurrency."""
    if symbol == "EUR":
        return amount
    return convert_price(amount, symbol, "EUR")
