import json
import os
import requests

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

ARCGIS_URL = (
    "https://services7.arcgis.com/"
    "ZCqVt1fRXwwK6GF4/arcgis/rest/services/"
    "Pla_Alfa_Municipal_Avui_FL_alternatiu_VW/"
    "FeatureServer/0/query"
)

USUARIOS_FILE = "usuarios.json"


# --------------------------------------------------
# USUARIOS
# --------------------------------------------------

def cargar_usuarios():
    try:
        with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def guardar_usuarios(datos):
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


# --------------------------------------------------
# PLAN ALFA
# --------------------------------------------------

def obtener_nivel_por_municipio(municipio):

    params = {
        "where": f"UPPER(NOMMUNI)=UPPER('{municipio}')",
        "outFields": "NOMMUNI,PERIL_M",
        "returnGeometry": "false",
        "f": "json",
    }

    try:
        r = requests.get(ARCGIS_URL, params=params, timeout=10)
        data = r.json()

        if data.get("features"):
            attr = data["features"][0]["attributes"]

            return {
                "municipio": attr["NOMMUNI"],
                "nivel": attr["PERIL_M"],
            }

    except Exception as e:
        print(e)

    return None


def obtener_nivel(lat, lon):

    params = {
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "NOMMUNI,PERIL_M",
        "returnGeometry": "false",
        "f": "json",
    }

    try:
        r = requests.get(ARCGIS_URL, params=params, timeout=10)
        data = r.json()

        if data.get("features"):
            attr = data["features"][0]["attributes"]

            return {
                "municipio": attr["NOMMUNI"],
                "nivel": attr["PERIL_M"],
            }

    except Exception as e:
        print(e)

    return None


# --------------------------------------------------
# COMANDOS
# --------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    teclado = [[KeyboardButton("📍 Compartir ubicación", request_location=True)]]

    await update.message.reply_text(
        "Hola.\n\n"
        "Compárteme tu ubicación para guardar tu municipio.",
        reply_markup=ReplyKeyboardMarkup(
            teclado,
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )


async def miestado(update: Update, context: ContextTypes.DEFAULT_TYPE):

    usuarios = cargar_usuarios()

    user_id = str(update.effective_user.id)

    if user_id not in usuarios:

        await update.message.reply_text(
            "No tienes municipio guardado.\n\nUsa /start"
        )
        return

    municipio = usuarios[user_id]["municipio"]

    info = obtener_nivel_por_municipio(municipio)

    if not info:
        await update.message.reply_text(
            f"📍 Municipio guardado: {municipio}\n"
            "⚠️ No se ha podido consultar el Pla Alfa."
        )
        return

    await update.message.reply_text(
        f"📍 Municipio: {info['municipio']}\n"
        f"🔥 Nivel Pla Alfa: {info['nivel']}"
    )


async def cambiar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    usuarios = cargar_usuarios()

    user_id = str(update.effective_user.id)

    if user_id in usuarios:
        del usuarios[user_id]
        guardar_usuarios(usuarios)

    teclado = [[KeyboardButton("📍 Compartir ubicación", request_location=True)]]

    await update.message.reply_text(
        "Envíame tu nueva ubicación.",
        reply_markup=ReplyKeyboardMarkup(
            teclado,
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )


# --------------------------------------------------
# UBICACIÓN
# --------------------------------------------------

async def recibir_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):

    lat = update.message.location.latitude
    lon = update.message.location.longitude

    info = obtener_nivel(lat, lon)

    if not info:
        await update.message.reply_text(
            "No he podido obtener el municipio."
        )
        return

    usuarios = cargar_usuarios()

    usuarios[str(update.effective_user.id)] = {
        "municipio": info["municipio"]
    }

    guardar_usuarios(usuarios)

    await update.message.reply_text(
        f"✅ Municipio guardado: {info['municipio']}\n"
        f"🔥 Nivel Pla Alfa actual: {info['nivel']}"
    )


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("miestado", miestado))
    app.add_handler(CommandHandler("cambiar", cambiar))

    app.add_handler(
        MessageHandler(
            filters.LOCATION,
            recibir_ubicacion,
        )
    )

    print("Bot iniciado")

    app.run_polling()


if __name__ == "__main__":
    main()
