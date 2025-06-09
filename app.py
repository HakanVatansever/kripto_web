from flask import Flask, render_template, jsonify
import requests
import matplotlib
matplotlib.use('Agg')  # GUI gerektirmez
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import io
import base64
import time

app = Flask(__name__)
API_REQUEST_DELAY = 3  # API rate limit için bekleme süresi

def get_historical_data(coin_id, days=30):
    # CoinGecko API’den coin’in tarihsel fiyat verisini alır
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
    response = requests.get(url)
    response.raise_for_status()
    time.sleep(API_REQUEST_DELAY)  # API aşımı önle
    data = response.json()
    return data['prices']

def create_chart(prices):
    # Matplotlib ile grafik oluşturup base64 string döner
    dates = [datetime.fromtimestamp(p[0]/1000) for p in prices]
    values = [p[1] for p in prices]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(dates, values, color='#673AB7', linewidth=2)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.set_title('Price History (Last 30 days)')
    ax.set_xlabel('Date')
    ax.set_ylabel('Price (USD)')
    fig.autofmt_xdate()
    fig.tight_layout()

    img = io.BytesIO()
    fig.savefig(img, format='png', dpi=100)
    img.seek(0)
    plt.close(fig)
    return base64.b64encode(img.read()).decode('utf-8')

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/coin_data/<coin_id>")
def coin_data(coin_id):
    try:
        prices = get_historical_data(coin_id, days=30)
        chart_base64 = create_chart(prices)
        return jsonify({"chart": chart_base64})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
