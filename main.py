import os
import requests
import feedparser

from datetime import datetime
from zoneinfo import ZoneInfo

from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

from groq import Groq

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)


# =========================================================
# AYARLAR
# =========================================================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

BINANCE_URL = "https://data-api.binance.vision/api/v3/ticker/24hr"

TRANSLATE_URL = "https://api.mymemory.translated.net/get"

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

ISTANBUL_LAT = 41.0082
ISTANBUL_LON = 28.9784

GROQ_MODEL = "openai/gpt-oss-120b"


# =========================================================
# GROQ
# =========================================================

groq_client = None

if GROQ_API_KEY:
    groq_client = Groq(
        api_key=GROQ_API_KEY
    )


# =========================================================
# HABER KAYNAKLARI
# =========================================================

WORLD_FEEDS = [
    ("https://feeds.bbci.co.uk/news/world/rss.xml", "BBC"),
    ("https://rss.dw.com/rdf/rss-en-world", "DW"),
    ("https://apnews.com/hub/world-news?output=1", "AP"),
]

TURKEY_FEEDS = [
    ("https://www.aa.com.tr/tr/rss/default?cat=guncel", "Anadolu Ajansı"),
    ("https://feeds.bbci.co.uk/turkce/rss.xml", "BBC Türkçe"),
    ("https://rss.dw.com/rdf/rss-tur", "DW Türkçe"),
]

CRYPTO_FEEDS = [
    ("https://www.coindesk.com/arc/outboundfeeds/rss/", "CoinDesk"),
    ("https://decrypt.co/feed", "Decrypt"),
    ("https://www.theblock.co/rss.xml", "The Block"),
]


# =========================================================
# RADAR KAYNAKLARI
# =========================================================

RADAR_WORLD_FEEDS = [
    ("https://feeds.bbci.co.uk/news/world/rss.xml", "BBC Dünya"),
    ("https://rss.dw.com/rdf/rss-en-world", "DW Dünya"),
]

RADAR_TURKEY_FEEDS = [
    ("https://www.aa.com.tr/tr/rss/default?cat=guncel", "Anadolu Ajansı"),
    ("https://feeds.bbci.co.uk/turkce/rss.xml", "BBC Türkçe"),
    ("https://rss.dw.com/rdf/rss-tur", "DW Türkçe"),
]

RADAR_ECONOMY_FEEDS = [
    ("https://feeds.bbci.co.uk/news/business/rss.xml", "BBC Ekonomi"),
    ("https://rss.dw.com/rdf/rss-en-bus", "DW Ekonomi"),
]


# =========================================================
# DİL
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
    "sk": "🇸🇰 Slovakça",
}


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
    "sk": "sk",
}


# =========================================================
# HABER ÇEVİRİ ÖNBELLEĞİ
# =========================================================

NEWS_TRANSLATION_CACHE = {}


# =========================================================
# DİL ALGILAMA
# =========================================================

def detect_language(text):
    try:
        detected = detect(text)

        if detected == "zh":
            return "zh-CN"

        if detected in MYMEMORY_CODES:
            return detected

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


# =========================================================
# GENEL ÇEVİRİ
# =========================================================

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
            "langpair": f"{source_code}|tr",
        }

        r = requests.get(
            TRANSLATE_URL,
            params=params,
            timeout=20,
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

        if (
            "INVALID SOURCE LANGUAGE"
            in translated.upper()
            or (
                "MYMEMORY"
                in translated.upper()
                and "ERROR"
                in translated.upper()
            )
        ):
            print(
                "ÇEVİRİ SERVİS HATASI:",
                translated
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
# HABER BAŞLIĞI ÇEVİRİSİ
# =========================================================

def translate_news_title(title):
    title = title.strip()

    if not title:
        return title

    if title in NEWS_TRANSLATION_CACHE:
        return NEWS_TRANSLATION_CACHE[title]

    try:
        params = {
            "q": title,
            "langpair": "en|tr",
        }

        r = requests.get(
            TRANSLATE_URL,
            params=params,
            timeout=20,
        )

        r.raise_for_status()

        data = r.json()

        response_status = data.get(
            "responseStatus"
        )

        if response_status not in (
            None,
            200,
        ):
            print(
                "HABER ÇEVİRİ SERVİSİ HATASI:",
                data.get("responseDetails")
            )

            NEWS_TRANSLATION_CACHE[title] = title
            return title

        response_data = data.get(
            "responseData",
            {}
        )

        translated = response_data.get(
            "translatedText",
            ""
        ).strip()

        if not translated:
            NEWS_TRANSLATION_CACHE[title] = title
            return title

        error_text = translated.upper()

        if (
            "INVALID SOURCE LANGUAGE"
            in error_text
            or (
                "MYMEMORY"
                in error_text
                and "ERROR"
                in error_text
            )
            or "QUOTA" in error_text
        ):
            NEWS_TRANSLATION_CACHE[title] = title
            return title

        NEWS_TRANSLATION_CACHE[title] = translated

        return translated

    except Exception as e:
        print(
            "HABER BAŞLIK ÇEVİRİ HATASI:",
            repr(e)
        )

        NEWS_TRANSLATION_CACHE[title] = title

        return title


# =========================================================
# RSS HABERLER
# =========================================================

def get_rss_news(
    feeds,
    limit=5,
    translate_titles=True,
):
    results = []
    seen = set()

    for feed_url, source_name in feeds:

        try:
            feed = feedparser.parse(
                feed_url
            )

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

                if translate_titles:
                    translated_title = (
                        translate_news_title(
                            title
                        )
                    )
                else:
                    translated_title = title

                results.append({
                    "title": translated_title,
                    "original_title": title,
                    "url": link,
                    "domain": source_name,
                })

                if len(results) >= limit:
                    return results

        except Exception as e:
            print(
                f"RSS HATASI ({source_name}):",
                repr(e)
            )

    return results


# =========================================================
# HABER METNİ
# =========================================================

def news_text(
    title,
    feeds,
    translate_titles=True,
):
    news = get_rss_news(
        feeds,
        limit=5,
        translate_titles=translate_titles,
    )

    if not news:
        return (
            f"📰 {title}\n\n"
            "Şu anda haber alınamadı."
        )

    text = f"📰 {title}\n\n"

    for i, item in enumerate(
        news,
        1
    ):
        text += (
            f"{i}. {item['title']}\n"
            f"📡 {item['domain']}\n"
            f"🔗 {item['url']}\n\n"
        )

    return text


# =========================================================
# BINANCE
# =========================================================

def get_price(symbol):
    try:
        r = requests.get(
            BINANCE_URL,
            params={
                "symbol": symbol
            },
            timeout=10,
        )

        r.raise_for_status()

        data = r.json()

        if "lastPrice" not in data:
            print(
                "BINANCE HATASI:",
                data
            )
            return None

        price = float(
            data["lastPrice"]
        )

        change = float(
            data.get(
                "priceChangePercent",
                0
            )
        )

        return price, change

    except Exception as e:
        print(
            "FIYAT HATASI:",
            repr(e)
        )
        return None


# =========================================================
# /FIYATBTC
# =========================================================

async def fiyatbtc(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    result = get_price(
        "BTCUSDT"
    )

    if not result:
        await update.message.reply_text(
            "❌ BTC fiyatı alınamadı."
        )
        return

    price, change = result

    emoji = (
        "🟢"
        if change >= 0
        else "🔴"
    )

    await update.message.reply_text(
        f"₿ Bitcoin\n\n"
        f"💰 {price:,.2f} USDT\n"
        f"{emoji} 24s: %{change:.2f}"
    )


# =========================================================
# /FIYATSOL
# =========================================================

async def fiyatsol(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    result = get_price(
        "SOLUSDT"
    )

    if not result:
        await update.message.reply_text(
            "❌ SOL fiyatı alınamadı."
        )
        return

    price, change = result

    emoji = (
        "🟢"
        if change >= 0
        else "🔴"
    )

    await update.message.reply_text(
        f"◎ Solana\n\n"
        f"💰 {price:,.2f} USDT\n"
        f"{emoji} 24s: %{change:.2f}"
    )


# =========================================================
# /TARA
# =========================================================

async def tara(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "🔎 Binance taraması yapıyorum..."
    )

    try:
        r = requests.get(
            BINANCE_URL,
            timeout=15,
        )

        r.raise_for_status()

        data = r.json()

        candidates = []

        for item in data:

            symbol = item.get(
                "symbol",
                ""
            )

            if not symbol.endswith(
                "USDT"
            ):
                continue

            try:
                price = float(
                    item["lastPrice"]
                )

                change = float(
                    item["priceChangePercent"]
                )

                volume = float(
                    item["quoteVolume"]
                )

            except Exception:
                continue

            if volume < 1_000_000:
                continue

            if change <= 0:
                continue

            score = (
                change * 0.7
                + (
                    min(
                        volume / 10_000_000,
                        10
                    )
                    * 0.3
                )
            )

            candidates.append({
                "symbol": symbol,
                "price": price,
                "change": change,
                "volume": volume,
                "score": score,
            })

        candidates.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        top = candidates[:10]

        if not top:
            await update.message.reply_text(
                "⚠️ Şu anda uygun momentum "
                "adayı bulunamadı."
            )
            return

        text = (
            "🦇 ALFRED RADAR\n\n"
            "Binance USDT paritelerinde "
            "pozitif momentum taraması:\n\n"
        )

        for i, coin in enumerate(
            top,
            1
        ):

            emoji = (
                "🚀"
                if coin["change"] >= 5
                else "🟢"
            )

            text += (
                f"{i}. {emoji} "
                f"{coin['symbol']}\n"
                f"   💰 {coin['price']:.8f}\n"
                f"   📈 %{coin['change']:.2f}\n"
                f"   💧 Hacim: "
                f"{coin['volume']:,.0f} USDT\n\n"
            )

        text += (
            "⚠️ Bu liste kâr garantisi değildir. "
            "Momentum yüksek olduğu kadar "
            "risk de yüksek olabilir."
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
            "❌ Binance taraması sırasında "
            "hata oluştu."
        )


# =========================================================
# /HABER
# =========================================================

async def haber(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        news_text(
            "Dünya Haberleri",
            WORLD_FEEDS,
            translate_titles=True,
        )
    )


# =========================================================
# /HABERTURK
# =========================================================

async def haberturk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        news_text(
            "Türkiye Haberleri",
            TURKEY_FEEDS,
            translate_titles=False,
        )
    )


# =========================================================
# /HABERKRIPTO
# =========================================================

async def haberkripto(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        news_text(
            "Kripto Haberleri",
            CRYPTO_FEEDS,
            translate_titles=True,
        )
    )


# =========================================================
# /CEVIR
# =========================================================

async def cevir(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not context.args:
        await update.message.reply_text(
            "🌍 /cevir\n\n"
            "Çevirmek istediğin metni yaz.\n\n"
            "Örnek:\n"
            "/cevir Hello, how are you?"
        )
        return

    text = " ".join(
        context.args
    )

    translated, source_language = (
        translate_to_turkish(
            text
        )
    )

    if not translated:
        await update.message.reply_text(
            "❌ Metin çevrilemedi.\n"
            "Biraz daha kısa bir metin "
            "deneyebilirsin."
        )
        return

    language_name = LANGUAGE_NAMES.get(
        source_language,
        source_language or "Bilinmiyor"
    )

    await update.message.reply_text(
        f"🌍 Kaynak dil: {language_name}\n\n"
        f"🇹🇷 {translated}"
    )


# =========================================================
# /HAVADURUMU
# =========================================================

async def havadurumu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    try:
        params = {
            "latitude": ISTANBUL_LAT,
            "longitude": ISTANBUL_LON,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "precipitation,"
                "weather_code,"
                "wind_speed_10m"
            ),
            "timezone": "Europe/Istanbul",
        }

        r = requests.get(
            WEATHER_URL,
            params=params,
            timeout=15,
        )

        r.raise_for_status()

        data = r.json()

        current = data.get(
            "current",
            {}
        )

        temperature = current.get(
            "temperature_2m"
        )

        humidity = current.get(
            "relative_humidity_2m"
        )

        apparent = current.get(
            "apparent_temperature"
        )

        precipitation = current.get(
            "precipitation"
        )

        wind = current.get(
            "wind_speed_10m"
        )

        weather_code = current.get(
            "weather_code"
        )

        weather_names = {
            0: "Açık",
            1: "Çoğunlukla açık",
            2: "Parçalı bulutlu",
            3: "Kapalı",
            45: "Sisli",
            48: "Kırağılı sis",
            51: "Hafif çiseleme",
            53: "Çiseleme",
            55: "Yoğun çiseleme",
            61: "Hafif yağmur",
            63: "Yağmur",
            65: "Kuvvetli yağmur",
            71: "Hafif kar",
            73: "Kar",
            75: "Yoğun kar",
            80: "Hafif sağanak",
            81: "Sağanak",
            82: "Kuvvetli sağanak",
            95: "Gök gürültülü fırtına",
        }

        description = weather_names.get(
            weather_code,
            "Bilinmeyen hava"
        )

        now = datetime.now(
            ZoneInfo(
                "Europe/Istanbul"
            )
        )

        days = [
            "Pazartesi",
            "Salı",
            "Çarşamba",
            "Perşembe",
            "Cuma",
            "Cumartesi",
            "Pazar",
        ]

        months = [
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
            "Aralık",
        ]

        date_text = (
            f"{now.day} "
            f"{months[now.month - 1]} "
            f"{now.year}, "
            f"{days[now.weekday()]}"
        )

        await update.message.reply_text(
            f"🌤️ İstanbul Hava Durumu\n\n"
            f"📅 {date_text}\n"
            f"🕒 {now.strftime('%H:%M')}\n\n"
            f"🌡️ Sıcaklık: {temperature}°C\n"
            f"🌡️ Hissedilen: {apparent}°C\n"
            f"💧 Nem: %{humidity}\n"
            f"🌧️ Yağış: {precipitation} mm\n"
            f"💨 Rüzgar: {wind} km/s\n"
            f"☁️ Durum: {description}"
        )

    except Exception as e:
        print(
            "HAVA DURUMU HATASI:",
            repr(e)
        )

        await update.message.reply_text(
            "❌ Hava durumu alınamadı."
        )


# =========================================================
# /OZETCIKAR
# =========================================================

async def ozetcikar(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not context.args:
        await update.message.reply_text(
            "📝 /ozetcikar\n\n"
            "Özetlemek istediğin metni "
            "komuttan sonra yaz.\n\n"
            "Örnek:\n"
            "/ozetcikar Bitcoin bugün yükseldi..."
        )
        return

    text = " ".join(
        context.args
    )

    if groq_client:

        try:
            response = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Sen Alfred'sin. "
                            "Türkçe konuş. "
                            "Verilen metni kısa, "
                            "net ve doğru şekilde özetle. "
                            "Gereksiz ayrıntıları çıkar."
                        ),
                    },
                    {
                        "role": "user",
                        "content": text,
                    },
                ],
                temperature=0.3,
                max_tokens=500,
            )

            summary = (
                response.choices[0]
                .message.content
                .strip()
            )

            await update.message.reply_text(
                "📝 Alfred Özeti\n\n"
                + summary
            )

            return

        except Exception as e:
            print(
                "AI ÖZETLEME HATASI:",
                repr(e)
            )

    words = text.split()

    if len(words) <= 40:
        summary = text
    else:
        summary = (
            " ".join(words[:40])
            + "..."
        )

    await update.message.reply_text(
        "📝 Özet\n\n"
        + summary
    )


# =========================================================
# /SOR
# =========================================================

async def sor(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not context.args:
        await update.message.reply_text(
            "🧠 /sor\n\n"
            "Bana bir soru yaz.\n\n"
            "Örnek:\n"
            "/sor Bitcoin neden yükseliyor?"
        )
        return

    if not groq_client:
        await update.message.reply_text(
            "❌ Alfred AI bağlantısı bulunamadı.\n\n"
            "Railway'de GROQ_API_KEY "
            "değişkenini kontrol et."
        )
        return

    question = " ".join(
        context.args
    )

    try:

        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sen Alfred'sin. "
                        "Kullanıcıyla Türkçe konuş. "
                        "Sakin, zeki, mantıklı, "
                        "dürüst ve doğrudan ol. "
                        "Gerektiğinde kullanıcıya "
                        "katılmadığını açıkça söyle. "
                        "Bilmediğin şeyi biliyormuş "
                        "gibi gösterme. "
                        "Cevaplarını gereksiz yere "
                        "uzatma ama soruyu yeterince "
                        "açıkla. "
                        "Finans ve kripto konularında "
                        "kesin kazanç garantisi verme."
                    ),
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
            temperature=0.5,
            max_tokens=800,
        )

        answer = (
            response.choices[0]
            .message.content
            .strip()
        )

        if not answer:
            await update.message.reply_text(
                "❌ Alfred şu anda cevap üretemedi."
            )
            return

        max_length = 4000

        if len(answer) <= max_length:

            await update.message.reply_text(
                "🦇 Alfred:\n\n"
                + answer
            )

        else:

            parts = [
                answer[i:i + max_length]
                for i in range(
                    0,
                    len(answer),
                    max_length
                )
            ]

            for index, part in enumerate(
                parts
            ):

                if index == 0:
                    await update.message.reply_text(
                        "🦇 Alfred:\n\n"
                        + part
                    )
                else:
                    await update.message.reply_text(
                        part
                    )

    except Exception as e:

        print(
            "GROQ HATASI:",
            repr(e)
        )

        error_text = str(e).lower()

        if (
            "rate" in error_text
            or "limit" in error_text
            or "429" in error_text
        ):
            message = (
                "⚠️ Alfred'in ücretsiz AI "
                "kullanım limitine ulaşıldı.\n\n"
                "Bir süre sonra tekrar deneyelim."
            )

        else:
            message = (
                "❌ Alfred AI şu anda "
                "cevap veremiyor.\n\n"
                "Railway Logs'u kontrol edelim."
            )

        await update.message.reply_text(
            message
        )


# =========================================================
# RADAR YARDIMCI FONKSİYONLARI
# =========================================================

def get_radar_news(
    feeds,
    limit=6,
):
    results = []
    seen = set()

    for feed_url, source_name in feeds:

        try:
            feed = feedparser.parse(
                feed_url
            )

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

                normalized = (
                    title.lower()
                    .replace(
                        " ",
                        ""
                    )
                )

                if (
                    link in seen
                    or normalized in seen
                ):
                    continue

                seen.add(link)
                seen.add(normalized)

                translated_title = (
                    translate_news_title(
                        title
                    )
                )

                results.append({
                    "title": translated_title,
                    "original_title": title,
                    "url": link,
                    "domain": source_name,
                })

                if len(results) >= limit:
                    return results

        except Exception as e:
            print(
                f"RADAR RSS HATASI ({source_name}):",
                repr(e)
            )

    return results


# =========================================================
# RADAR ANAHTAR KELİMELERİ
# =========================================================

def radar_priority(title):
    text = title.lower()

    critical_words = [
        "war",
        "attack",
        "invasion",
        "missile",
        "earthquake",
        "tsunami",
        "nuclear",
        "emergency",
        "crisis",
        "collapse",
        "default",
        "bank failure",
        "banking crisis",
        "faiz kararı",
        "deprem",
        "savaş",
        "saldırı",
        "işgal",
        "füze",
        "nükleer",
        "acil durum",
        "kriz",
        "çöküş",
        "iflas",
        "banka krizi",
    ]

    important_words = [
        "fed",
        "ecb",
        "central bank",
        "interest rate",
        "inflation",
        "recession",
        "oil",
        "gold",
        "tariff",
        "sanctions",
        "election",
        "government",
        "economy",
        "economic",
        "market",
        "enflasyon",
        "merkez bankası",
        "faiz",
        "resesyon",
        "petrol",
        "altın",
        "gümrük",
        "yaptırım",
        "seçim",
        "hükümet",
        "ekonomi",
        "ekonomik",
        "piyasa",
    ]

    for word in critical_words:
        if word in text:
            return 3

    for word in important_words:
        if word in text:
            return 2

    return 1


def radar_label(priority):
    if priority == 3:
        return "🔴 KRİTİK"

    if priority == 2:
        return "🟠 ÖNEMLİ"

    return "🟢 GÜNDEM"


# =========================================================
# RADAR RSS KANITI HAZIRLA
# =========================================================

def build_radar_evidence(
    world_news,
    turkey_news,
    economy_news,
):
    evidence = []

    for item in world_news:
        evidence.append({
            "category": "Dünya",
            **item
        })

    for item in turkey_news:
        evidence.append({
            "category": "Türkiye",
            **item
        })

    for item in economy_news:
        evidence.append({
            "category": "Ekonomi",
            **item
        })

    return evidence


# =========================================================
# AI RADAR
# =========================================================

def ai_radar_analysis(evidence):

    if not groq_client:
        return None

    evidence_text = ""

    for index, item in enumerate(
        evidence,
        1
    ):

        evidence_text += (
            f"\n[{index}] "
            f"Kategori: {item['category']}\n"
            f"Başlık: {item['title']}\n"
            f"Kaynak: {item['domain']}\n"
            f"URL: {item['url']}\n"
        )

    prompt = f"""
Sen Alfred'sin ve gelişmiş bir haber/risk radarısın.

Şu anda Dünya, Türkiye ve ekonomi alanındaki
en önemli gelişmeleri analiz ediyorsun.

KESİN KURALLAR:

1. KRİPTO PARA HABERLERİNİ ANALİZ ETME.
2. Bitcoin, Ethereum, altcoin, memecoin,
   kripto borsa ve token haberlerini RADARA ALMA.
3. Dünya, Türkiye ve EKONOMİ konularına odaklan.
4. Güncel gelişmeleri gerektiğinde web araması
   yaparak kontrol et.
5. Aynı olayın farklı kaynaklardaki tekrarlarını
   mümkün olduğunca tek olay altında birleştir.
6. Eski veya düşük etkili haberleri ele.
7. Gerçekten önemli olayları öne çıkar.
8. Tahmin ile doğrulanmış bilgiyi birbirine
   karıştırma.
9. Bilgi kesin değilse bunu açıkça belirt.
10. Yatırım tavsiyesi verme.

ÖNEM DERECELERİ:

🔴 KRİTİK:
Savaş, büyük saldırı, doğal afet, ciddi ekonomik
kriz, bankacılık krizi, devlet iflası, nükleer
tehdit veya dünya/Türkiye açısından olağanüstü
etkili gelişmeler.

🟠 ÖNEMLİ:
Merkez bankası kararları, faiz, enflasyon,
resesyon, enerji, petrol, altın, ticaret
politikaları, yaptırımlar, seçimler, hükümet
kararları ve önemli ekonomik gelişmeler.

🟢 GÜNDEM:
Önemli fakat acil veya büyük sistemik etkisi
olmayan gelişmeler.

ÇIKTI FORMATI:

📡 ALFRED AI RADAR

🔴/🟠/🟢 [ÖNEM]
🌍/🇹🇷/💰 [KATEGORİ]
[Haber başlığı]

🧠 Alfred:
[1-2 cümlelik kısa ve mantıklı değerlendirme]

⚠️ Etki:
[Düşük / Orta / Yüksek / Çok yüksek]

📡 Kaynak:
[Kaynak adı]

🔗 [URL]

Her haber arasında:

━━━━━━━━━━━━━━

En fazla 8 olay göster.

Sonuna:

🦇 Genel tablo:
[2-4 cümleyle günün genel görünümünü
Dünya + Türkiye + ekonomi açısından değerlendir.]

ekle.

ASLA kripto haberi gösterme.

RSS KAYNAKLARI:
{evidence_text}
"""

    try:

        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sen Alfred AI Radar'sın. "
                        "Türkçe konuş. "
                        "Güncel gelişmeleri dikkatli "
                        "ve tarafsız şekilde analiz et. "
                        "Kriptoyu radar dışında tut."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
            max_tokens=1800,
            tools=[
                {
                    "type": "browser_search"
                }
            ],
        )

        answer = (
            response.choices[0]
            .message.content
            .strip()
        )

        if not answer:
            return None

        return answer

    except Exception as e:

        print(
            "AI RADAR HATASI:",
            repr(e)
        )

        return None


# =========================================================
# KLASİK RADAR
# =========================================================

def classic_radar(
    all_news
):

    for item in all_news:
        item["priority"] = radar_priority(
            item["title"]
        )

    all_news.sort(
        key=lambda x: x["priority"],
        reverse=True,
    )

    final_news = []
    seen_titles = set()

    for item in all_news:

        normalized = (
            item["title"]
            .lower()
            .strip()
        )

        if normalized in seen_titles:
            continue

        seen_titles.add(
            normalized
        )

        final_news.append(
            item
        )

        if len(final_news) >= 10:
            break

    now = datetime.now(
        ZoneInfo(
            "Europe/Istanbul"
        )
    )

    text = (
        "📡 ALFRED RADAR\n\n"
        f"🕒 {now.strftime('%d.%m.%Y %H:%M')}\n\n"
        "Dünya, Türkiye ve ekonomi "
        "gelişmeleri tarandı.\n\n"
    )

    for index, item in enumerate(
        final_news,
        1
    ):

        priority_text = radar_label(
            item["priority"]
        )

        text += (
            f"{priority_text}\n"
            f"{item['category']}\n"
            f"{index}. {item['title']}\n"
            f"📡 {item['domain']}\n"
            f"🔗 {item['url']}\n\n"
        )

    text += (
        "━━━━━━━━━━━━━━\n"
        "🦇 Alfred değerlendirmesi:\n"
        "AI Radar şu anda devre dışı veya "
        "erişilemez olduğu için klasik radar "
        "sıralaması kullanıldı."
    )

    return text


# =========================================================
# TELEGRAM MESAJINI PARÇALA
# =========================================================

async def send_long_message(
    update,
    text,
):
    max_length = 4000

    if len(text) <= max_length:

        await update.message.reply_text(
            text
        )

        return

    parts = [
        text[i:i + max_length]
        for i in range(
            0,
            len(text),
            max_length
        )
    ]

    for part in parts:

        await update.message.reply_text(
            part
        )


# =========================================================
# /RADAR
# =========================================================

async def radar(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await update.message.reply_text(
        "📡 Alfred AI Radar çalışıyor...\n\n"
        "🌍 Dünya\n"
        "🇹🇷 Türkiye\n"
        "💰 Ekonomi\n"
        "🤖 AI analizi\n"
        "🌐 Güncel gelişme kontrolü\n\n"
        "Biraz bekleyin efendim..."
    )

    try:

        # -------------------------------------------------
        # RSS VERİLERİNİ TOPLA
        # -------------------------------------------------

        world_news = get_radar_news(
            RADAR_WORLD_FEEDS,
            limit=5,
        )

        turkey_news = get_radar_news(
            RADAR_TURKEY_FEEDS,
            limit=5,
        )

        economy_news = get_radar_news(
            RADAR_ECONOMY_FEEDS,
            limit=5,
        )

        all_news = []

        for item in world_news:
            item["category"] = "🌍 Dünya"
            all_news.append(item)

        for item in turkey_news:
            item["category"] = "🇹🇷 Türkiye"
            all_news.append(item)

        for item in economy_news:
            item["category"] = "💰 Ekonomi"
            all_news.append(item)

        if not all_news:

            await update.message.reply_text(
                "📡 Alfred Radar\n\n"
                "Şu anda radar verisi alınamadı."
            )

            return

        # -------------------------------------------------
        # AI RADAR
        # -------------------------------------------------

        evidence = build_radar_evidence(
            world_news,
            turkey_news,
            economy_news,
        )

        ai_result = ai_radar_analysis(
            evidence
        )

        # -------------------------------------------------
        # AI BAŞARILIYSA
        # -------------------------------------------------

        if ai_result:

            now = datetime.now(
                ZoneInfo(
                    "Europe/Istanbul"
                )
            )

            final_text = (
                f"{ai_result}\n\n"
                "━━━━━━━━━━━━━━\n"
                f"🕒 Radar zamanı: "
                f"{now.strftime('%d.%m.%Y %H:%M')}\n"
                "🦇 Alfred AI Radar aktif\n"
                "🚫 Kripto radar dışında tutulmuştur."
            )

            await send_long_message(
                update,
                final_text
            )

            return

        # -------------------------------------------------
        # AI ÇALIŞMAZSA KLASİK RADAR
        # -------------------------------------------------

        classic_text = classic_radar(
            all_news
        )

        await send_long_message(
            update,
            classic_text
        )

    except Exception as e:

        print(
            "RADAR HATASI:",
            repr(e)
        )

        await update.message.reply_text(
            "❌ Alfred Radar çalışırken "
            "bir hata oluştu."
        )


# =========================================================
# /YARDIM
# =========================================================

async def yardim(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = """🦇 ALFRED 2.0 — YARDIM

Merhaba. Ben Alfred. Aşağıdaki komutlarla size yardımcı olabilirim.

━━━━━━━━━━━━━━
📈 PİYASA
━━━━━━━━━━━━━━

/fiyatbtc
₿ Bitcoin'in güncel fiyatını ve 24 saatlik değişimini gösterir.

/fiyatsol
◎ Solana'nın güncel fiyatını ve 24 saatlik değişimini gösterir.

/tara
🔎 Binance piyasasını tarar ve dikkat çeken yükseliş/momentum hareketlerini listeler.

━━━━━━━━━━━━━━
📰 HABERLER
━━━━━━━━━━━━━━

/haber
🌍 Dünyadan önemli güncel haberleri getirir.

/haberturk
🇹🇷 Türkiye'den önemli güncel haberleri getirir.

/haberkripto
₿ Kripto para dünyasındaki güncel gelişmeleri getirir.

━━━━━━━━━━━━━━
🌍 ARAÇLAR
━━━━━━━━━━━━━━

/havadurumu
🌦️ Güncel hava durumunu gösterir.

/cevir
🌐 Yazdığınız metni otomatik olarak algılar ve Türkçeye çevirir.

Örnek:
/cevir Hello, how are you?

/ozetcikar
📝 Uzun bir metni analiz ederek daha kısa ve anlaşılır hâle getirir.

Örnek:
/ozetcikar [metin]

━━━━━━━━━━━━━━
🧠 ALFRED
━━━━━━━━━━━━━━

/sor
🤖 Alfred'e istediğiniz konuda soru sorabilirsiniz.

Örnek:
/sor Yapay zeka nasıl çalışır?

/radar
📡 Dünyadaki önemli gelişmeleri ve ekonomik olayları tarar.

━━━━━━━━━━━━━━
⚙️ SİSTEM
━━━━━━━━━━━━━━

/start
🦇 Alfred'i başlatır ve ana menüyü gösterir.

/yardim
📖 Bu yardım menüsünü gösterir.

━━━━━━━━━━━━━━

🦇 Alfred hazır. Buyurun, sizi dinliyorum.
"""

    await update.message.reply_text(
        text
    )


# =========================================================
# /START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "🦇 Alfred hazır. Buyurun, sizi dinliyorum.\n\n"
        "Komutları görmek için:\n"
        "/yardim"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN bulunamadı."
        )

    if not GROQ_API_KEY:
        print(
            "⚠️ GROQ_API_KEY bulunamadı. "
            "/sor ve AI Radar çalışamaz."
        )

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    # Sistem
    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "yardim",
            yardim
        )
    )

    # Piyasa
    application.add_handler(
        CommandHandler(
            "fiyatbtc",
            fiyatbtc
        )
    )

    application.add_handler(
        CommandHandler(
            "fiyatsol",
            fiyatsol
        )
    )

    application.add_handler(
        CommandHandler(
            "tara",
            tara
        )
    )

    # Haberler
    application.add_handler(
        CommandHandler(
            "haber",
            haber
        )
    )

    application.add_handler(
        CommandHandler(
            "haberturk",
            haberturk
        )
    )

    application.add_handler(
        CommandHandler(
            "haberkripto",
            haberkripto
        )
    )

    # Araçlar
    application.add_handler(
        CommandHandler(
            "havadurumu",
            havadurumu
        )
    )

    application.add_handler(
        CommandHandler(
            "cevir",
            cevir
        )
    )

    application.add_handler(
        CommandHandler(
            "ozetcikar",
            ozetcikar
        )
    )

    # Alfred
    application.add_handler(
        CommandHandler(
            "sor",
            sor
        )
    )

    application.add_handler(
        CommandHandler(
            "radar",
            radar
        )
    )

    print(
        "🦇 Alfred 2.0 başlatılıyor..."
    )

    application.run_polling()


if __name__ == "__main__":
    main()
