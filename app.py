# Gerekli kütüphaneleri içe aktarma
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import datetime
import time # İstekler arasına gecikme koymak için
import json

# Flask uygulamasını başlatma
app = Flask(__name__)
# Tüm rotalar için CORS'u etkinleştirme (frontend'in backend'e erişebilmesi için gerekli)
CORS(app)

# CoinGecko API temel URL'i
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# Basit bir bellek içi önbellek (cache) mekanizması
# API hız limitlerini aşmamak ve performansı artırmak için kullanılır.
# Anahtar: API isteği URL'si, Değer: (Veri, Zaman damgası)
CACHE = {}
CACHE_EXPIRATION_TIME = 300 # Saniye cinsinden (5 dakika)

# --- Yardımcı Fonksiyonlar ---

def fetch_data_from_api(url, cache_key=None):
    """
    Belirtilen URL'den veri çeker ve basit bir önbellek kullanır.
    API hız limiti hatalarını da yakalamayı dener.
    """
    if cache_key and cache_key in CACHE:
        cached_data, timestamp = CACHE[cache_key]
        if (time.time() - timestamp) < CACHE_EXPIRATION_TIME:
            print(f"Önbellekten servis ediliyor: {cache_key}")
            return cached_data
        else:
            print(f"Önbellek süresi doldu: {cache_key}")
            del CACHE[cache_key] # Süresi dolmuş veriyi sil

    print(f"API'den çekiliyor: {url}")
    try:
        # API hız limitine takılmamak için 3 saniye bekleme eklendi
        time.sleep() 
        response = requests.get(url, timeout=15)
        response.raise_for_status() # HTTP hatalarını (4xx veya 5xx) yakala
        data = response.json()

        if cache_key:
            CACHE[cache_key] = (data, time.time()) # Yeni veriyi önbelleğe kaydet
        return data
    except requests.exceptions.Timeout:
        print(f"API isteği zaman aşımına uğradı: {url}")
        raise ConnectionError("API isteği zaman aşımına uğradı. Lütfen daha sonra tekrar deneyin.")
    except requests.exceptions.RequestException as e:
        # Özellikle hız limiti hatası (429 Too Many Requests) kontrolü
        if response.status_code == 429:
            print(f"API hız limiti aşıldı: {url}")
            raise ConnectionError("CoinGecko API hız limiti aşıldı. Lütfen bir süre sonra tekrar deneyin.")
        else:
            print(f"API isteği hatası: {e}")
            raise ConnectionError(f"API isteği başarısız oldu: {e}")
    except json.JSONDecodeError:
        print(f"API'den geçersiz JSON yanıtı alındı: {url}")
        raise ValueError("API'den geçersiz veri formatı alındı.")


def create_chart_image(dates, values, title, y_label, color, show_grid=True):
    """
    Verilen verilerle bir Matplotlib grafiği oluşturur ve Base64 kodlu PNG olarak döndürür.
    """
    plt.style.use('dark_background') # Koyu tema stilini uygula
    fig, ax = plt.subplots(figsize=(10, 5)) # Grafik boyutunu ayarla

    ax.plot(dates, values, color=color, linewidth=2) # Çizgi rengi ve kalınlığı

    ax.set_title(title, color='#eee', fontsize=16) # Başlık
    ax.set_xlabel('Date', color='#bbb', fontsize=12) # X ekseni etiketi
    ax.set_ylabel(y_label, color='#bbb', fontsize=12) # Y ekseni etiketi

    ax.tick_params(axis='x', colors='#bbb', rotation=45, labelsize=10) # X ekseni etiketleri
    ax.tick_params(axis='y', colors='#bbb', labelsize=10) # Y ekseni etiketleri

    ax.set_facecolor('#1f1f1f') # Grafik arka plan rengi
    fig.patch.set_facecolor('#1f1f1f') # Figür arka plan rengi

    if show_grid:
        ax.grid(True, linestyle='--', alpha=0.5, color='#444') # Izgara ekle

    fig.autofmt_xdate() # X ekseni tarih etiketlerini otomatik formatla
    plt.tight_layout() # Düzenlemeyi sıkılaştır

    # Grafiği bellekte bir PNG'ye kaydet
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    plt.close(fig) # Bellek sızıntılarını önlemek için figürü kapatmak çok önemli

    # PNG verisini Base64 olarak kodla
    graphic = base64.b64encode(image_png).decode('utf-8')
    return graphic

# --- Flask Rotaları ---

@app.route('/')
def index():
    """Ana sayfa, HTML şablonunu render eder."""
    # `index.html` dosyanızın `templates/` klasöründe olduğundan emin olun.
    return render_template('index.html')

@app.route('/global_market_data')
def get_global_market_data():
    """CoinGecko'dan global piyasa verilerini çeker."""
    cache_key = 'global_data'
    try:
        url = f"{COINGECKO_BASE_URL}/global"
        data = fetch_data_from_api(url, cache_key)
        
        # Sadece ihtiyacımız olan verileri döndürüyoruz
        global_data = data.get('data', {})
        market_cap_usd = global_data.get('total_market_cap', {}).get('usd', 0)
        volume_24h_usd = global_data.get('total_volume', {}).get('usd', 0)
        
        return jsonify({
            "total_market_cap_usd": market_cap_usd,
            "total_24h_volume_usd": volume_24h_usd
        })
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"Global market data hatası: {e}")
        return jsonify({"error": "Global piyasa verileri çekilirken bir hata oluştu."}), 500


@app.route('/trending_coins')
def get_trending_coins():
    """CoinGecko'dan trend olan coinleri çeker."""
    cache_key = 'trending_coins'
    try:
        url = f"{COINGECKO_BASE_URL}/search/trending"
        data = fetch_data_from_api(url, cache_key)
        
        # Trend olan coinlerin sadece isimlerini ve sembollerini al
        trending_list = []
        for coin_data in data.get('coins', []):
            coin = coin_data.get('item', {})
            trending_list.append({
                "id": coin.get('id'),
                "name": coin.get('name'),
                "symbol": coin.get('symbol'),
                "market_cap_rank": coin.get('market_cap_rank'),
                "large_image": coin.get('large')
            })
        
        return jsonify({"trending_coins": trending_list})
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"Trend coinler hatası: {e}")
        return jsonify({"error": "Trend olan coinler çekilirken bir hata oluştu."}), 500


@app.route('/coin_details/<coin_id>')
def get_coin_details(coin_id):
    """Belirli bir coin'in detaylı bilgilerini çeker."""
    cache_key = f'coin_details_{coin_id}'
    try:
        url = f"{COINGECKO_BASE_URL}/coins/{coin_id}?localization=false&tickers=false&market_data=false&community_data=false&developer_data=false&sparkline=false"
        data = fetch_data_from_api(url, cache_key)
        
        # İhtiyacımız olan detayları seçiyoruz
        details = {
            "id": data.get('id'),
            "symbol": data.get('symbol', '').upper(),
            "name": data.get('name'),
            "description": data.get('description', {}).get('en', 'N/A'), # İngilizce açıklama
            "homepage": data.get('links', {}).get('homepage', [])[0] if data.get('links', {}).get('homepage') else 'N/A',
            "asset_platform_id": data.get('asset_platform_id'),
            "image_thumb": data.get('image', {}).get('thumb'),
            "image_small": data.get('image', {}).get('small'),
            "image_large": data.get('image', {}).get('large'),
            "market_cap_rank": data.get('market_cap_rank')
        }
        
        return jsonify(details)
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"Coin detayları hatası ({coin_id}): {e}")
        return jsonify({"error": f"{coin_id} için detaylar çekilirken bir hata oluştu."}), 500


@app.route('/coin_chart/<coin_id>/<int:days>')
def get_coin_price_chart(coin_id, days):
    """
    Belirli bir coin'in geçmiş fiyat grafiğini (days parametresi ile) oluşturur.
    `days` (gün) parametresi: 1, 7, 14, 30, 90, 180, 365, "max" olabilir.
    """
    if days not in [1, 7, 14, 30, 90, 180, 365] and days != "max":
        return jsonify({"error": "Geçersiz 'days' parametresi. Desteklenen değerler: 1, 7, 14, 30, 90, 180, 365, 'max'."}), 400

    cache_key = f'price_chart_{coin_id}_{days}'
    try:
        url = f"{COINGECKO_BASE_URL}/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
        market_data = fetch_data_from_api(url, cache_key)
        
        prices = market_data.get('prices')
        
        if not prices:
            return jsonify({"error": f"No price data available for {coin_id} for the last {days} days."}), 404

        dates = [datetime.datetime.fromtimestamp(p[0] / 1000) for p in prices]
        values = [p[1] for p in prices]

        title = f'{coin_id.capitalize()} Price Chart ({days} Gün)' if days != "max" else f'{coin_id.capitalize()} Fiyat Grafiği (Tüm Zamanlar)'
        y_label = 'Fiyat (USD)'
        color = '#00d8ff' # Mavi

        graphic_base64 = create_chart_image(dates, values, title, y_label, color)
        
        return jsonify({"chart": graphic_base64})
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"Fiyat grafiği oluşturma hatası ({coin_id}, {days} gün): {e}")
        return jsonify({"error": "Fiyat grafiği oluşturulurken bir hata oluştu."}), 500


@app.route('/market_cap_chart/<coin_id>/<int:days>')
def get_coin_market_cap_chart(coin_id, days):
    """
    Belirli bir coin'in geçmiş piyasa değeri grafiğini (days parametresi ile) oluşturur.
    `days` (gün) parametresi: 1, 7, 14, 30, 90, 180, 365, "max" olabilir.
    """
    if days not in [1, 7, 14, 30, 90, 180, 365] and days != "max":
        return jsonify({"error": "Geçersiz 'days' parametresi. Desteklenen değerler: 1, 7, 14, 30, 90, 180, 365, 'max'."}), 400

    cache_key = f'market_cap_chart_{coin_id}_{days}'
    try:
        # Hata düzeltildi: COINGECKO_BASE_BASE_URL -> COINGECKO_BASE_URL
        url = f"{COINGECKO_BASE_URL}/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
        market_data = fetch_data_from_api(url, cache_key)
        
        market_caps = market_data.get('market_caps')
        
        if not market_caps:
            return jsonify({"error": f"No market cap data available for {coin_id} for the last {days} days."}), 404

        dates = [datetime.datetime.fromtimestamp(p[0] / 1000) for p in market_caps]
        values = [p[1] for p in market_caps]

        title = f'{coin_id.capitalize()} Piyasa Değeri Grafiği ({days} Gün)' if days != "max" else f'{coin_id.capitalize()} Piyasa Değeri Grafiği (Tüm Zamanlar)'
        y_label = 'Piyasa Değeri (USD)'
        color = '#ff6b6b' # Kırmızı tonu

        graphic_base64 = create_chart_image(dates, values, title, y_label, color)
        
        return jsonify({"chart": graphic_base64})
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"Piyasa değeri grafiği oluşturma hatası ({coin_id}, {days} gün): {e}")
        return jsonify({"error": "Piyasa değeri grafiği oluşturulurken bir hata oluştu."}), 500


# Uygulama başlatma
if __name__ == '__main__':
    # Flask uygulamasını çalıştırmak için gunicorn gibi bir WSGI sunucusu kullanmak üretim için daha iyidir.
    # Ancak yerel testler için app.run(debug=True) kullanılabilir.
    # Eğer Render'da dağıtıyorsanız, Start Command'ınız `gunicorn app:app` olmalıdır.
    app.run(debug=True, host='0.0.0.0', port=5000) # host='0.0.0.0' dışarıdan erişime izin verir
