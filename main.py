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
import json

PLA_ALFA_URL = (
    "https://services7.arcgis.com/"
    "ZCqVt1fRXwwK6GF4/arcgis/rest/services/"
    "Pla_Alfa_Municipal_Avui_FL_alternatiu_VW/"
    "FeatureServer/0/query"
)

USUARIOS_FILE = "usuarios.json"


def cargar_usuarios():
    try:
        with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def guardar_usuarios(datos):
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


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

    r = requests.get(
        PLA_ALFA_URL,
        params=params,
        timeout=15
    )

    data = r.json()

    features = data.get("features", [])

    if not features:
        return None

    attrs = features[0]["attributes"]

    return {
        "municipio": attrs["NOMMUNI"],
        "nivel": attrs["PERIL_M"]
    }


def consultar_pla_alfa_coordenadas(lat, lon):

    params = {
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "NOMMUNI,PERIL_M",
        "returnGeometry": "false",
        "f": "json"
    }

    r = requests.get(
        PLA_ALFA_URL,
        params=params,
        timeout=15
    )

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
        "Comandos disponibles:\n\n"
        "/olivella - Estado de Olivella\n"
        "/estado - Estado de Olivella y tu ubicación guardada\n\n"
        "También puedes enviarme tu ubicación."
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


async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):

    usuarios = cargar_usuarios()

    user_id = str(update.effective_user.id)

    mensaje = ""

    olivella = consultar_pla_alfa("Olivella")

    if olivella:

        mensaje += (
            f"📍 Olivella\n"
            f"🔥 Pla Alfa: Nivel {olivella['nivel']}\n"
            f"{texto_nivel(olivella['nivel'])}\n\n"
        )

    if user_id in usuarios:

        municipio = usuarios[user_id]["municipio"]

        actual = consultar_pla_alfa(municipio)

        if actual:

            mensaje += (
                f"📍 Tu ubicación guardada\n"
                f"{actual['municipio']}\n"
                f"🔥 Pla Alfa: Nivel {actual['nivel']}\n"
                f"{texto_nivel(actual['nivel'])}"
            )

    else:

        mensaje += (
            "📍 Aún no has enviado una ubicación.\n"
            "Envíamela para guardarla."
        )

    await update.message.reply_text(mensaje)


async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):

    lat = update.message.location.latitude
    lon = update.message.location.longitude

    try:

        resultado = consultar_pla_alfa_coordenadas(lat, lon)

        if resultado is None:

            await update.message.reply_text(
                "No se ha encontrado información Pla Alfa para esta ubicación."
            )
            return

        usuarios = cargar_usuarios()

        usuarios[str(update.effective_user.id)] = {
            "municipio": resultado["municipio"]
        }

        guardar_usuarios(usuarios)

        await update.message.reply_text(
            f"📍 Municipio: {resultado['municipio']}\n\n"
            f"🔥 Pla Alfa: Nivel {resultado['nivel']}\n"
            f"{texto_nivel(resultado['nivel'])}\n\n"
            f"✅ Ubicación guardada."
        )

    except Exception as e:

        await update.message.reply_text(
            f"Error: {str(e)}"
        )


def main():

    token = os.getenv("BOT_TOKEN")

    if not token:
        raise ValueError("BOT_TOKEN no configurado")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("olivella", olivella))
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(MessageHandler(filters.LOCATION, location))

    print("Bot iniciado...")

    app.run_polling()


if __name__ == "__main__":
    main()
