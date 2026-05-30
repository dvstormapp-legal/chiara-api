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


def leggi_numero(dizionario, chiavi, valore_default=None):
    """
    Legge un numero da un dizionario provando più nomi di chiave.
    Serve per evitare crash se l'API restituisce nomi diversi o dati incompleti.
    """
    for chiave in chiavi:
        if chiave in dizionario and dizionario[chiave] is not None:
            try:
                return float(dizionario[chiave])
            except (TypeError, ValueError):
                pass
    return valore_default


def leggi_testo(dizionario, chiavi, valore_default=""):
    for chiave in chiavi:
        if chiave in dizionario and dizionario[chiave] is not None:
            return str(dizionario[chiave])
    return valore_default


def nome_vento_da_gradi(gradi):
    if gradi is None:
        return "vento non definito"

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
    if gradi is None:
        return nome_vento

    if nome_vento == "Ponente" and gradi > 280:
        return "Ponente-maestrale"
    return nome_vento


def descrivi_condizione(condizione, pioggia, raffiche, is_day=True):
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

    if "sole" in c or "soleggiato" in c or "sereno" in c or "clear" in c:
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

    if "parzialmente" in c or "poco nuvoloso" in c or "partly cloudy" in c:
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

    if "nuvoloso" in c or "coperto" in c or "cloud" in c or "overcast" in c:
        return random.choice([
            "il cielo è in prevalenza nuvoloso",
            "la nuvolosità è piuttosto presente",
            "il cielo si presenta spesso coperto"
        ])

    if condizione:
        return f"il tempo è caratterizzato da {condizione.lower()}"

    return "i dati disponibili non descrivono chiaramente lo stato del cielo"


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


def carica_localita():
    with open("localita_sardegna.json", "r", encoding="utf-8") as file:
        return json.load(file)


def trova_localita(testo_input, localita_sardegna):
    for localita in localita_sardegna:
        nome = localita.get("nome", "").lower()
        id_localita = localita.get("id", "").lower()

        if testo_input in nome or testo_input in id_localita:
            return localita

    return None


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
        localita_sardegna = carica_localita()
    except Exception as e:
        return jsonify({
            "descrizione": "Non riesco a leggere l'elenco delle località.",
            "errore": str(e)
        }), 500

    localita_trovata = trova_localita(testo_input, localita_sardegna)

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
        risposta_api = requests.get(url, timeout=10)
        dati = risposta_api.json()
    except Exception as e:
        return jsonify({
            "descrizione": "Non riesco a contattare il servizio meteo in questo momento.",
            "errore": str(e)
        }), 502

    if "error" in dati:
        return jsonify({
            "descrizione": "Il servizio meteo non ha restituito dati validi per questa richiesta.",
            "errore": dati.get("error")
        }), 502

    if giorno == 0:
        if "current" not in dati:
            return jsonify({
                "descrizione": "Non riesco a recuperare i dati meteo attuali in questo momento.",
                "debug": dati
            }), 502

        meteo = dati["current"]

        temperatura = leggi_numero(
            meteo,
            ["temp_c", "temperature_c", "temperature_2m", "temperature"],
            None
        )

        if temperatura is None:
            return jsonify({
                "descrizione": "Al momento non ho dati abbastanza affidabili sulla temperatura per questa località.",
                "errore": "temperatura_mancante",
                "debug_keys": list(meteo.keys())
            }), 502

        vento = leggi_numero(
            meteo,
            ["wind_kph", "wind_speed_10m", "windspeed_kph", "wind_speed"],
            0
        )

        raffiche = leggi_numero(
            meteo,
            ["gust_kph", "wind_gusts_10m", "windgust_kph", "gust"],
            vento
        )

        direzione_vento = leggi_numero(
            meteo,
            ["wind_degree", "wind_direction_10m", "wind_dir_degree"],
            None
        )

        pioggia = leggi_numero(
            meteo,
            ["precip_mm", "precipitation", "rain", "rain_mm"],
            0
        )

        nuvole = leggi_numero(
            meteo,
            ["cloud", "cloud_cover", "cloudcover"],
            0
        )

        condizione = ""
        if isinstance(meteo.get("condition"), dict):
            condizione = meteo.get("condition", {}).get("text", "")
        else:
            condizione = leggi_testo(meteo, ["condition", "weather", "summary"], "")

        is_day = meteo.get("is_day", 1) == 1
        nome_giorno = "adesso"

        nome_vento = nome_vento_da_gradi(direzione_vento)
        vento_locale = adatta_vento_sardegna(nome_vento, direzione_vento)

        frase_condizione = descrivi_condizione(condizione, pioggia, raffiche, is_day)
        frase_pioggia = descrivi_pioggia(pioggia)
        consiglio = crea_consiglio(temperatura, vento, raffiche, pioggia, nuvole)

        if direzione_vento is not None:
            frase_vento = (
                f"Il vento soffia da {vento_locale.lower()}, "
                f"con raffiche fino a {raffiche:g} km/h. "
            )
        else:
            frase_vento = (
                f"Il vento soffia a circa {vento:g} km/h, "
                f"con raffiche fino a {raffiche:g} km/h. "
            )

        risposta_chiara = (
            f"A {nome_localita} in questo momento ci sono {temperatura:g}°C. "
            f"{frase_condizione.capitalize()}. "
            f"{frase_vento}"
            f"{frase_pioggia}"
            f"{consiglio}"
        )

    else:
        if "forecast" not in dati:
            return jsonify({
                "descrizione": "Non riesco a recuperare la previsione in questo momento.",
                "debug": dati
            }), 502

        forecast_days = dati["forecast"].get("forecastday", [])

        if giorno >= len(forecast_days):
            return jsonify({
                "descrizione": "Questa previsione non è disponibile."
            }), 400

        giorno_dati = forecast_days[giorno]
        meteo = giorno_dati.get("day", {})

        temperatura = leggi_numero(meteo, ["avgtemp_c", "temp_c", "temperature"], None)
        temp_min = leggi_numero(meteo, ["mintemp_c", "temp_min", "temperature_min"], None)
        temp_max = leggi_numero(meteo, ["maxtemp_c", "temp_max", "temperature_max"], None)

        if temperatura is None or temp_min is None or temp_max is None:
            return jsonify({
                "descrizione": "Al momento non ho dati abbastanza affidabili sulla temperatura prevista per questa località.",
                "errore": "temperatura_previsione_mancante",
                "debug_keys": list(meteo.keys())
            }), 502

        vento = leggi_numero(meteo, ["maxwind_kph", "wind_kph", "wind_speed"], 0)
        raffiche = vento
        pioggia = leggi_numero(meteo, ["totalprecip_mm", "precip_mm", "precipitation"], 0)
        nuvole = 0

        if isinstance(meteo.get("condition"), dict):
            condizione = meteo.get("condition", {}).get("text", "")
        else:
            condizione = leggi_testo(meteo, ["condition", "weather", "summary"], "")

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
            f"La temperatura oscillerà tra {temp_min:g}°C e {temp_max:g}°C, "
            f"con una media intorno ai {temperatura:g}°C. "
            f"Il vento potrà raggiungere circa {vento:g} km/h. "
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