from flask import Flask, render_template, request
import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import io, base64

app = Flask(__name__)

favorites = []
alarms = []

def get_binance_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}"
        res = requests.get(url)
        res.raise_for_status()
        return float(res.json()['price'])
    except:
        return None

def get_binance_history(symbol, days=7):
    try:
        interval = "1d"
        limit = days
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol.upper()}&interval={interval}&limit={limit}"
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        prices = [[int(item[0]), float(item[4])] for item in data]  # close price
        return prices
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

@app.route("/", methods=["GET", "POST"])
def index():
    context = {
        "symbol": None,
        "price": None,
        "chart": None,
        "favorites": favorites,
        "alarm_set": False,
        "error": None
    }

    if request.method == "POST":
        symbol = request.form.get("coin_symbol", "").upper()
        days = int(request.form.get("days", 7))
        style = request.form.get("chart_style", "line")

        if not symbol:
            context["error"] = "Lütfen bir coin sembolü girin (örneğin: BTCUSDT)!"
        else:
            price = get_binance_price(symbol)
            if price is None:
                context["error"] = "Fiyat verisi alınamadı. Sembol doğru mu?"
            else:
                context["symbol"] = symbol
                context["price"] = price
                history = get_binance_history(symbol, days)
                if history:
                    context["chart"] = create_chart(history, style)
                else:
                    context["error"] = "Geçmiş veri bulunamadı."

        if "add_fav" in request.form and symbol and symbol not in favorites:
            favorites.append(symbol)

        if "set_alarm" in request.form:
            try:
                target = float(request.form["alarm_price"])
                alarms.append({"coin": symbol, "target": target})
                context["alarm_set"] = True
            except:
                context["error"] = "Alarm fiyatı geçersiz!"

    return render_template("index.html", **context)

if __name__ == "__main__":
    app.run(debug=True)
