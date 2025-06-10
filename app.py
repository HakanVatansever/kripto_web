from flask import Flask, render_template, jsonify
import requests
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import datetime # Tarih dönüşümü için ekledik
from flask_cors import CORS # CORS desteği için ekledik

app = Flask(__name__)
CORS(app) # Tüm rotalar için CORS'u etkinleştir

# CoinGecko API URL'leri
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# Flask'ın HTML dosyasını sunmasını istiyorsak, index.html'in templates klasöründe olduğundan emin olun.
@app.route('/')
def index():
    # Bu, Flask'ın templates/index.html dosyasını tarayıcıya göndermesini sağlar.
    # Eğer frontend HTML'i ayrı bir dosya olarak tarayıcıda açılıyorsa ve Flask sadece API sağlıyorsa
    # bu kısım gereksiz olabilir veya sadece CORS için bırakılabilir.
    return render_template('index.html')

@app.route('/coin_data/<coin_id>')
def get_coin_chart(coin_id):
    try:
        # Fiyat geçmişini çek (30 günlük veri daha iyi bir grafik sağlar)
        # days=7 yerine days=30 yapıyorum ki daha uzun bir tarih aralığı olsun.
        prices_res = requests.get(f"{COINGECKO_BASE_URL}/coins/{coin_id}/market_chart?vs_currency=usd&days=30")
        prices_res.raise_for_status() # HTTP hatalarını kontrol et
        prices_data = prices_res.json()
        
        prices = prices_data.get('prices') # .get() kullanarak anahtarın varlığını kontrol et
        
        if not prices:
            # CoinGecko API'den veri gelmediyse veya yanlış coin_id ise
            return jsonify({"error": "No price data available for this coin. Please check the coin ID or try again later."}), 404

        # Grafiği oluştur
        # Unix zaman damgalarını datetime nesnelerine dönüştür
        dates = [datetime.datetime.fromtimestamp(p[0] / 1000) for p in prices]
        values = [p[1] for p in prices]

        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(dates, values, color='#00d8ff', linewidth=2) # Çizgi kalınlığını artırdık
        ax.set_title(f'{coin_id.capitalize()} Price Chart (Last 30 Days)', color='#eee') # Başlık güncellendi
        ax.set_xlabel('Date', color='#bbb')
        ax.set_ylabel('Price (USD)', color='#bbb')
        ax.tick_params(axis='x', colors='#bbb', rotation=45) # X ekseni etiketlerini döndür
        ax.tick_params(axis='y', colors='#bbb')
        ax.set_facecolor('#1f1f1f')
        fig.patch.set_facecolor('#1f1f1f')
        ax.grid(True, linestyle='--', alpha=0.5) # Izgara eklendi

        # Tarih formatını ayarla (daha okunabilir olması için)
        fig.autofmt_xdate() # Otomatik tarih formatlama
        plt.tight_layout()

        # Grafiği belleğe kaydet ve base64 olarak kodla
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100) # dpi ekledik, boşluklar için bbox_inches
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        graphic = base64.b64encode(image_png).decode('utf-8')

        plt.close(fig) # Bellek sızıntılarını önlemek için figürü kapat

        return jsonify({"chart": graphic})
    except requests.exceptions.RequestException as e:
        # API isteğiyle ilgili ağ veya HTTP hataları
        return jsonify({"error": f"API request failed: {str(e)}. Please check your internet connection or CoinGecko API status."}), 500
    except Exception as e:
        # Diğer beklenmedik hatalar (örneğin veri işleme, matplotlib hatası)
        print(f"An unexpected error occurred in get_coin_chart for {coin_id}: {str(e)}") # Sunucu tarafında hata detayını gör
        return jsonify({"error": f"An internal server error occurred while generating the chart: {str(e)}"}), 500

if __name__ == '__main__':
    # Flask uygulamasını başlat. debug=True geliştirme için iyidir.
    # production'da debug=False yapın ve farklı bir sunucu (Gunicorn gibi) kullanın.
    app.run(debug=True)