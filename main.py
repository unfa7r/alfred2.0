import os
import requests

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

BINANCE_URL = "https://data-api.binance.vision/api/v3/ticker/24hr"
GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


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
# HABERLER
# =========================

def get_news(query, limit=5):
    try:
        params = {
            "query": query,
            "mode": "artlist",
            "maxrecords": limit,
            "format": "json",
            "sort": "datedesc"
        }

        r = requests.get(
            GDELT_URL,
            params=params,
            timeout=20
        )

        r.raise_for_status()

        data = r.json()
        articles = data.get("articles", [])

        results = []

        for article in articles:
            title = article.get("title", "")
            url = article.get("url", "")
            domain = article.get("domain", "")

            if title and url:
                results.append({
                    "title": title,
                    "url": url,
                    "domain": domain
                })

        return results[:limit]

    except Exception as e:
        print("HABER HATASI:", repr(e))
        return []


def news_text(header, news):
    if not news:
        return (
            f"{header}\n\n"
            "⚠️ Şu anda güvenilir haber bulunamadı."
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
        "🌍 Güvenilir dünya haberleri taranıyor..."
    )

    query = (
        "(world OR global OR international) "
        "(domain:reuters.com OR "
        "domain:apnews.com OR "
        "domain:bbc.com OR "
        "domain:dw.com)"
    )

    news = get_news(query, 5)

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
        "🇹🇷 Güvenilir Türkiye haberleri taranıyor..."
    )

    query = (
        "(Turkey OR Türkiye) "
        "(domain:aa.com.tr OR "
        "domain:reuters.com OR "
        "domain:bbc.com OR "
        "domain:dw.com)"
    )

    news = get_news(query, 5)

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
        "₿ Güvenilir kripto haberleri taranıyor..."
    )

    query = (
        "(Bitcoin OR Ethereum OR crypto OR cryptocurrency OR blockchain) "
        "(domain:reuters.com OR "
        "domain:coindesk.com OR "
        "domain:theblock.co OR "
        "domain:decrypt.co)"
    )

    news = get_news(query, 5)

    await update.message.reply_text(
        news_text(
            "₿ ALFRED — KRİPTO HABERLERİ",
            news
        )
    )


# =========================
# ARAÇLAR
# =========================

async def havadurumu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌤️ Hava durumu modülü hazırlanıyor."
    )


async def cevir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌍 Çeviri modülü hazırlanıyor."
    )


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
