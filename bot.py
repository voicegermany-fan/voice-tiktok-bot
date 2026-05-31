"""
The Voice Germany TikTok Bot
Generiert automatisch Ranking-Posts und postet sie auf TikTok.
"""

import os
import json
import random
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io

# ─── Konfiguration ────────────────────────────────────────────────────────────

TIKTOK_CLIENT_KEY    = os.environ["TIKTOK_CLIENT_KEY"]
TIKTOK_CLIENT_SECRET = os.environ["TIKTOK_CLIENT_SECRET"]
TIKTOK_ACCESS_TOKEN  = os.environ["TIKTOK_ACCESS_TOKEN"]

# Farben für das Ranking-Design
COLORS = {
    "background": (15, 15, 20),
    "card":       (25, 25, 35),
    "red":        (226, 75, 74),
    "gold":       (255, 196, 0),
    "silver":     (180, 180, 190),
    "bronze":     (180, 100, 50),
    "white":      (255, 255, 255),
    "gray":       (140, 140, 150),
    "accent":     (226, 75, 74),
}

# ─── Content-Daten ────────────────────────────────────────────────────────────

RANKINGS = [
    {
        "title": "Top 5 Blind Auditions aller Zeiten",
        "subtitle": "The Voice Germany – Die emotionalsten Momente",
        "hashtags": "#TheVoiceGermany #BlindAudition #Top5 #Musik #Talent #Viral",
        "items": [
            {"rank": 1, "name": "Andrea Berg",    "detail": "Staffel 3",  "song": "Du hast mich tausendmal belogen"},
            {"rank": 2, "name": "Lina Seefried",  "detail": "Staffel 11", "song": "Chandelier"},
            {"rank": 3, "name": "Jonny Fischer",  "detail": "Staffel 10", "song": "Bohemian Rhapsody"},
            {"rank": 4, "name": "Sarah Lombardi", "detail": "Staffel 2",  "song": "Son of a Preacher Man"},
            {"rank": 5, "name": "Manon Joste",    "detail": "Staffel 12", "song": "River"},
        ],
    },
    {
        "title": "Top 5 The Voice Kids Auftritte",
        "subtitle": "Die stärksten Kinder-Talente Deutschlands",
        "hashtags": "#TheVoiceKids #Talent #Top5 #Kinder #Musik #Deutschland",
        "items": [
            {"rank": 1, "name": "Fabio",  "detail": "9 Jahre",  "song": "Bohemian Rhapsody"},
            {"rank": 2, "name": "Anny",   "detail": "11 Jahre", "song": "Rise Up"},
            {"rank": 3, "name": "Leon",   "detail": "10 Jahre", "song": "Shallow"},
            {"rank": 4, "name": "Maya",   "detail": "12 Jahre", "song": "Hallelujah"},
            {"rank": 5, "name": "Tim",    "detail": "13 Jahre", "song": "Imagine"},
        ],
    },
    {
        "title": "Top 5 Coach-Statistiken",
        "subtitle": "Wer hat die meisten Chairs gedreht?",
        "hashtags": "#TheVoiceGermany #Coaches #Ranking #Top5 #Statistik",
        "items": [
            {"rank": 1, "name": "Rea Garvey",       "detail": "Coach seit Staffel 1", "song": "3 Gewinner · 47 Blind Turns"},
            {"rank": 2, "name": "Mark Forster",      "detail": "Coach seit Staffel 7", "song": "2 Gewinner · 38 Blind Turns"},
            {"rank": 3, "name": "Stefanie Kloß",     "detail": "Coach seit Staffel 9", "song": "2 Gewinner · 31 Blind Turns"},
            {"rank": 4, "name": "Nena",              "detail": "Coach (Staffel 1–3)",  "song": "1 Gewinner · 29 Blind Turns"},
            {"rank": 5, "name": "Lena",              "detail": "Coach seit Staffel 12","song": "1 Gewinner · 22 Blind Turns"},
        ],
    },
    {
        "title": "Top 5 meistgeklickte Songs auf YouTube",
        "subtitle": "The Voice Germany – die viralen Auftritte",
        "hashtags": "#TheVoiceGermany #YouTube #Viral #Top5 #Musik #Rekord",
        "items": [
            {"rank": 1, "name": "Lina Seefried",    "detail": "50+ Mio. Views",  "song": "Chandelier"},
            {"rank": 2, "name": "Jonny Fischer",    "detail": "38 Mio. Views",   "song": "Bohemian Rhapsody"},
            {"rank": 3, "name": "Manon Joste",      "detail": "29 Mio. Views",   "song": "River"},
            {"rank": 4, "name": "Stefanie Heinzmann","detail": "24 Mio. Views",  "song": "Halo"},
            {"rank": 5, "name": "Alexander Knappe", "detail": "18 Mio. Views",   "song": "Titanium"},
        ],
    },
    {
        "title": "Top 5 emotionalste Coach-Reaktionen",
        "subtitle": "Wenn selbst die Coaches Tränen bekommen",
        "hashtags": "#TheVoiceGermany #Coaches #Emotional #Top5 #Gänsehaut",
        "items": [
            {"rank": 1, "name": "Mark Forster weint", "detail": "Staffel 10",   "song": "bei Bohemian Rhapsody"},
            {"rank": 2, "name": "Nena steht auf",     "detail": "Staffel 2",    "song": "bei Rise Up"},
            {"rank": 3, "name": "Rea Garvey springt", "detail": "Staffel 8",    "song": "bei Hallelujah"},
            {"rank": 4, "name": "Stefanie Kloß weint","detail": "Staffel 12",   "song": "bei Imagine"},
            {"rank": 5, "name": "Alle 4 drehen sich", "detail": "Staffel 11",   "song": "bei Chandelier"},
        ],
    },
]

CAPTION_TEMPLATES = [
    "Welcher Platz überrascht dich am meisten? Kommentiere unten! 👇",
    "Bist du einverstanden? Schreib deinen Favoriten in die Kommentare! 🎤",
    "Welcher Moment fehlt in dieser Liste? 👇",
    "Folgen für täglich neue The Voice Rankings! 🔔",
    "Wer war DEIN Favorit? Lass es uns wissen! 👇🎶",
]

# ─── Bild-Generator ───────────────────────────────────────────────────────────

def create_ranking_image(ranking: dict) -> bytes:
    """Erstellt ein 1080x1920 TikTok-Ranking-Bild."""
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), COLORS["background"])
    draw = ImageDraw.Draw(img)

    # Versuch, Schriftarten zu laden (Fallback auf Standard)
    try:
        font_big    = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
        font_med    = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
        font_small  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        font_tiny   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        font_rank   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
    except Exception:
        font_big   = ImageFont.load_default()
        font_med   = font_big
        font_small = font_big
        font_tiny  = font_big
        font_rank  = font_big

    # Header-Bereich
    draw.rectangle([(0, 0), (W, 220)], fill=COLORS["red"])

    # Logo-Text
    draw.text((540, 60),  "🎤 THE VOICE",  font=font_big,  fill=COLORS["white"],  anchor="mm")
    draw.text((540, 120), "GERMANY",        font=font_big,  fill=COLORS["white"],  anchor="mm")
    draw.text((540, 175), "RANKING",        font=font_small,fill=COLORS["white"],  anchor="mm")

    # Titel
    title_lines = textwrap.wrap(ranking["title"], width=28)
    y = 260
    for line in title_lines:
        draw.text((540, y), line, font=font_med, fill=COLORS["white"], anchor="mm")
        y += 55

    # Trennlinie
    draw.rectangle([(80, y + 10), (W - 80, y + 14)], fill=COLORS["red"])
    y += 50

    # Ranking-Karten
    rank_colors = {1: COLORS["gold"], 2: COLORS["silver"], 3: COLORS["bronze"]}

    for item in ranking["items"]:
        card_top = y
        card_h   = 230
        rank_col = rank_colors.get(item["rank"], COLORS["gray"])

        # Karten-Hintergrund
        draw.rounded_rectangle([(60, card_top), (W - 60, card_top + card_h)],
                                radius=20, fill=COLORS["card"])

        # Rang-Balken links
        draw.rounded_rectangle([(60, card_top), (130, card_top + card_h)],
                                radius=20, fill=rank_col)
        draw.text((95, card_top + card_h // 2),
                  str(item["rank"]), font=font_rank,
                  fill=COLORS["background"], anchor="mm")

        # Platz-Label
        rank_label = {1: "PLATZ", 2: "PLATZ", 3: "PLATZ"}.get(item["rank"], "PLATZ")
        draw.text((95, card_top + card_h // 2 + 42),
                  rank_label, font=font_tiny,
                  fill=COLORS["background"], anchor="mm")

        # Name
        draw.text((155, card_top + 45),
                  item["name"], font=font_med,
                  fill=COLORS["white"], anchor="lm")

        # Detail (Staffel / Jahr)
        draw.text((155, card_top + 100),
                  item["detail"], font=font_small,
                  fill=rank_col, anchor="lm")

        # Song
        song_lines = textwrap.wrap(f'🎵 "{item["song"]}"', width=32)
        sy = card_top + 148
        for sl in song_lines:
            draw.text((155, sy), sl, font=font_tiny, fill=COLORS["gray"], anchor="lm")
            sy += 34

        # Trennlinie zwischen Karten (außer letzte)
        if item["rank"] < len(ranking["items"]):
            draw.rectangle([(60, card_top + card_h + 6),
                             (W - 60, card_top + card_h + 8)],
                            fill=(40, 40, 55))

        y += card_h + 16

    # Footer
    footer_y = H - 120
    draw.rectangle([(0, footer_y), (W, H)], fill=COLORS["red"])
    caption = random.choice(CAPTION_TEMPLATES)
    draw.text((540, footer_y + 40),
              caption, font=font_tiny, fill=COLORS["white"], anchor="mm")
    draw.text((540, footer_y + 85),
              "📲 Folgen für mehr Rankings!", font=font_tiny,
              fill=COLORS["white"], anchor="mm")

    # Als Bytes zurückgeben
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


# ─── TikTok API ───────────────────────────────────────────────────────────────

def get_tiktok_headers() -> dict:
    return {
        "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
        "Content-Type":  "application/json; charset=UTF-8",
    }


def upload_photo_to_tiktok(image_bytes: bytes) -> str:
    """Lädt ein Bild hoch und gibt die media_id zurück."""
    # Schritt 1: Upload-URL anfordern
    init_resp = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/video/init/",
        headers=get_tiktok_headers(),
        json={
            "source_info": {
                "source":     "FILE_UPLOAD",
                "video_size": len(image_bytes),
                "chunk_size": len(image_bytes),
                "total_chunk_count": 1,
            }
        },
        timeout=30,
    )
    init_resp.raise_for_status()
    data      = init_resp.json().get("data", {})
    upload_url = data["upload_url"]
    publish_id = data["publish_id"]

    # Schritt 2: Bild hochladen
    upload_resp = requests.put(
        upload_url,
        data=image_bytes,
        headers={
            "Content-Type":         "image/jpeg",
            "Content-Length":       str(len(image_bytes)),
            "Content-Range":        f"bytes 0-{len(image_bytes)-1}/{len(image_bytes)}",
        },
        timeout=60,
    )
    upload_resp.raise_for_status()
    return publish_id


def publish_photo_post(publish_id: str, caption: str) -> dict:
    """Veröffentlicht das hochgeladene Foto als TikTok-Post."""
    resp = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/photo/init/",
        headers=get_tiktok_headers(),
        json={
            "post_info": {
                "title":          caption[:2200],
                "privacy_level":  "PUBLIC_TO_EVERYONE",
                "disable_duet":   False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source":       "PULL_FROM_URL",
                "photo_images": [f"publish_id:{publish_id}"],
                "photo_cover_index": 0,
            },
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ─── Posting-Logik ────────────────────────────────────────────────────────────

def get_todays_ranking() -> dict:
    """Wählt das Ranking für heute – rotiert durch alle 5 Optionen."""
    day_of_year  = datetime.date.today().timetuple().tm_yday
    post_number  = int(os.environ.get("POST_NUMBER", "0"))  # 0–4 je Tageszeit
    index        = (day_of_year + post_number) % len(RANKINGS)
    return RANKINGS[index]


def build_caption(ranking: dict) -> str:
    caption  = f"🎤 {ranking['title']}\n\n"
    for item in ranking["items"]:
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(item["rank"], f"{item['rank']}.")
        caption += f"{medal} {item['name']} – \"{item['song']}\"\n"
    caption += f"\n{random.choice(CAPTION_TEMPLATES)}\n\n"
    caption += ranking["hashtags"]
    return caption


def run():
    print(f"[{datetime.datetime.now()}] The Voice Germany TikTok Bot startet...")
    ranking = get_todays_ranking()
    print(f"  Ranking: {ranking['title']}")

    # Bild erstellen
    print("  Erstelle Ranking-Bild...")
    image_bytes = create_ranking_image(ranking)
    print(f"  Bild erstellt: {len(image_bytes) // 1024} KB")

    # Auf TikTok hochladen
    print("  Lade Bild auf TikTok hoch...")
    publish_id = upload_photo_to_tiktok(image_bytes)
    print(f"  Upload erfolgreich, publish_id: {publish_id}")

    # Caption erstellen und posten
    caption = build_caption(ranking)
    print("  Poste auf TikTok...")
    result = publish_photo_post(publish_id, caption)
    print(f"  Post erfolgreich! Antwort: {json.dumps(result, indent=2)}")
    print(f"[{datetime.datetime.now()}] Fertig!")


if __name__ == "__main__":
    run()

