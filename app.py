from flask import Flask, render_template, request
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import io, base64

app = Flask(__name__)

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
        "coin": None,
        "price": None,
        "logo_url": None,
        "chart": None,
        "error": None,
        "currency": "usd"
    }

    if request.method == "POST":
        coin = request.form.get("coin_id", "").lower().strip()
        currency = request.form.get("currency", "usd").lower()
        days = request.form.get("days", "7")
        style = request.form.get("chart_style", "line")

        context["currency"] = currency

        if not coin:
            context["error"] = "Lütfen coin ID giriniz."
        else:
            try:
                days_int = int(days)
                if days_int <= 0:
                    raise ValueError
            except:
                context["error"] = "Geçerli bir gün sayısı giriniz."
                return render_template("index.html", **context)

            price = get_price(coin, currency)
            if price is None:
                context["error"] = "Fiyat bilgisi alınamadı. Coin ID veya para birimini kontrol edin."
            else:
                context["coin"] = coin
                context["price"] = price
                context["logo_url"] = get_coin_logo(coin)
                history = get_price_history(coin, days_int, currency)
                if history:
                    context["chart"] = create_chart(history, style)
                else:
                    context["error"] = "Geçmiş fiyat verisi alınamadı."

    return render_template("index.html", **context)

if __name__ == "__main__":
    app.run(debug=True)
