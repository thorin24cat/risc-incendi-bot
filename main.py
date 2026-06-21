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

    await update.message.reply_text(
        f"Ubicación recibida:\nLatitud: {lat}\nLongitud: {lon}"
    )

token = os.getenv("BOT_TOKEN")

app = Application.builder().token(token).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.LOCATION, location))

app.run_polling()
