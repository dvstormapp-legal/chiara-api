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
    return nome_vento


def descrivi_condizione(condizione, pioggia, raffiche, is_day=True):
    """
    Trasforma la condizione grezza dell'API in una frase naturale per Chiara.

    is_day serve per evitare frasi sbagliate di notte:
    - giorno + sereno = cielo sereno / situazione stabile
    - notte + sereno = notte serena / cielo notturno aperto
    """
    c = condizione.lower()

    if "temporale" in c or "thunder" in c:
        if raffiche >= 50 or pioggia >= 10:
            return random.choice([
                "sono possibili temporali, localmente anche intensi",
                "sono previsti fenomeni temporaleschi, con possibili fasi intense",
                "il tempo potrà risultare instabile, con temporali e fenomeni localmente forti"
            ])
        return random.choice([
            "sono possibili temporali",
            "potranno verificarsi temporali locali",
            "il tempo potrà risultare temporalesco a tratti"
        ])

    if pioggia >= 30:
        return random.choice([
            "sono previste piogge diffuse e abbondanti",
            "la situazione sarà segnata da precipitazioni importanti",
            "sono possibili piogge insistenti e localmente forti"
        ])

    if pioggia >= 10:
        return random.choice([
            "sono previste precipitazioni sparse",
            "sono possibili piogge a tratti anche moderate",
            "potranno verificarsi piogge distribuite a macchia di leopardo"
        ])

    if pioggia > 0:
        return random.choice([
            "potrebbe esserci qualche precipitazione sparsa",
            "qualche pioggia locale non è esclusa",
            "qualche pioggia sarà possibile"
        ])

    if "sole" in c or "soleggiato" in c or "sereno" in c:
        if is_day:
            return random.choice([
                "il cielo è sereno o poco nuvoloso",
                "il tempo è stabile, con cielo in prevalenza sereno",
                "il cielo si presenta abbastanza aperto"
            ])
        else:
            return random.choice([
                "il cielo è sereno o poco nuvoloso",
                "la notte si presenta serena o poco nuvolosa",
                "il cielo notturno è abbastanza aperto"
            ])

    if "parzialmente" in c or "poco nuvoloso" in c:
        if is_day:
            return random.choice([
                "il cielo è sereno o poco nuvoloso",
                "il cielo sarà abbastanza aperto, con qualche nuvola occasionale",
                "il cielo risulta parzialmente nuvoloso"
            ])
        else:
            return random.choice([
                "il cielo notturno è parzialmente nuvoloso",
                "la notte si presenta con qualche nube, ma senza segnali particolari",
                "il cielo è poco o parzialmente nuvoloso"
            ])

    if "nuvoloso" in c or "coperto" in c:
        return random.choice([
            "il cielo è in prevalenza nuvoloso",
            "la nuvolosità è piuttosto presente",
            "il cielo si presenta spesso coperto"
        ])

    return f"il tempo è caratterizzato da {condizione.lower()}"


def descrivi_pioggia(pioggia):
    if pioggia >= 30:
        return "Sono possibili piogge abbondanti."
    elif pioggia >= 10:
        return "Sono previste piogge sparse o a tratti moderate."
    elif pioggia > 0:
        return "Qualche pioggia locale non è esclusa."
    else:
        return "Non sono previste piogge."


def crea_consiglio(temperatura, vento, raffiche, pioggia, nuvole):
    if raffiche >= 70:
        return " ⚠️ Attenzione al vento forte."
    elif pioggia >= 30:
        return " ⚠️ Prestare attenzione a possibili piogge intense."
    elif pioggia >= 10:
        return " ☔ Meglio tenere un ombrello a portata di mano."
    elif temperatura >= 38:
        return " 🥵 Caldo intenso, meglio evitare le ore centrali."
    elif temperatura <= 0:
        return " ❄️ Temperature molto basse."
    elif vento <= 15 and pioggia == 0:
        return " 🌤️ Nel complesso sarà una situazione abbastanza tranquilla."
    elif nuvole > 80:
        return " ☁️ Meglio tenere d'occhio il cielo."
    return ""


@app.route("/chiara")
def chiara():
    nome_cercato = request.args.get("localita", "Cagliari")
    testo_input = nome_cercato.lower().strip()

    for parola in PAROLACCE:
        if parola in testo_input:
            return jsonify({
                "descrizione": random.choice(RISPOSTE_GAGGIU),
                "tipo": "gaggiu"
            })

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

    try:
        with open("localita_sardegna.json", "r", encoding="utf-8") as file:
            localita_sardegna = json.load(file)
    except Exception as e:
        return jsonify({
            "descrizione": "Non riesco a leggere l'elenco delle località.",
            "errore": str(e)
        }), 500

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
        })

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

    try:
        risposta = requests.get(url, timeout=10)
        dati = risposta.json()
    except Exception as e:
        return jsonify({
            "descrizione": "Non riesco a contattare il servizio meteo in questo momento.",
            "errore": str(e)
        }), 502

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
        is_day = meteo.get("is_day", 1) == 1
        nome_giorno = "adesso"

        nome_vento = nome_vento_da_gradi(direzione_vento)
        vento_locale = adatta_vento_sardegna(nome_vento, direzione_vento)

        frase_condizione = descrivi_condizione(condizione, pioggia, raffiche, is_day)
        frase_pioggia = descrivi_pioggia(pioggia)
        consiglio = crea_consiglio(temperatura, vento, raffiche, pioggia, nuvole)

        risposta_chiara = (
            f"A {nome_localita} in questo momento ci sono {temperatura}°C. "
            f"{frase_condizione.capitalize()}. "
            f"Il vento soffia da {vento_locale.lower()}, con raffiche fino a {raffiche} km/h. "
            f"{frase_pioggia}"
            f"{consiglio}"
        )

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
        pioggia = meteo["totalprecip_mm"]
        nuvole = 0
        condizione = meteo["condition"]["text"]

        if giorno == 1:
            nome_giorno = "domani"
            apertura = f"Per domani a {nome_localita}"
        elif giorno == 2:
            nome_giorno = "tra 2 giorni"
            apertura = f"A {nome_localita}, tra 2 giorni"
        else:
            nome_giorno = "tra 3 giorni"
            apertura = f"A {nome_localita}, tra 3 giorni"

        frase_condizione = descrivi_condizione(condizione, pioggia, raffiche, True)
        frase_pioggia = descrivi_pioggia(pioggia)
        consiglio = crea_consiglio(temperatura, vento, raffiche, pioggia, nuvole)

        risposta_chiara = (
            f"{apertura}, {frase_condizione}. "
            f"La temperatura oscillerà tra {temp_min}°C e {temp_max}°C, "
            f"con una media intorno ai {temperatura}°C. "
            f"Il vento potrà raggiungere circa {vento} km/h. "
            f"{frase_pioggia}"
            f"{consiglio}"
        )

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
        risposta_finale["is_day"] = is_day
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