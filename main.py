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

PLA_ALFA_URL = (
    "https://services7.arcgis.com/"
    "ZCqVt1fRXwwK6GF4/arcgis/rest/services/"
    "Pla_Alfa_Municipal_Avui_FL_alternatiu_VW/"
    "FeatureServer/0/query"
)


def texto_nivel(nivel):
    textos = {
        0: "🟢 Perill baix d'incendi",
        1: "🟡 Perill moderat d'incendi",
        2: "🟠 Perill alt d'incendi",
        3: "🔴 Perill molt alt d'incendi",
        4: "🚨 Perill extrem d'incendi",
    }
    return textos.get(nivel, "Nivell desconegut")


def consultar_pla_alfa(municipio):
    params = {
        "where": f"NOMMUNI='{municipio}'",
        "outFields": "NOMMUNI,PERIL_M",
        "f": "json"
    }

    r = requests.get(PLA_ALFA_URL, params=params, timeout=15)
    data = r.json()

    features = data.get("features", [])

    if not features:
        return None

    attrs = features[0]["attributes"]

    return {
        "municipio": attrs["NOMMUNI"],
        "nivel": attrs["PERIL_M"]
    }


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 Pla Alfa Bot\n\n"
        "Comandos disponibles:\n"
        "/olivella\n\n"
        "O envíame tu ubicación."
    )


async def olivella(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        resultado = consultar_pla_alfa("Olivella")

        if resultado is None:
            await update.message.reply_text(
                "No se ha encontrado información de Olivella."
            )
            return

        await update.message.reply_text(
            f"📍 {resultado['municipio']}\n\n"
            f"🔥 Pla Alfa: Nivel {resultado['nivel']}\n"
            f"{texto_nivel(resultado['nivel'])}"
        )

    except Exception as e:
        await update.message.reply_text(
            f"Error: {str(e)}"
        )


async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lat = update.message.location.latitude
    lon = update.message.location.longitude

    try:
        headers = {
            "User-Agent": "PlaAlfaBot/1.0"
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
        )

        if not municipio:
            await update.message.reply_text(
                "No se ha podido determinar el municipio."
            )
            return

        resultado = consultar_pla_alfa(municipio)

        if resultado is None:
            await update.message.reply_text(
                f"📍 Municipio: {municipio}\n\n"
                "No encontrado en Pla Alfa."
            )
            return

        await update.message.reply_text(
            f"📍 Municipio: {resultado['municipio']}\n\n"
            f"🔥 Pla Alfa: Nivel {resultado['nivel']}\n"
            f"{texto_nivel(resultado['nivel'])}"
        )

    except Exception as e:
        await update.message.reply_text(
            f"Error: {str(e)}"
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
