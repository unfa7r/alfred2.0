import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import feedparser
from langdetect import detect, LangDetectException

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)


# =========================================================
# AYARLAR
# =========================================================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

BINANCE_URL = "https://data-api.binance.vision/api/v3/ticker/24hr"

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

TRANSLATE_URL = "https://api.mymemory.translated.net/get"


# =========================================================
# BINANCE
# =========================================================

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
        change = float(
            data.get("priceChangePercent", 0)
        )

        return price, change

    except Exception as e:
        print("FIYAT HATASI:", repr(e))
        return None


# =========================================================
# RSS HABERLER
# =========================================================

WORLD_FEEDS = [
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


TURKEY_FEEDS = [
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


CRYPTO_FEEDS = [
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


def get_rss_news(feeds, limit=5):
    results = []
    seen = set()

    for feed_url, source_name in feeds:

        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries:

                title = entry.get(
                    "title",
                    ""
                ).strip()

                link = entry.get(
                    "link",
                    ""
                ).strip()

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


def news_text(title, feeds):
    news = get_rss_news(
        feeds,
        limit=5
    )

    if not news:
        return (
            f"📰 {title}\n\n"
            "Şu anda haber alınamadı."
        )

    text = f"📰 {title}\n\n"

    for i, item in enumerate(news, 1):

        text += (
            f"{i}. {item['title']}\n"
            f"📡 {item['domain']}\n"
            f"🔗 {item['url']}\n\n"
        )

    return text


# =========================================================
# HAVA DURUMU
# =========================================================

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

            print(
                "HAVA VERİ HATASI:",
                data
            )

            return None

        return data["current"]

    except Exception as e:

        print(
            "HAVA DURUMU HATASI:",
            repr(e)
        )

        return None


# =========================================================
# 30 DİLLİ ÇEVİRİ SİSTEMİ
# =========================================================

LANGUAGE_NAMES = {

    "tr": "🇹🇷 Türkçe",

    "en": "🇬🇧 İngilizce",

    "de": "🇩🇪 Almanca",

    "fr": "🇫🇷 Fransızca",

    "es": "🇪🇸 İspanyolca",

    "it": "🇮🇹 İtalyanca",

    "pt": "🇵🇹 Portekizce",

    "ru": "🇷🇺 Rusça",

    "zh-CN": "🇨🇳 Çince",

    "ja": "🇯🇵 Japonca",

    "ko": "🇰🇷 Korece",

    "ar": "🇸🇦 Arapça",

    "hi": "🇮🇳 Hintçe",

    "nl": "🇳🇱 Felemenkçe",

    "pl": "🇵🇱 Lehçe",

    "uk": "🇺🇦 Ukraynaca",

    "th": "🇹🇭 Tayca",

    "vi": "🇻🇳 Vietnamca",

    "id": "🇮🇩 Endonezce",

    "ms": "🇲🇾 Malayca",

    "sv": "🇸🇪 İsveççe",

    "no": "🇳🇴 Norveççe",

    "da": "🇩🇰 Danca",

    "fi": "🇫🇮 Fince",

    "cs": "🇨🇿 Çekçe",

    "el": "🇬🇷 Yunanca",

    "hu": "🇭🇺 Macarca",

    "ro": "🇷🇴 Romence",

    "he": "🇮🇱 İbranice",

    "sk": "🇸🇰 Slovakça"
}


# MyMemory için dil kodları
MYMEMORY_CODES = {

    "tr": "tr",

    "en": "en",

    "de": "de",

    "fr": "fr",

    "es": "es",

    "it": "it",

    "pt": "pt",

    "ru": "ru",

    "zh-CN": "zh-CN",

    "ja": "ja",

    "ko": "ko",

    "ar": "ar",

    "hi": "hi",

    "nl": "nl",

    "pl": "pl",

    "uk": "uk",

    "th": "th",

    "vi": "vi",

    "id": "id",

    "ms": "ms",

    "sv": "sv",

    "no": "no",

    "da": "da",

    "fi": "fi",

    "cs": "cs",

    "el": "el",

    "hu": "hu",

    "ro": "ro",

    "he": "he",

    "sk": "sk"
}


def detect_language(text):

    try:

        detected = detect(text)

        # langdetect'in bazı kodlarını
        # sistemimizde kullanılan kodlara çevir

        if detected == "zh":
            return "zh-CN"

        if detected in MYMEMORY_CODES:
            return detected

        # Desteklemediğimiz bir dil algılanırsa
        # İngilizce varsaymak yerine hata döndür

        return None

    except LangDetectException as e:

        print(
            "DİL ALGILAMA HATASI:",
            repr(e)
        )

        return None

    except Exception as e:

        print(
            "DİL ALGILAMA HATASI:",
            repr(e)
        )

        return None


def translate_to_turkish(text):

    try:

        source_language = detect_language(text)

        if source_language is None:
            return None, None

        if source_language == "tr":
            return text, source_language

        source_code = MYMEMORY_CODES.get(
            source_language
        )

        if not source_code:
            return None, source_language

        params = {

            "q": text,

            "langpair": (
                f"{source_code}|tr"
            )
        }

        r = requests.get(

            TRANSLATE_URL,

            params=params,

            timeout=20
        )

        r.raise_for_status()

        data = r.json()

        response_data = data.get(
            "responseData",
            {}
        )

        translated = response_data.get(
            "translatedText",
            ""
        ).strip()

        if not translated:

            print(
                "ÇEVİRİ VERİ HATASI:",
                data
            )

            return None, source_language

        return translated, source_language

    except Exception as e:

        print(
            "ÇEVİRİ HATASI:",
            repr(e)
        )

        return None, None


# =========================================================
# TELEGRAM KOMUTLARI
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🦇 ALFRED 2.0\n\n"
        "Hoş geldin.\n"
        "Sisteme hazırım.\n\n"
        "Komutları görmek için:\n"
        "/yardim"
    )


async def yardim(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
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

    await update.message.reply_text(text)


# =========================================================
# BTC
# =========================================================

async def fiyatbtc(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    result = get_price("BTCUSDT")

    if result is None:

        await update.message.reply_text(
            "⚠️ BTC fiyatı alınamadı."
        )

        return

    price, change = result

    await update.message.reply_text(

        "₿ BITCOIN\n\n"

        f"💰 Fiyat: ${price:,.2f}\n"
        f"📊 24s: {change:+.2f}%"
    )


# =========================================================
# SOL
# =========================================================

async def fiyatsol(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    result = get_price("SOLUSDT")

    if result is None:

        await update.message.reply_text(
            "⚠️ SOL fiyatı alınamadı."
        )

        return

    price, change = result

    await update.message.reply_text(

        "◎ SOLANA\n\n"

        f"💰 Fiyat: ${price:,.2f}\n"
        f"📊 24s: {change:+.2f}%"
    )


# =========================================================
# TARAMA
# =========================================================

async def tara(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🔎 Alfred piyasayı tarıyor...\n"
        "🦇 Birkaç saniye."
    )

    try:

        r = requests.get(
            BINANCE_URL,
            timeout=15
        )

        r.raise_for_status()

        data = r.json()

        usdt_pairs = [

            x for x in data

            if x.get("symbol", "").endswith(
                "USDT"
            )
            and float(
                x.get("quoteVolume", 0)
            ) > 1000000
        ]

        usdt_pairs.sort(

            key=lambda x:
            float(
                x.get(
                    "priceChangePercent",
                    0
                )
            ),

            reverse=True
        )

        top = usdt_pairs[:5]

        if not top:

            await update.message.reply_text(
                "⚠️ Tarama sonucu bulunamadı."
            )

            return

        text = (
            "📡 ALFRED — PİYASA TARAMASI\n\n"
        )

        for i, coin in enumerate(top, 1):

            symbol = coin["symbol"]

            change = float(
                coin.get(
                    "priceChangePercent",
                    0
                )
            )

            price = float(
                coin.get(
                    "lastPrice",
                    0
                )
            )

            text += (

                f"{i}. {symbol}\n"

                f"💰 ${price:g}\n"

                f"📈 24s: {change:+.2f}%\n\n"
            )

        text += (
            "⚠️ Bu liste garanti kazanç anlamına "
            "gelmez. Piyasa hızlı değişebilir."
        )

        await update.message.reply_text(
            text
        )

    except Exception as e:

        print(
            "TARAMA HATASI:",
            repr(e)
        )

        await update.message.reply_text(
            "⚠️ Piyasa taraması başarısız."
        )


# =========================================================
# HABERLER
# =========================================================

async def haber(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        news_text(
            "DÜNYA HABERLERİ",
            WORLD_FEEDS
        )
    )


async def haberturk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        news_text(
            "TÜRKİYE HABERLERİ",
            TURKEY_FEEDS
        )
    )


async def haberkripto(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        news_text(
            "KRİPTO HABERLERİ",
            CRYPTO_FEEDS
        )
    )


# =========================================================
# HAVA DURUMU
# =========================================================

async def havadurumu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    weather = get_istanbul_weather()

    if weather is None:

        await update.message.reply_text(
            "⚠️ İstanbul hava durumu alınamadı."
        )

        return

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

    day_name = day_names[
        now.weekday()
    ]

    month_name = month_names[
        now.month - 1
    ]

    current_time = (

        f"{day_name} — "
        f"{now.day} {month_name} "
        f"{now.year} — "
        f"{now.strftime('%H:%M')}"
    )

    temperature = weather.get(
        "temperature_2m"
    )

    apparent = weather.get(
        "apparent_temperature"
    )

    humidity = weather.get(
        "relative_humidity_2m"
    )

    precipitation = weather.get(
        "precipitation"
    )

    wind = weather.get(
        "wind_speed_10m"
    )

    code = weather.get(
        "weather_code"
    )

    description = weather_description(
        code
    )

    await update.message.reply_text(

        "🌤️ İSTANBUL HAVA DURUMU\n\n"

        f"📅 {current_time}\n\n"

        f"{description}\n\n"

        f"🌡️ Sıcaklık: "
        f"{temperature}°C\n"

        f"🤚 Hissedilen: "
        f"{apparent}°C\n"

        f"💧 Nem: "
        f"%{humidity}\n"

        f"🌧️ Yağış: "
        f"{precipitation} mm\n"

        f"💨 Rüzgar: "
        f"{wind} km/sa"
    )


# =========================================================
# ÇEVİRİ
# =========================================================

async def cevir(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.args:

        await update.message.reply_text(

            "🌍 ALFRED ÇEVİRİ\n\n"

            "Çevirmek istediğin metni "
            "/cevir komutundan sonra yaz.\n\n"

            "Örnek:\n"

            "/cevir Hello, how are you?"
        )

        return

    text = " ".join(
        context.args
    )

    await update.message.reply_text(

        "🌍 Metin analiz ediliyor...\n"
        "🦇 Alfred çalışıyor."
    )

    translated, source_language = (
        translate_to_turkish(text)
    )

    if translated is None:

        await update.message.reply_text(

            "⚠️ Çeviri yapılamadı.\n\n"

            "Metnin dili desteklenen 30 dil "
            "arasında olmayabilir veya "
            "çeviri servisi geçici olarak "
            "yanıt vermiyor olabilir."
        )

        return

    detected_name = LANGUAGE_NAMES.get(

        source_language,

        source_language
        if source_language
        else "Bilinmeyen dil"
    )

    await update.message.reply_text(

        "🌍 ALFRED — ÇEVİRİ\n\n"

        f"🔎 Algılanan dil: "
        f"{detected_name}\n\n"

        f"📝 Orijinal:\n"
        f"{text}\n\n"

        "🇹🇷 Türkçe:\n"
        f"{translated}"
    )


# =========================================================
# ÖZET
# =========================================================

async def ozetcikar(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.args:

        await update.message.reply_text(

            "📝 ALFRED ÖZET\n\n"

            "Özetlemek istediğin metni "
            "komuttan sonra yaz.\n\n"

            "Örnek:\n"
            "/ozetcikar Buraya uzun metni yaz..."
        )

        return

    text = " ".join(
        context.args
    )

    await update.message.reply_text(

        "📝 Metin alındı.\n\n"

        "🦇 AI özet sistemi henüz "
        "bağlanmadı."
    )


# =========================================================
# SOR
# =========================================================

async def sor(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.args:

        await update.message.reply_text(

            "🧠 ALFRED SORU SİSTEMİ\n\n"

            "Örnek:\n"
            "/sor Bitcoin nedir?"
        )

        return

    question = " ".join(
        context.args
    )

    await update.message.reply_text(

        "🧠 Alfred sorunu aldı.\n\n"

        f"❓ {question}\n\n"

        "AI cevap sistemi henüz "
        "bağlanmadı."
    )


# =========================================================
# RADAR
# =========================================================

async def radar(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "📡 ALFRED RADAR\n\n"

        "🌍 Küresel olay radarı hazır.\n\n"

        "Gelişmiş anomali ve olay taraması "
        "bir sonraki aşamada bağlanacak."
    )


# =========================================================
# BOT
# =========================================================

def main():

    if not TOKEN:

        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN bulunamadı."
        )

    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    # Sistem
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "yardim",
            yardim
        )
    )

    # Piyasa
    app.add_handler(
        CommandHandler(
            "fiyatbtc",
            fiyatbtc
        )
    )

    app.add_handler(
        CommandHandler(
            "fiyatsol",
            fiyatsol
        )
    )

    app.add_handler(
        CommandHandler(
            "tara",
            tara
        )
    )

    # Haberler
    app.add_handler(
        CommandHandler(
            "haber",
            haber
        )
    )

    app.add_handler(
        CommandHandler(
            "haberturk",
            haberturk
        )
    )

    app.add_handler(
        CommandHandler(
            "haberkripto",
            haberkripto
        )
    )

    # Araçlar
    app.add_handler(
        CommandHandler(
            "havadurumu",
            havadurumu
        )
    )

    app.add_handler(
        CommandHandler(
            "cevir",
            cevir
        )
    )

    app.add_handler(
        CommandHandler(
            "ozetcikar",
            ozetcikar
        )
    )

    # Alfred
    app.add_handler(
        CommandHandler(
            "sor",
            sor
        )
    )

    app.add_handler(
        CommandHandler(
            "radar",
            radar
        )
    )

    print(
        "🦇 Alfred 2.0 çalışıyor..."
    )

    app.run_polling()


if __name__ == "__main__":
    main()
