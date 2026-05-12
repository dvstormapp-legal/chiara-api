from flask import Flask, request, jsonify
import requests
import json
import time
import os

app = Flask(__name__)

CACHE = {}
CACHE_DURATA_SECONDI = 1800  # 30 minuti


@app.route("/")
def home():
    return "Chiara API attiva"


@app.route("/chiara")
def chiara():
    nome_cercato = request.args.get("localita", "Cagliari")

    chiave_cache = nome_cercato.strip().lower()
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
            "errore": "WEATHER_API_KEY non configurata su Render"
        }), 500

    with open("localita_sardegna.json", "r", encoding="utf-8") as file:
        localita_sardegna = json.load(file)

    localita_trovata = None

    for localita in localita_sardegna:
        nome = localita["nome"].lower()
        id_localita = localita["id"].lower()

        if nome_cercato.lower() in nome or nome_cercato.lower() in id_localita:
            localita_trovata = localita
            break

    if localita_trovata is None:
        return jsonify({"errore": "Località non trovata"}), 404

    nome_localita = localita_trovata["nome"]
    lat = localita_trovata["lat"]
    lon = localita_trovata["lng"]

    url = (
        "https://api.weatherapi.com/v1/current.json"
        f"?key={api_key}"
        f"&q={lat},{lon}"
        "&lang=it"
    )

    risposta = requests.get(url, timeout=10)
    dati = risposta.json()

    if "current" not in dati:
        return jsonify({
            "errore": "Dati meteo non disponibili",
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

    if direzione_vento >= 337.5 or direzione_vento < 22.5:
        nome_vento = "Tramontana"
    elif direzione_vento < 67.5:
        nome_vento = "Grecale"
    elif direzione_vento < 112.5:
        nome_vento = "Levante"
    elif direzione_vento < 157.5:
        nome_vento = "Scirocco"
    elif direzione_vento < 202.5:
        nome_vento = "Ostro"
    elif direzione_vento < 247.5:
        nome_vento = "Libeccio"
    elif direzione_vento < 292.5:
        nome_vento = "Ponente"
    else:
        nome_vento = "Maestrale"

    vento_locale = nome_vento

    if nome_vento == "Ponente" and direzione_vento > 280:
        vento_locale = "Ponente-maestrale"

    if nome_vento == "Maestrale":
        vento_locale = "Maestrale (tipico della Sardegna)"

    if raffiche >= 60:
        valutazione_vento = "Vento molto forte"
    elif raffiche >= 40:
        valutazione_vento = "Vento forte"
    else:
        valutazione_vento = "Vento debole o moderato"

    if pioggia > 0:
        valutazione_meteo = "Sono presenti precipitazioni"
    elif nuvole > 80:
        valutazione_meteo = "Cielo molto nuvoloso"
    else:
        valutazione_meteo = "Cielo variabile o sereno"

    risposta_chiara = (
        f"A {nome_localita} ci sono {temperatura}°C. "
        f"Soffia {vento_locale.lower()} con raffiche fino a {raffiche} km/h. "
        f"{valutazione_meteo}. Condizione rilevata: {condizione}."
    )

    risposta_finale = {
        "localita": nome_localita,
        "coordinate": {
            "lat": lat,
            "lon": lon
        },
        "temperatura": temperatura,
        "vento": vento,
        "raffiche": raffiche,
        "direzione_vento": {
            "gradi": direzione_vento,
            "nome": nome_vento,
            "locale": vento_locale
        },
        "precipitazioni": pioggia,
        "copertura_nuvolosa": nuvole,
        "condizione": condizione,
        "valutazione_vento": valutazione_vento,
        "valutazione_meteo": valutazione_meteo,
        "descrizione": risposta_chiara,
        "cache": "aggiornata",
        "provider": "WeatherAPI"
    }

    CACHE[chiave_cache] = {
        "timestamp": adesso,
        "risposta": risposta_finale
    }

    return jsonify(risposta_finale)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)