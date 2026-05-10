import requests
import json

nome_cercato = input("Scrivi una località della Sardegna: ")

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
    print("Località non trovata")
    exit()

nome_localita = localita_trovata["nome"]
lat = localita_trovata["lat"]
lon = localita_trovata["lng"]

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

# --- ADATTAMENTO SARDEGNA ---
vento_locale = nome_vento

if nome_vento == "Ponente" and direzione_vento > 280:
    vento_locale = "Ponente-maestrale"

if nome_vento == "Maestrale":
    vento_locale = "Maestrale (tipico della Sardegna)"

# --- VALUTAZIONE VENTO ---
if raffiche >= 60:
    valutazione_vento = "Vento molto forte, raffiche intense."
elif raffiche >= 40:
    valutazione_vento = "Vento moderato o forte, con raffiche significative."
elif vento >= 20:
    valutazione_vento = "Vento moderato."
else:
    valutazione_vento = "Vento debole o poco significativo."

# --- VALUTAZIONE METEO ---
if pioggia > 0:
    valutazione_meteo = "Sono presenti precipitazioni in corso."
elif nuvole > 80:
    valutazione_meteo = "Cielo molto nuvoloso, possibili fenomeni."
elif nuvole > 60:
    valutazione_meteo = "Cielo nuvoloso o variabile."
else:
    valutazione_meteo = "Cielo sereno o poco nuvoloso."

# --- INSTABILITÀ SARDEGNA ---
instabilita = "bassa"

if pioggia > 0:
    instabilita = "in atto"
elif nuvole > 70 and vento > 15:
    instabilita = "possibile instabilità"
elif nuvole > 50 and vento > 20:
    instabilita = "instabilità locale possibile"

# --- TEMPORALI / FENOMENI INTENSI ---
temporali = "non evidenti"

if pioggia > 0 and raffiche >= 50 and nuvole > 70:
    temporali = "possibili temporali o rovesci intensi in atto"
elif raffiche >= 60 and nuvole > 70:
    temporali = "possibili fenomeni convettivi con raffiche intense"
elif pioggia > 0 and nuvole > 80:
    temporali = "possibili rovesci o temporali locali"

# --- RISPOSTA CHIARA ---
risposta_chiara = (
    f"A {nome_localita} ci sono {meteo['temperature_2m']}°C. "
    f"Soffia {vento_locale.lower()} a {vento} km/h, "
    f"con raffiche fino a {raffiche} km/h. "
    f"{valutazione_meteo} "
)

# aggiunte intelligenti
if instabilita != "bassa":
    risposta_chiara += f"Attenzione: {instabilita}. "

if temporali != "non evidenti":
    risposta_chiara += f"Possibili {temporali}. "

# --- JSON FINALE ---
chiara_json = {
    "localita": nome_localita,
    "coordinate": {
        "lat": lat,
        "lon": lon
    },
    "temperatura": {
        "valore": meteo["temperature_2m"],
        "unita": "°C"
    },
    "vento": {
        "valore": vento,
        "unita": "km/h"
    },
    "raffiche": {
        "valore": raffiche,
        "unita": "km/h"
    },
    "direzione_vento": {
        "valore": direzione_vento,
        "unita": "gradi",
        "nome": nome_vento,
        "locale": vento_locale
    },
    "precipitazioni": {
        "valore": pioggia,
        "unita": "mm"
    },
    "copertura_nuvolosa": {
        "valore": nuvole,
        "unita": "%"
    },
    "valutazione_vento": valutazione_vento,
    "valutazione_meteo": valutazione_meteo,
    "instabilita": instabilita,
    "temporali": temporali,
    "risposta_chiara": risposta_chiara
}

print(json.dumps(chiara_json, indent=4, ensure_ascii=False))