from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters
import os

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hola. Envíame tu ubicación y te indicaré el nivel de riesgo."
    )

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lat = update.message.location.latitude
    lon = update.message.location.longitude

    import requests

    headers = {
        "User-Agent": "RiscIncendiBot/1.0"
    }

    url = (
        f"https://nominatim.openstreetmap.org/reverse"
        f"?lat={lat}&lon={lon}&format=jsonv2"
    )

    try:
        response = requests.get(url, headers=headers, timeout=10)
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
            f"📍 Municipio: {municipio}"
        )

    except Exception as e:
        await update.message.reply_text(
            f"Error obteniendo municipio: {e}"
        )

token = os.getenv("BOT_TOKEN")

app = Application.builder().token(token).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.LOCATION, location))

app.run_polling()
