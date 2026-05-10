from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

@app.route("/")
def home():
    return "Chiara API attiva"

@app.route("/chiara")
def chiara():

    nome_cercato = request.args.get("localita", "Cagliari")

    # --- LETTURA FILE LOCALITÀ ---
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
        return jsonify({"errore": "Località non trovata"})

    nome_localita = localita_trovata["nome"]
    lat = localita_trovata["lat"]
    lon = localita_trovata["lng"]

    # --- API METEO ---
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lon}"
        "&current=temperature_2m,wind_speed_10m,wind_gusts_10m,wind_direction_10m,precipitation,cloud_cover"
    )

    risposta = requests.get(url)
    dati = risposta.json()
    meteo = dati["current"]

    # --- DATI BASE ---
    vento = meteo["wind_speed_10m"]
    raffiche = meteo["wind_gusts_10m"]
    direzione_vento = meteo["wind_direction_10m"]
    pioggia = meteo["precipitation"]
    nuvole = meteo["cloud_cover"]

    # --- DIREZIONE VENTO ---
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

    # --- VALUTAZIONI ---
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

    # --- RISPOSTA CHIARA ---
    risposta_chiara = (
        f"A {nome_localita} ci sono {meteo['temperature_2m']}°C. "
        f"Soffia {vento_locale.lower()} con raffiche fino a {raffiche} km/h. "
        f"{valutazione_meteo}."
    )

    return jsonify({
        "localita": nome_localita,
        "coordinate": {
            "lat": lat,
            "lon": lon
        },
        "temperatura": meteo["temperature_2m"],
        "vento": vento,
        "raffiche": raffiche,
        "descrizione": risposta_chiara
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)