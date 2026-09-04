import os
import requests

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

BINANCE_URL = "https://data-api.binance.vision/api/v3/ticker/24hr"


def get_binance_price(symbol):
    try:
        response = requests.get(
            BINANCE_URL,
            params={"symbol": symbol},
            timeout=10,
            headers={"User-Agent": "Alfred2.0"}
        )

        print("Binance HTTP:", response.status_code)
        print("Binance cevap:", response.text)

        response.raise_for_status()

        data = response.json()

        # Binance hata döndürürse
        if isinstance(data, dict) and "code" in data:
            print("Binance API hatası:", data)
            return None

        # Beklenen veri yoksa
        if not isinstance(data, dict) or "lastPrice" not in data:
            print("Beklenmeyen Binance cevabı:", data)
            return None

        price = float(data["lastPrice"])
        change = float(data.get("priceChangePercent", 0))

        return price, change

    except Exception as e:
        print("Binance fiyat hatası:", repr(e))
        return None


# =========================
# SİSTEM
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
# PİYASA
# =========================

async def fiyatbtc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_binance_price("BTCUSDT")

    if result is None:
        await update.message.reply_text(
            "⚠️ BTC fiyatı alınamadı.\n"
            "Binance bağlantısı kontrol ediliyor."
        )
        return

    price, change = result

    await update.message.reply_text(
        f"₿ BTC / USDT\n\n"
        f"💰 Fiyat: ${price:,.2f}\n"
        f"📊 24s: {change:+.2f}%\n\n"
        f"🦇 Alfred 2.0"
    )


async def fiyatsol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_binance_price("SOLUSDT")

    if result is None:
        await update.message.reply_text(
            "⚠️ SOL fiyatı alınamadı.\n"
            "Binance bağlantısı kontrol ediliyor."
        )
        return

    price, change = result

    await update.message.reply_text(
        f"◎ SOL / USDT\n\n"
        f"💰 Fiyat: ${price:,.2f}\n"
        f"📊 24s: {change:+.2f}%\n\n"
        f"🦇 Alfred 2.0"
    )


async def tara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔎 Piyasa taraması başlatılıyor...\n\n"
        "🦇 Alfred 2.0 tarama sistemi hazırlanıyor."
    )


# =========================
# HABERLER
# =========================

async def haber(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📰 Dünya haberleri modülü hazırlanıyor."
    )


async def haberturk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🇹🇷 Türkiye haberleri modülü hazırlanıyor."
    )


async def haberkripto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "₿ Kripto haberleri modülü hazırlanıyor."
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
        raise RuntimeError("TELEGRAM_BOT_TOKEN bulunamadı.")

    app = Application.builder().token(TOKEN).build()

    # Sistem
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("yardim", yardim))

    # Piyasa
    app.add_handler(CommandHandler("fiyatbtc", fiyatbtc))
    app.add_handler(CommandHandler("fiyatsol", fiyatsol))
    app.add_handler(CommandHandler("tara", tara))

    # Haberler
    app.add_handler(CommandHandler("haber", haber))
    app.add_handler(CommandHandler("haberturk", haberturk))
    app.add_handler(CommandHandler("haberkripto", haberkripto))

    # Araçlar
    app.add_handler(CommandHandler("havadurumu", havadurumu))
    app.add_handler(CommandHandler("cevir", cevir))
    app.add_handler(CommandHandler("ozetcikar", ozetcikar))

    # Alfred
    app.add_handler(CommandHandler("sor", sor))
    app.add_handler(CommandHandler("radar", radar))

    print("🦇 Alfred 2.0 aktif.")
    app.run_polling()


if __name__ == "__main__":
    main()
