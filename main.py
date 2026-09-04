import os
import requests

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

BINANCE_URL = "https://data-api.binance.vision/api/v3/ticker/24hr"


# =========================
# BINANCE
# =========================

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

        if isinstance(data, dict) and "code" in data:
            print("Binance API hatası:", data)
            return None

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
# BTC
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


# =========================
# SOL
# =========================

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


# =========================
# TARA
# =========================

async def tara(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🔎 Binance piyasası taranıyor...\n"
        "🦇 Alfred analiz yapıyor..."
    )

    try:
        response = requests.get(
            BINANCE_URL,
            timeout=20,
            headers={"User-Agent": "Alfred2.0"}
        )

        print("TARA HTTP:", response.status_code)
        print("TARA cevabı alındı.")

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, list):
            print("Beklenmeyen tara cevabı:", data)

            await update.message.reply_text(
                "⚠️ Binance tarama verisi alınamadı."
            )
            return

        candidates = []

        for coin in data:

            symbol = coin.get("symbol", "")

            # Sadece USDT pariteleri
            if not symbol.endswith("USDT"):
                continue

            # Stablecoinleri çıkar
            excluded = [
                "USDCUSDT",
                "FDUSDUSDT",
                "TUSDUSDT",
                "USDTUSDT",
                "DAIUSDT",
            ]

            if symbol in excluded:
                continue

            try:
                change = float(
                    coin.get("priceChangePercent", 0)
                )

                volume = float(
                    coin.get("quoteVolume", 0)
                )

                price = float(
                    coin.get("lastPrice", 0)
                )

            except (TypeError, ValueError):
                continue

            # Yeterli hacim
            if volume < 1_000_000:
                continue

            # Pozitif hareket
            if change <= 0:
                continue

            candidates.append({
                "symbol": symbol.replace("USDT", ""),
                "change": change,
                "volume": volume,
                "price": price
            })

        # En çok yükselenleri sırala
        candidates.sort(
            key=lambda x: x["change"],
            reverse=True
        )

        top = candidates[:5]

        if not top:
            await update.message.reply_text(
                "⚠️ Şu anda uygun pozitif sinyal bulunamadı."
            )
            return

        message = (
            "🦇 ALFRED 2.0 RADAR\n"
            "━━━━━━━━━━━━━━\n\n"
            "📈 En güçlü hareketler:\n\n"
        )

        for i, coin in enumerate(top, 1):

            message += (
                f"{i}. 🔥 {coin['symbol']}\n"
                f"   📈 24s: +{coin['change']:.2f}%\n"
                f"   💰 Hacim: ${coin['volume']:,.0f}\n"
                f"   💵 Fiyat: ${coin['price']:.8f}\n\n"
            )

        message += (
            "━━━━━━━━━━━━━━\n"
            "⚠️ Bu liste AL/SAT garantisi değildir.\n"
            "📡 Alfred piyasa momentumunu tarıyor."
        )

        await update.message.reply_text(message)

    except Exception as e:

        print("TARA HATASI:", repr(e))

        await update.message.reply_text(
            "⚠️ P
