from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import requests
import os


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hola. Envíame tu ubicación o escribe /olivella"
    )


async def olivella(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📍 Municipio: Olivella\n\n🔥 Consulta Pla Alfa pendiente de implementar"
    )


async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lat = update.message.location.latitude
    lon = update.message.location.longitude

    try:
        headers = {
            "User-Agent": "RiscIncendiBot/1.0"
        }

        url = (
            f"https://nominatim.openstreetmap.org/reverse"
            f"?lat={lat}&lon={lon}&format=jsonv2"
        )

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        data = response.json()

        address = data.get("address", {})

        municipio = (
            address.get("municipality")
            or address.get("town")
            or address.get("village")
            or address.get("city")
            or "Desconocido"
        )

        await update.message.reply_text(
    f"📍 Municipio: {municipio}\n"
    f"🌍 Latitud: {lat}\n"
    f"🌍 Longitud: {lon}"
)

    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: {str(e)}"
        )


def main():
    token = os.getenv("BOT_TOKEN")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("olivella", olivella))
    app.add_handler(MessageHandler(filters.LOCATION, location))

    app.run_polling()


if __name__ == "__main__":
    main()
