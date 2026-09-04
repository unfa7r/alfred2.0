import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🦇 Alfred 2.0 çevrimiçi.\n\n"
        "Size nasıl yardımcı olabilirim?"
    )


async def yardim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🦇 ALFRED 2.0\n\n"
        "/start - Alfred'i başlat\n"
        "/fiyat BTC - Bitcoin fiyatı\n"
        "/fiyat SOL - Solana fiyatı\n"
        "/haber - Dünya haberleri\n"
        "/haber turk - Türkiye haberleri\n"
        "/haber kripto - Kripto haberleri\n"
        "/tara - Yükselen coinleri tara\n"
        "/havadurumu - Türkiye hava durumu\n"
        "/cevir - Türkçeye çevir\n"
        "/radar - Global olağandışı gelişmeler\n"
        "/ozetcikar - Metin özetle\n"
        "/sor - Alfred'e soru sor\n"
        "/yardim - Komutları göster"
    )


def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN bulunamadı.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("yardim", yardim))

    print("Alfred 2.0 çalışıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()
