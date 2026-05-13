from flask import Flask, request, jsonify
import requests
import json
import time
import os
import random

app = Flask(__name__)

CACHE = {}
CACHE_DURATA_SECONDI = 1800  # 30 minuti

PAROLACCE = [
    "cacca", "parolaccia", "volgarita", "insulto", "stupido", "idiota",
    "merda", "vaffanculo", "cazzo", "fottiti", "puttana", "deficiente",
    "imbecille", "bastardo", "cretino", "stronzo", "culo", "troia",
    "scemo", "pirla", "ignorante", "fanculo", "gomblotto",
    "frocio", "droga", "drogato", "minchione", "minchia",
    "belin", "pisello", "pippa", "marijuana", "gaggio",
    "gaggiu", "cagare", "cazzata", "coglione", "palle",
    "pezzente", "puzzone", "pompino"
]

RISPOSTE_GAGGIU = [
    "E bah, o gaggiu!",
    "Non sono mica il tuo gatto!",
    "Ajo, chiedimi il meteo 😄",
    "Io provo ad aiutarti eh 😅",
    "Facciamo i seri e guardiamo il meteo!"
]

LOCALITA_NON_SARDE = [
    "roma", "milano", "napoli", "torino", "palermo",
    "genova", "bologna", "firenze", "venezia",
    "parigi", "londra", "berlino", "madrid"
]


@app.route("/")
def home():
    return "Chiara API attiva"


def nome_vento_da_gradi(gradi):
    if gradi >= 337.5 or gradi < 22.5:
        return "Tramontana"
    elif gradi < 67.5:
        return "Grecale"
    elif gradi < 112.5:
        return "Levante"
    elif gradi < 157.5:
        return "Scirocco"
    elif gradi < 202.5:
        return "Ostro"
    elif gradi < 247.5:
        return "Libeccio"
    elif gradi < 292.5:
        return "Ponente"
    else:
        return "Maestrale"


def adatta_vento_sardegna(nome_vento, gradi):
    if nome_vento == "Ponente" and gradi > 280:
        return "Ponente-maestrale"
    if nome_vento == "Maestrale":
        return "Maestrale"
    return nome_vento


def crea_consiglio(temperatura, vento, raffiche, pioggia, nuvole):
    if raffiche >= 70:
        return " ⚠️ Attenzione al vento forte."
    elif pioggia >= 10:
        return " ☔ Possibili rovesci intensi."
    elif temperatura >= 38:
        return " 🥵 Caldo intenso, meglio evitare le ore centrali."
    elif temperatura <= 0:
        return " ❄️ Temperature molto basse."
    elif vento <= 15 and pioggia == 0:
        return " 🌤️ Giornata abbastanza tranquilla."
    elif nuvole > 80:
        return " ☁️ Meglio tenere d'occhio il cielo."
    return ""


@app.route("/chiara")
def chiara():
    nome_cercato = request.args.get("localita", "Cagliari")
    testo_input = nome_cercato.lower().strip()

    # 🔴 Parolacce / input provocatori
    for parola in PAROLACCE:
        if parola in testo_input:
            return jsonify({
                "descrizione": random.choice(RISPOSTE_GAGGIU),
                "tipo": "gaggiu"
            })

    # 🌍 Località fuori Sardegna
    for luogo in LOCALITA_NON_SARDE:
        if luogo in testo_input:
            return jsonify({
                "descrizione": "Eh, lì non ci sono ancora arrivata 😅",
                "tipo": "fuori_sardegna"
            })

    try:
        giorno = int(request.args.get("giorno", "0"))
    except ValueError:
        giorno = 0

    if giorno < 0 or giorno > 3:
        giorno = 0

    chiave_cache = f"{testo_input}_{giorno}"
    adesso = time.time()

    if chiave_cache in CACHE:
        dati_cache = CACHE[chiave_cache]
        if adesso - dati_cache["timestamp"] < CACHE_DURATA_SECONDI:
            risposta_cache = dati_cache["risposta"].copy()
            risposta_cache["cache"] = "usata"
            return jsonify(risposta_cache)

    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return jsonify({
            "descrizione": "Chiara non è configurata correttamente.",
            "errore": "WEATHER_API_KEY mancante"
        }), 500

    with open("localita_sardegna.json", "r", encoding="utf-8") as file:
        localita_sardegna = json.load(file)

    localita_trovata = None

    for localita in localita_sardegna:
        nome = localita["nome"].lower()
        id_localita = localita["id"].lower()

        if testo_input in nome or testo_input in id_localita:
            localita_trovata = localita
            break

    if localita_trovata is None:
        return jsonify({
            "descrizione": "Sei sicuro di aver scritto bene?",
            "tipo": "localita_non_trovata"
        }), 404

    nome_localita = localita_trovata["nome"]
    lat = localita_trovata["lat"]
    lon = localita_trovata["lng"]

    if giorno == 0:
        url = (
            "https://api.weatherapi.com/v1/current.json"
            f"?key={api_key}"
            f"&q={lat},{lon}"
            "&lang=it"
        )
    else:
        url = (
            "https://api.weatherapi.com/v1/forecast.json"
            f"?key={api_key}"
            f"&q={lat},{lon}"
            "&days=4"
            "&lang=it"
        )

    risposta = requests.get(url, timeout=10)
    dati = risposta.json()

    if giorno == 0:
        if "current" not in dati:
            return jsonify({
                "descrizione": "Non riesco a recuperare i dati meteo in questo momento.",
                "debug": dati
            }), 502

        meteo = dati["current"]

        temperatura = meteo["temp_c"]
        vento = meteo["wind_kph"]
        raffiche = meteo.get("gust_kph", vento)
        direzione_vento = meteo["wind_degree"]
        pioggia = meteo["precip_mm"]
        nuvole = meteo["cloud"]
        condizione = meteo["condition"]["text"]
        nome_giorno = "adesso"

    else:
        if "forecast" not in dati:
            return jsonify({
                "descrizione": "Non riesco a recuperare la previsione in questo momento.",
                "debug": dati
            }), 502

        forecast_days = dati["forecast"]["forecastday"]

        if giorno >= len(forecast_days):
            return jsonify({
                "descrizione": "Questa previsione non è disponibile."
            }), 400

        giorno_dati = forecast_days[giorno]
        meteo = giorno_dati["day"]

        temperatura = meteo["avgtemp_c"]
        temp_min = meteo["mintemp_c"]
        temp_max = meteo["maxtemp_c"]
        vento = meteo["maxwind_kph"]
        raffiche = vento
        direzione_vento = 0
        pioggia = meteo["totalprecip_mm"]
        nuvole = 0
        condizione = meteo["condition"]["text"]

        if giorno == 1:
            nome_giorno = "domani"
        elif giorno == 2:
            nome_giorno = "tra 2 giorni"
        else:
            nome_giorno = "tra 3 giorni"

    nome_vento = nome_vento_da_gradi(direzione_vento)
    vento_locale = adatta_vento_sardegna(nome_vento, direzione_vento)

    if raffiche >= 60:
        valutazione_vento = "vento molto forte"
    elif raffiche >= 40:
        valutazione_vento = "vento sostenuto"
    else:
        valutazione_vento = "vento debole o moderato"

    if pioggia > 5:
        valutazione_meteo = "sono possibili piogge significative"
    elif pioggia > 0:
        valutazione_meteo = "non si esclude qualche precipitazione"
    else:
        valutazione_meteo = "non sono previste precipitazioni rilevanti"

    consiglio = crea_consiglio(temperatura, vento, raffiche, pioggia, nuvole)

    if giorno == 0:
        risposta_chiara = (
            f"A {nome_localita} ci sono {temperatura}°C. "
            f"Il vento soffia da {vento_locale.lower()}, con raffiche fino a {raffiche} km/h. "
            f"Il cielo risulta: {condizione.lower()}. "
            f"{valutazione_meteo.capitalize()}."
            f"{consiglio}"
        )
    else:
        risposta_chiara = (
            f"A {nome_localita}, {nome_giorno}, ci si aspetta una giornata con {condizione.lower()}. "
            f"Le temperature saranno comprese tra {temp_min}°C e {temp_max}°C, "
            f"con una media intorno ai {temperatura}°C. "
            f"Il vento potrà raggiungere circa {vento} km/h: {valutazione_vento}."
        )

        if pioggia > 0:
            risposta_chiara += " Possibili precipitazioni durante la giornata."

        risposta_chiara += consiglio

    risposta_finale = {
        "localita": nome_localita,
        "coordinate": {
            "lat": lat,
            "lon": lon
        },
        "giorno": giorno,
        "quando": nome_giorno,
        "temperatura": temperatura,
        "vento": vento,
        "raffiche": raffiche,
        "precipitazioni": pioggia,
        "condizione": condizione,
        "valutazione_vento": valutazione_vento,
        "valutazione_meteo": valutazione_meteo,
        "descrizione": risposta_chiara,
        "cache": "aggiornata",
        "provider": "WeatherAPI"
    }

    if giorno == 0:
        risposta_finale["direzione_vento"] = {
            "gradi": direzione_vento,
            "nome": nome_vento,
            "locale": vento_locale
        }
        risposta_finale["copertura_nuvolosa"] = nuvole
    else:
        risposta_finale["temperatura_min"] = temp_min
        risposta_finale["temperatura_max"] = temp_max

    CACHE[chiave_cache] = {
        "timestamp": adesso,
        "risposta": risposta_finale
    }

    return jsonify(risposta_finale)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)