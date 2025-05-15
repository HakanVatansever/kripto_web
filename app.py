from flask import Flask, render_template, request
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

favorites = []
alarms = []

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

def get_coin_logo(coin_id):
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
    else:  # line
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
        "coin": None,
        "price": None,
        "logo_url": None,
        "chart": None,
        "favorites": favorites,
        "alarm_set": False,
        "error": None,
        "currency": "usd",
        "days": 7,
        "chart_style": "line"
    }

    if request.method == "POST":
        coin = request.form.get("coin_id", "").strip().lower()
        currency = request.form.get("currency", "usd").lower()
        days = request.form.get("days", 7)
        chart_style = request.form.get("chart_style", "line")

        # Gün sayısı int olarak alınıyor, hata varsa default 7
        try:
            days = int(days)
            if days < 1:
                days = 7
        except:
            days = 7

        context["currency"] = currency
        context["days"] = days
        context["chart_style"] = chart_style

        if not coin:
            context["error"] = "Lütfen bir coin ID girin!"
        else:
            price = get_price(coin, currency)
            if price is None:
                context["error"] = "Fiyat verisi alınamadı, lütfen doğru coin ID girin."
            else:
                context["coin"] = coin
                context["price"] = price
                context["logo_url"] = get_coin_logo(coin)

                history = get_price_history(coin, days, currency)
                if history:
                    context["chart"] = create_chart(history, chart_style)
                else:
                    context["error"] = "Geçmiş veri bulunamadı."

        if "add_fav" in request.form:
            if coin and coin not in favorites:
                favorites.append(coin)

        if "set_alarm" in request.form:
            try:
                target = float(request.form.get("alarm_price", "0"))
                alarms.append({"coin": coin, "target": target, "currency": currency})
                context["alarm_set"] = True
            except:
                context["error"] = "Alarm fiyatı geçersiz!"

    return render_template("index.html", get_coin_logo=get_coin_logo, **context)

if __name__ == "__main__":
    app.run(debug=True)
