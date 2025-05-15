from flask import Flask, render_template, request
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import io, base64, os

app = Flask(__name__)
alarms = []
favorites = []
FAVORITES_FILE = "favorites.txt"

def get_price(coin_id, currency):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={currency}"
        res = requests.get(url).json()
        return res[coin_id][currency]
    except:
        return None

def get_price_history(coin_id, days=7, currency="usd"):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency={currency}&days={days}"
        data = requests.get(url).json()
        return data["prices"]
    except:
        return None

def get_coin_logo_url(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        res = requests.get(url).json()
        return res["image"]["large"]
    except:
        return None

def create_chart(prices, style="line"):
    timestamps = [datetime.fromtimestamp(p[0] / 1000).strftime('%d-%m') for p in prices]
    values = [p[1] for p in prices]
    plt.figure(figsize=(10, 4))
    if style == "bar":
        plt.bar(timestamps, values, color="orange")
    elif style == "area":
        plt.fill_between(timestamps, values, color="skyblue", alpha=0.5)
        plt.plot(timestamps, values, color='blue')
    elif style == "scatter":
        plt.scatter(timestamps, values, color="red")
    else:
        plt.plot(timestamps, values, marker='o')
    plt.xticks(rotation=45)
    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format="png", bbox_inches="tight")
    img.seek(0)
    plt.close()
    return base64.b64encode(img.read()).decode("utf-8")

def save_favorites():
    with open(FAVORITES_FILE, "w") as f:
        for coin in favorites:
            f.write(coin + "\n")

def load_favorites():
    global favorites
    if os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, "r") as f:
            favorites[:] = [line.strip() for line in f.readlines()]

@app.route("/", methods=["GET", "POST"])
def index():
    load_favorites()
    context = {
        "coin": None,
        "price": None,
        "logo_url": None,
        "chart": None,
        "favorites": favorites,
        "alarm_set": False,
        "error": None
    }

    if request.method == "POST":
        coin = request.form.get("coin", "").lower().strip()
        currency = request.form.get("currency", "usd")
        days = int(request.form.get("days", 7))
        style = request.form.get("chart_style", "line")

        if not coin:
            context["error"] = "Lütfen bir coin adı girin!"
        else:
            price = get_price(coin, currency)
            if price is None:
                context["error"] = "Fiyat verisi alınamadı."
            else:
                context["coin"] = coin
                context["price"] = price
                context["logo_url"] = get_coin_logo_url(coin)
                history = get_price_history(coin, days, currency)
                if history:
                    context["chart"] = create_chart(history, style)

        if "add_fav" in request.form and coin and coin not in favorites:
            favorites.append(coin)
            save_favorites()

        if "set_alarm" in request.form:
            try:
                target = float(request.form["alarm_price"])
                alarms.append({"coin": coin, "target": target, "currency": currency})
                context["alarm_set"] = True
            except:
                context["error"] = "Alarm fiyatı geçersiz!"

    return render_template("index.html", **context)

if __name__ == "__main__":
    app.run(debug=True)
