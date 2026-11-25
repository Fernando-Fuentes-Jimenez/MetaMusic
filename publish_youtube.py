"""Publica en YouTube (Pasta Clara) el Short del día según calendario.json.
Lo ejecuta GitHub Actions cada día. Necesita YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN."""
import json, os, sys, datetime, zoneinfo
import requests

RAW = "https://raw.githubusercontent.com/Fernando-Fuentes-Jimenez/MetaMusic/pasta-clara-media/"
API = "https://www.googleapis.com/youtube/v3"

def token():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]

def ya_subidos(h):
    ch = requests.get(f"{API}/channels", params={"part": "snippet,contentDetails", "mine": "true"}, headers=h, timeout=30).json()
    item = ch["items"][0]
    print("Canal:", item["snippet"]["title"])
    up = item["contentDetails"]["relatedPlaylists"]["uploads"]
    r = requests.get(f"{API}/playlistItems", params={"part": "snippet", "playlistId": up, "maxResults": 50}, headers=h, timeout=30).json()
    return {i["snippet"]["title"] for i in r.get("items", [])}

def main():
    fecha = os.environ.get("FECHA")
    if not fecha:
        # Ejecución programada (19:00 Madrid). GitHub a veces la retrasa horas: si arranca de madrugada
        # ya es "mañana" y publicaría el vídeo del día siguiente antes de tiempo. Antes de las 18:00
        # se usa la fecha de ayer (si ya estaba subido, no hace nada; si no, recupera el retrasado).
        ahora = datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Madrid"))
        dia = ahora.date() if ahora.hour >= 18 else ahora.date() - datetime.timedelta(days=1)
        fecha = dia.isoformat()
        print("Hora Madrid:", ahora.strftime("%Y-%m-%d %H:%M"), "→ fecha a publicar:", fecha)
    cal = requests.get(RAW + "calendario.json", timeout=30).json()
    hoy = [v for v in cal["videos"] if v["fecha"] == fecha and v.get("n8n", True) is not False]
    if not hoy:
        print("Nada que publicar el", fecha); return
    h = {"Authorization": f"Bearer {token()}"}
    subidos = ya_subidos(h)
    for v in hoy:
        if v["title"] in subidos:
            print("Ya estaba subido:", v["title"]); continue
        mp4 = requests.get(v["url"], timeout=300); mp4.raise_for_status()
        meta = {"snippet": {"title": v["title"], "description": v["description"],
                            "tags": [t.strip() for t in v["tags"].split(",") if t.strip()],
                            "categoryId": v.get("categoryId", "27"), "defaultLanguage": "es", "defaultAudioLanguage": "es"},
                "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
        init = requests.post("https://www.googleapis.com/upload/youtube/v3/videos",
                             params={"uploadType": "resumable", "part": "snippet,status"},
                             headers={**h, "Content-Type": "application/json; charset=UTF-8",
                                      "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(len(mp4.content))},
                             data=json.dumps(meta), timeout=60)
        init.raise_for_status()
        r = requests.put(init.headers["Location"], headers={"Content-Type": "video/mp4"}, data=mp4.content, timeout=600)
        r.raise_for_status()
        print("Publicado:", v["title"], "→ https://youtu.be/" + r.json()["id"])

if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        print("Error:", e.response.status_code, e.response.text[:800]); sys.exit(1)
