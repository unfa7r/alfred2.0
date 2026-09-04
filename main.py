import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def get_crypto_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        return {
            "price": float(data["lastPrice"]),
            "change": float(data["priceChangePercent"])
        }

    except Exception as e:
        print(f"Fiyat hatası: {e}")
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🦇 Alfred 2.0 çevrimiçi.\n\n"
        "Komutları görmek için /yardim yaz."
    )


async def fiyatbtc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🦇 BTC fiyatı kontrol ediliyor...")

    data = get_crypto_price("BTCUSDT")

    if not data:
        await update.message.reply_text("⚠️ BTC fiyatı alınamadı.")
        return

    change_emoji = "📈" if data["change"] >= 0 else "📉"

    message = (
        "🦇 ALFRED MARKET\n\n"
        "₿ BITCOIN (BTC)\n\n"
        f"💰 Fiyat: ${data['price']:,.2f}\n"
        f"{change_emoji} 24s: {data['change']:+.2f}%"
    )

    await update.message.reply_text(message)


async def fiyatsol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🦇 SOL fiyatı kontrol ediliyor...")

    data = get_crypto_price("SOLUSDT")

    if not data:
        await update.message.reply_text("⚠️ SOL fiyatı alınamadı.")
        return

    change_emoji = "📈" if data["change"] >= 0 else "📉"

    message = (
        "🦇 ALFRED MARKET\n\n"
        "◎ SOLANA (SOL)\n\n"
        f"💰 Fiyat: ${data['price']:,.2f}\n"
        f"{change_emoji} 24s: {data['change']:+.2f}%"
    )

    await update.message.reply_text(message)


async def yardim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🦇 ALFRED 2.0 KOMUTLARI\n\n"
        "📈 PİYASA\n"
        "/fiyatbtc - Bitcoin fiyatı\n"
        "/fiyatsol - Solana fiyatı\n"
        "/tara - Yükselen coinleri tara\n\n"
        "📰 HABERLER\n"
        "/haber - Dünya haberleri\n"
        "/haberturk - Türkiye haberleri\n"
        "/haberkripto - Kripto haberleri\n\n"
        "🌍 ARAÇLAR\n"
        "/havadurumu - Türkiye hava durumu\n"
        "/cevir - Metni Türkçeye çevir\n"
        "/ozetcikar - Metni özetle\n\n"
        "🧠 ALFRED\n"
        "/sor - Alfred'e soru sor\n"
        "/radar - Global olağandışı gelişmeler\n\n"
        "⚙️ SİSTEM\n"
        "/start - Alfred'i başlat\n"
        "/yardim - Komutları göster"
    )


def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN bulunamadı.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("fiyatbtc", fiyatbtc))
    app.add_handler(CommandHandler("fiyatsol", fiyatsol))
    app.add_handler(CommandHandler("yardim", yardim))

    print("🦇 Alfred 2.0 çalışıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()
