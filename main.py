import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import feedparser

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

BINANCE_URL = "https://data-api.binance.vision/api/v3/ticker/24hr"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
TRANSLATE_URL = "https://api.mymemory.translated.net/get"


# =========================
# BINANCE
# =========================

def get_price(symbol):
    try:
        r = requests.get(
            BINANCE_URL,
            params={"symbol": symbol},
            timeout=10
        )

        r.raise_for_status()
        data = r.json()

        if "lastPrice" not in data:
            print("BINANCE HATASI:", data)
            return None

        price = float(data["lastPrice"])
        change = float(data.get("priceChangePercent", 0))

        return price, change

    except Exception as e:
        print("FIYAT HATASI:", repr(e))
        return None


# =========================
# RSS HABER MOTORU
# =========================

def get_rss_news(feeds, limit=5):
    results = []
    seen = set()

    for feed_url, source_name in feeds:
        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()

                if not title or not link:
                    continue

                if link in seen:
                    continue

                seen.add(link)

                results.append({
                    "title": title,
                    "url": link,
                    "domain": source_name
                })

        except Exception as e:
            print(
                f"RSS HATASI ({source_name}):",
                repr(e)
            )

    return results[:limit]


def news_text(header, news):
    if not news:
        return (
            f"{header}\n\n"
            "⚠️ Şu anda haber alınamadı.\n\n"
            "🦇 Alfred haber servisi tekrar denenebilir."
        )

    text = f"{header}\n"
    text += "━━━━━━━━━━━━━━\n\n"

    for i, article in enumerate(news, 1):
        text += f"{i}. {article['title']}\n"
        text += f"🏛 Kaynak: {article['domain']}\n"
        text += f"🔗 {article['url']}\n\n"

    text += "━━━━━━━━━━━━━━\n"
    text += "🦇 Alfred 2.0"

    return text


# =========================
# HAVA DURUMU
# =========================

def weather_description(code):
    descriptions = {
        0: "☀️ Açık",
        1: "🌤️ Çoğunlukla açık",
        2: "⛅ Parçalı bulutlu",
        3: "☁️ Kapalı",
        45: "🌫️ Sisli",
        48: "🌫️ Kırağılı sis",
        51: "🌦️ Hafif çisenti",
        53: "🌦️ Çisenti",
        55: "🌧️ Yoğun çisenti",
        61: "🌧️ Hafif yağmur",
        63: "🌧️ Yağmur",
        65: "🌧️ Kuvvetli yağmur",
        71: "🌨️ Hafif kar",
        73: "🌨️ Kar",
        75: "❄️ Yoğun kar",
        80: "🌦️ Hafif sağanak",
        81: "🌧️ Sağanak",
        82: "⛈️ Kuvvetli sağanak",
        95: "⛈️ Gök gürültülü fırtına",
        96: "⛈️ Dolu ihtimali",
        99: "⛈️ Kuvvetli dolu"
    }

    return descriptions.get(
        code,
        "🌤️ Bilinmeyen hava durumu"
    )


def get_istanbul_weather():
    try:
        params = {
            "latitude": 41.0082,
            "longitude": 28.9784,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "precipitation,"
                "weather_code,"
                "wind_speed_10m"
            ),
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "timezone": "Europe/Istanbul"
        }

        r = requests.get(
            WEATHER_URL,
            params=params,
            timeout=15
        )

        r.raise_for_status()

        data = r.json()

        if "current" not in data:
            print("HAVA VERİ HATASI:", data)
            return None

        return data["current"]

    except Exception as e:
        print("HAVA DURUMU HATASI:", repr(e))
        return None


async def havadurumu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌤️ İstanbul hava durumu alınıyor...\n"
        "🦇 Alfred kontrol ediyor."
    )

    weather = get_istanbul_weather()

    if weather is None:
        await update.message.reply_text(
            "⚠️ İstanbul hava durumu alınamadı."
        )
        return

    temperature = weather.get("temperature_2m")
    humidity = weather.get("relative_humidity_2m")
    apparent = weather.get("apparent_temperature")
    precipitation = weather.get("precipitation")
    wind = weather.get("wind_speed_10m")
    code = weather.get("weather_code")

    description = weather_description(code)

    now = datetime.now(
        ZoneInfo("Europe/Istanbul")
    )

    day_names = [
        "Pazartesi",
        "Salı",
        "Çarşamba",
        "Perşembe",
        "Cuma",
        "Cumartesi",
        "Pazar"
    ]

    month_names = [
        "Ocak",
        "Şubat",
        "Mart",
        "Nisan",
        "Mayıs",
        "Haziran",
        "Temmuz",
        "Ağustos",
        "Eylül",
        "Ekim",
        "Kasım",
        "Aralık"
    ]

    day_name = day_names[now.weekday()]
    month_name = month_names[now.month - 1]

    current_time = (
        f"{day_name} — "
        f"{now.day} {month_name} {now.year} — "
        f"{now.strftime('%H:%M')}"
    )

    text = (
        "🌤️ ALFRED — İSTANBUL HAVA DURUMU\n\n"
        "📍 İstanbul\n"
        f"{description}\n\n"
        f"📅 {current_time}\n\n"
        f"🌡️ Sıcaklık: {temperature:.1f}°C\n"
        f"🌡️ Hissedilen: {apparent:.1f}°C\n"
        f"💧 Nem: %{humidity}\n"
        f"💨 Rüzgâr: {wind:.1f} km/sa\n"
        f"🌧️ Yağış: {precipitation:.1f} mm\n\n"
        "━━━━━━━━━━━━━━\n"
        "🦇 Alfred 2.0"
    )

    await update.message.reply_text(text)


# =========================
# ÇEVİRİ
# =========================

def translate_to_turkish(text):
    try:
        params = {
            "q": text,
            "langpair": "aut|tr"
        }

        r = requests.get(
            TRANSLATE_URL,
            params=params,
            timeout=20
        )

        r.raise_for_status()

        data = r.json()

        response_data = data.get("responseData", {})
        translated = response_data.get(
            "translatedText",
            ""
        ).strip()

        if not translated:
            print("ÇEVİRİ VERİ HATASI:", data)
            return None

        return translated

    except Exception as e:
        print("ÇEVİRİ HATASI:", repr(e))
        return None


async def cevir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🌍 ALFRED ÇEVİRİ\n\n"
            "Çevirmek istediğin metni /cevir komutundan "
            "sonra yaz.\n\n"
            "Örnek:\n"
            "/cevir Hello, how are you?"
        )
        return

    text = " ".join(context.args)

    await update.message.reply_text(
        "🌍 Metin çevriliyor...\n"
        "🦇 Alfred çalışıyor."
    )

    translated = translate_to_turkish(text)

    if translated is None:
        await update.message.reply_text(
            "⚠️ Çeviri yapılamadı.\n\n"
            "Lütfen biraz sonra tekrar dene."
        )
        return

    await update.message.reply_text(
        "🌍 ALFRED — ÇEVİRİ\n\n"
        f"📝 Orijinal:\n{text}\n\n"
        "🇹🇷 Türkçe:\n"
        f"{translated}"
    )


# =========================
# SISTEM
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🦇 Alfred 2.0 aktif.\n\n"
        "Komutları görmek için /yardim yaz."
    )


async def yardim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🦇 ALFRED 2.0 KOMUTLARI\n\n"
        "📈 PİYASA\n"
        "/fiyatbtc\n"
        "/fiyatsol\n"
        "/tara\n\n"
        "📰 HABERLER\n"
        "/haber\n"
        "/haberturk\n"
        "/haberkripto\n\n"
        "🌍 ARAÇLAR\n"
        "/havadurumu\n"
        "/cevir\n"
        "/ozetcikar\n\n"
        "🧠 ALFRED\n"
        "/sor\n"
        "/radar\n\n"
        "⚙️ SİSTEM\n"
        "/start\n"
        "/yardim"
    )


# =========================
# BTC
# =========================

async def fiyatbtc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_price("BTCUSDT")

    if result is None:
        await update.message.reply_text(
            "⚠️ BTC fiyatı alınamadı."
        )
        return

    price, change = result

    await update.message.reply_text(
        f"₿ BTC / USDT\n\n"
        f"💰 Fiyat: ${price:,.2f}\n"
        f"📊 24s: {change:+.2f}%"
    )


# =========================
# SOL
# =========================

async def fiyatsol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_price("SOLUSDT")

    if result is None:
        await update.message.reply_text(
            "⚠️ SOL fiyatı alınamadı."
        )
        return

    price, change = result

    await update.message.reply_text(
        f"◎ SOL / USDT\n\n"
        f"💰 Fiyat: ${price:,.2f}\n"
        f"📊 24s: {change:+.2f}%"
    )


# =========================
# TARA
# =========================

async def tara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔎 Binance piyasası taranıyor...\n"
        "🦇 Alfred analiz yapıyor."
    )

    try:
        r = requests.get(
            BINANCE_URL,
            timeout=20
        )

        r.raise_for_status()
        data = r.json()

        if not isinstance(data, list):
            print("TARA VERİ HATASI:", data)
            await update.message.reply_text(
                "⚠️ Binance tarama verisi alınamadı."
            )
            return

        coins = []

        excluded = [
            "USDCUSDT",
            "FDUSDUSDT",
            "TUSDUSDT",
            "USDTUSDT",
            "DAIUSDT"
        ]

        for item in data:
            symbol = item.get("symbol", "")

            if not symbol.endswith("USDT"):
                continue

            if symbol in excluded:
                continue

            try:
                change = float(
                    item.get("priceChangePercent", 0)
                )

                volume = float(
                    item.get("quoteVolume", 0)
                )

                price = float(
                    item.get("lastPrice", 0)
                )

            except (TypeError, ValueError):
                continue

            if volume < 1000000:
                continue

            if change <= 0:
                continue

            coins.append({
                "symbol": symbol.replace("USDT", ""),
                "change": change,
                "volume": volume,
                "price": price
            })

        coins.sort(
            key=lambda x: x["change"],
            reverse=True
        )

        top = coins[:5]

        if not top:
            await update.message.reply_text(
                "⚠️ Uygun sinyal bulunamadı."
            )
            return

        text = "🦇 ALFRED 2.0 RADAR\n\n"
        text += "📈 En güçlü hareketler:\n\n"

        for i, coin in enumerate(top, 1):
            text += (
                f"{i}. 🔥 {coin['symbol']}\n"
                f"📈 24s: +{coin['change']:.2f}%\n"
                f"💰 Hacim: ${coin['volume']:,.0f}\n"
                f"💵 Fiyat: ${coin['price']:.8f}\n\n"
            )

        text += "⚠️ Bu liste AL/SAT garantisi değildir."

        await update.message.reply_text(text)

    except Exception as e:
        print("TARA HATASI:", repr(e))

        await update.message.reply_text(
            "⚠️ Tarama sırasında hata oluştu."
        )


# =========================
# DÜNYA HABERLERİ
# =========================

async def haber(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌍 Dünya haberleri taranıyor..."
    )

    feeds = [
        (
            "https://feeds.bbci.co.uk/news/world/rss.xml",
            "BBC"
        ),
        (
            "https://rss.dw.com/rdf/rss-en-world",
            "DW"
        ),
        (
            "https://apnews.com/hub/world-news?output=1",
            "AP"
        )
    ]

    news = get_rss_news(feeds, 5)

    await update.message.reply_text(
        news_text(
            "🌍 ALFRED — DÜNYA HABERLERİ",
            news
        )
    )


# =========================
# TÜRKİYE HABERLERİ
# =========================

async def haberturk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🇹🇷 Türkiye haberleri taranıyor..."
    )

    feeds = [
        (
            "https://www.aa.com.tr/tr/rss/default?cat=guncel",
            "Anadolu Ajansı"
        ),
        (
            "https://feeds.bbci.co.uk/turkce/rss.xml",
            "BBC Türkçe"
        ),
        (
            "https://rss.dw.com/rdf/rss-tur",
            "DW Türkçe"
        )
    ]

    news = get_rss_news(feeds, 5)

    await update.message.reply_text(
        news_text(
            "🇹🇷 ALFRED — TÜRKİYE HABERLERİ",
            news
        )
    )


# =========================
# KRİPTO HABERLERİ
# =========================

async def haberkripto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "₿ Kripto haberleri taranıyor..."
    )

    feeds = [
        (
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "CoinDesk"
        ),
        (
            "https://decrypt.co/feed",
            "Decrypt"
        ),
        (
            "https://www.theblock.co/rss.xml",
            "The Block"
        )
    ]

    news = get_rss_news(feeds, 5)

    await update.message.reply_text(
        news_text(
            "₿ ALFRED — KRİPTO HABERLERİ",
            news
        )
    )


# =========================
# ÖZET
# =========================

async def ozetcikar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 Özet çıkarma modülü hazırlanıyor."
    )


# =========================
# ALFRED
# =========================

async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 Alfred AI soru-cevap modülü hazırlanıyor."
    )


async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📡 Radar aktif.\n\n"
        "🌍 Olağandışı gelişmeler ve piyasa anomalileri "
        "modülü hazırlanıyor."
    )


# =========================
# BOT
# =========================

def main():
    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN bulunamadı."
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("yardim", yardim))

    app.add_handler(CommandHandler("fiyatbtc", fiyatbtc))
    app.add_handler(CommandHandler("fiyatsol", fiyatsol))
    app.add_handler(CommandHandler("tara", tara))

    app.add_handler(CommandHandler("haber", haber))
    app.add_handler(CommandHandler("haberturk", haberturk))
    app.add_handler(CommandHandler("haberkripto", haberkripto))

    app.add_handler(CommandHandler("havadurumu", havadurumu))
    app.add_handler(CommandHandler("cevir", cevir))
    app.add_handler(CommandHandler("ozetcikar", ozetcikar))

    app.add_handler(CommandHandler("sor", sor))
    app.add_handler(CommandHandler("radar", radar))

    print("🦇 Alfred 2.0 aktif.")

    app.run_polling()


if __name__ == "__main__":
    main()
