from flask import Flask, render_template, jsonify
import requests
import matplotlib.pyplot as plt
import base64
from io import BytesIO

app = Flask(__name__)

# CoinGecko API URL'leri
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/coin_data/<coin_id>')
def get_coin_chart(coin_id):
    try:
        # Fiyat geçmişini çek
        prices_res = requests.get(f"{COINGECKO_BASE_URL}/coins/{coin_id}/market_chart?vs_currency=usd&days=7")
        prices_res.raise_for_status() # HTTP hatalarını kontrol et
        prices_data = prices_res.json()
        
        prices = prices_data['prices']
        
        if not prices:
            return jsonify({"error": "No price data available for this coin."}), 404

        # Grafiği oluştur
        dates = [p[0] for p in prices]
        values = [p[1] for p in prices]

        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(dates, values, color='#00d8ff')
        ax.set_title(f'{coin_id.capitalize()} Price Chart (Last 7 Days)', color='#eee')
        ax.set_xlabel('Date', color='#bbb')
        ax.set_ylabel('Price (USD)', color='#bbb')
        ax.tick_params(axis='x', colors='#bbb')
        ax.tick_params(axis='y', colors='#bbb')
        ax.set_facecolor('#1f1f1f')
        fig.patch.set_facecolor('#1f1f1f')

        # Tarih formatını ayarla (isteğe bağlı, daha iyi görünüm için)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Grafiği belleğe kaydet ve base64 olarak kodla
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        graphic = base64.b64encode(image_png)
        graphic = graphic.decode('utf-8')

        plt.close(fig) # Bellek sızıntılarını önlemek için figürü kapat

        return jsonify({"chart": graphic})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API request failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)