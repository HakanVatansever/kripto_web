from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime

app = Flask(_name_)

# === API Fonksiyonları ===
def get_price(coin_id, currency):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={currency}"
        response = requests.get(url)
        data = response.json()
        return data[coin_id][currency]
    except:
        return None

def get_price_history(coin_id, days=7, currency="usd"):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency={currency}&days={days}"
        response = requests.get(url)
        data = response.json()
        return data["prices"]
    except:
        return None

def get_coin_logo(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        response = requests.get(url)
        data = response.json()
        return data["image"]["large"]
    except:
        return None

# === Ana Sayfa ===
@app.route("/")
def index():
    return render_template("index.html")

# === API: Coin Verileri ===
@app.route("/api/coin", methods=["POST"])
def coin_data():
    data = request.json
    coin_id = data["coin"]
    currency = data["currency"]
    days = int(data["days"])

    price = get_price(coin_id, currency)
    history = get_price_history(coin_id, days, currency)
    logo_url = get_coin_logo(coin_id)

    if price is None or history is None:
        return jsonify({"error": "Veri alınamadı"}), 400

    timestamps = [datetime.fromtimestamp(p[0] / 1000).strftime('%d-%m') for p in history]
    values = [p[1] for p in history]

    return jsonify({
        "price": price,
        "logo_url": logo_url,
        "labels": timestamps,
        "data": values
    })

if _name_ == "_main_":
    app.run(debug=True)