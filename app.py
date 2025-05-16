from flask import Flask, render_template, request
import requests
import matplotlib.pyplot as plt
from datetime import datetime
import io, base64

app = Flask(__name__)

favorites = []
alarms = []

def get_coincap_price(coin_id):
    try:
        url = f"https://api.coincap.io/v2/assets/{coin_id}"
        res = requests.get(url)
        res.raise_for_status()
        price = float(res.json()['data']['priceUsd'])
        return price
    except Exception as e:
        print("Hata get_coincap_price:", e)
        return None

def get_coincap_history(coin_id, days=7):
    try:
        url = f"https://api.coincap.io/v2/assets/{coin_id}/history?interval=d1"
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()['data']
        # Son 'days' kadar veriyi al, API genelde 30+ gün veriyor
        filtered = data[-days:]
        prices = []
        for item in filtered:
            # Tarih formatı ISO8601, parse edip sadece gün-ay alıyoruz
            date = datetime.strptime(item['date'], "%Y-%m-%dT%H:%M:%S.%fZ")
            prices.append([date.strftime("%d-%m"), float(item['priceUsd'])])
        return prices
    except Exception as e:
        print("Hata get_coincap_history:", e)
        return None

def create_chart(prices, style="line"):
    timestamps = [p[0] for p in prices]
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
        coin_id = request.form.get("coin_symbol", "").lower()
        days = int(request.form.get("days", 7))
        style = request.form.get("chart_style", "line")

        if not coin_id:
            context["error"] = "Lütfen bir coin id girin (örn: bitcoin)!"
        else:
            price = get_coincap_price(coin_id)
            if price is None:
                context["error"] = "Fiyat verisi alınamadı. Coin id doğru mu?"
            else:
                context["symbol"] = coin_id.upper()
                context["price"] = round(price, 4)
                history = get_coincap_history(coin_id, days)
                if history:
                    context["chart"] = create_chart(history, style)
                else:
                    context["error"] = "Geçmiş veri bulunamadı."

        if "add_fav" in request.form and coin_id and coin_id not in favorites:
            favorites.append(coin_id)

        if "set_alarm" in request.form:
            try:
                target = float(request.form["alarm_price"])
                alarms.append({"coin": coin_id, "target": target})
                context["alarm_set"] = True
            except:
                context["error"] = "Alarm fiyatı geçersiz!"

    return render_template("index.html", **context)

if __name__ == "_main_":
    app.run(debug=True)