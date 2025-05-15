from flask import Flask, render_template, request
import requests

app = Flask(__name__)

COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

COIN_LIST = {
    "bitcoin": "Bitcoin",
    "ethereum": "Ethereum",
    "binancecoin": "Binance Coin",
    "cardano": "Cardano",
    "dogecoin": "Dogecoin",
    "polkadot": "Polkadot",
    "solana": "Solana",
    "litecoin": "Litecoin"
}

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    selected_coin = None

    if request.method == "POST":
        selected_coin = request.form.get("coin")
        if selected_coin:
            params = {
                "ids": selected_coin,
                "vs_currencies": "usd"
            }
            try:
                response = requests.get(COINGECKO_API_URL, params=params)
                data = response.json()
                price = data[selected_coin]["usd"]
                result = f"{COIN_LIST.get(selected_coin, selected_coin).title()} şu an ${price} USD"
            except Exception as e:
                result = f"Hata: {str(e)}"

    return render_template("index.html", coins=COIN_LIST, result=result)

# Bu kısım Render'da gerekmez, ama yerel test için ekliyoruz
if __name__ == "__main__":
    app.run(debug=True)
