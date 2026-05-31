"""
The Voice Germany TikTok Bot
Postet automatisch Ranking-Bilder auf TikTok via Video Upload (MP4).
"""

import os
import json
import random
import datetime
import requests
import subprocess
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import tempfile

TIKTOK_CLIENT_KEY    = os.environ["TIKTOK_CLIENT_KEY"]
TIKTOK_CLIENT_SECRET = os.environ["TIKTOK_CLIENT_SECRET"]
TIKTOK_ACCESS_TOKEN  = os.environ["TIKTOK_ACCESS_TOKEN"]

COLORS = {
    "background": (15, 15, 20),
    "card":       (25, 25, 35),
    "red":        (226, 75, 74),
    "gold":       (255, 196, 0),
    "silver":     (180, 180, 190),
    "bronze":     (180, 100, 50),
    "white":      (255, 255, 255),
    "gray":       (140, 140, 150),
}

RANKINGS = [
    {
        "title": "Top 5 Blind Auditions aller Zeiten",
        "hashtags": "#TheVoiceGermany #BlindAudition #Top5 #Musik #Talent",
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
        "hashtags": "#TheVoiceKids #Talent #Top5 #Kinder #Musik",
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
        "hashtags": "#TheVoiceGermany #Coaches #Ranking #Top5",
        "items": [
            {"rank": 1, "name": "Rea Garvey",   "detail": "Staffel 1+",  "song": "3 Gewinner"},
            {"rank": 2, "name": "Mark Forster", "detail": "Staffel 7+",  "song": "2 Gewinner"},
            {"rank": 3, "name": "Stef. Kloss",  "detail": "Staffel 9+",  "song": "2 Gewinner"},
            {"rank": 4, "name": "Nena",         "detail": "Staffel 1-3", "song": "1 Gewinner"},
            {"rank": 5, "name": "Lena",         "detail": "Staffel 12+", "song": "1 Gewinner"},
        ],
    },
    {
        "title": "Top 5 meistgeklickte Songs",
        "hashtags": "#TheVoiceGermany #YouTube #Viral #Top5 #Musik",
        "items": [
            {"rank": 1, "name": "Lina Seefried",    "detail": "50+ Mio. Views", "song": "Chandelier"},
            {"rank": 2, "name": "Jonny Fischer",    "detail": "38 Mio. Views",  "song": "Bohemian Rhapsody"},
            {"rank": 3, "name": "Manon Joste",      "detail": "29 Mio. Views",  "song": "River"},
            {"rank": 4, "name": "Stef. Heinzmann",  "detail": "24 Mio. Views",  "song": "Halo"},
            {"rank": 5, "name": "Alex. Knappe",     "detail": "18 Mio. Views",  "song": "Titanium"},
        ],
    },
    {
        "title": "Top 5 Coach-Reaktionen",
        "hashtags": "#TheVoiceGermany #Coaches #Emotional #Top5",
        "items": [
            {"rank": 1, "name": "Mark Forster weint", "detail": "Staffel 10", "song": "bei Bohemian Rhapsody"},
            {"rank": 2, "name": "Nena steht auf",     "detail": "Staffel 2",  "song": "bei Rise Up"},
            {"rank": 3, "name": "Rea springt auf",    "detail": "Staffel 8",  "song": "bei Hallelujah"},
            {"rank": 4, "name": "Stef. Kloss weint",  "detail": "Staffel 12", "song": "bei Imagine"},
            {"rank": 5, "name": "Alle 4 drehen sich", "detail": "Staffel 11", "song": "bei Chandelier"},
        ],
    },
]

CAPTION_TEMPLATES = [
    "Welcher Platz ueberrascht dich am meisten?",
    "Bist du einverstanden? Kommentiere deinen Favoriten!",
    "Welcher Moment fehlt in dieser Liste?",
    "Folgen fuer taeglich neue The Voice Rankings!",
    "Wer war DEIN Favorit?",
]


def create_ranking_image(ranking: dict) -> bytes:
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), COLORS["background"])
    draw = ImageDraw.Draw(img)

    try:
        font_big   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
        font_med   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        font_tiny  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        font_rank  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
    except Exception:
        font_big = font_med = font_small = font_tiny = font_rank = ImageFont.load_default()

    draw.rectangle([(0, 0), (W, 220)], fill=COLORS["red"])
    draw.text((540, 70),  "THE VOICE", font=font_big,   fill=COLORS["white"], anchor="mm")
    draw.text((540, 130), "GERMANY",   font=font_big,   fill=COLORS["white"], anchor="mm")
    draw.text((540, 180), "RANKING",   font=font_small, fill=COLORS["white"], anchor="mm")

    title_lines = textwrap.wrap(ranking["title"], width=28)
    y = 260
    for line in title_lines:
        draw.text((540, y), line, font=font_med, fill=COLORS["white"], anchor="mm")
        y += 55

    draw.rectangle([(80, y + 10), (W - 80, y + 14)], fill=COLORS["red"])
    y += 50

    rank_colors = {1: COLORS["gold"], 2: COLORS["silver"], 3: COLORS["bronze"]}

    for item in ranking["items"]:
        card_top = y
        card_h   = 230
        rank_col = rank_colors.get(item["rank"], COLORS["gray"])

        draw.rounded_rectangle([(60, card_top), (W - 60, card_top + card_h)], radius=20, fill=COLORS["card"])
        draw.rounded_rectangle([(60, card_top), (130, card_top + card_h)],    radius=20, fill=rank_col)
        draw.text((95, card_top + card_h // 2),      str(item["rank"]), font=font_rank,  fill=COLORS["background"], anchor="mm")
        draw.text((95, card_top + card_h // 2 + 42), "PLATZ",           font=font_tiny,  fill=COLORS["background"], anchor="mm")
        draw.text((155, card_top + 45),  item["name"],   font=font_med,   fill=COLORS["white"], anchor="lm")
        draw.text((155, card_top + 100), item["detail"], font=font_small, fill=rank_col,        anchor="lm")

        song_lines = textwrap.wrap(f'"{item["song"]}"', width=32)
        sy = card_top + 148
        for sl in song_lines:
            draw.text((155, sy), sl, font=font_tiny, fill=COLORS["gray"], anchor="lm")
            sy += 34

        if item["rank"] < len(ranking["items"]):
            draw.rectangle([(60, card_top + card_h + 6), (W - 60, card_top + card_h + 8)], fill=(40, 40, 55))

        y += card_h + 16

    footer_y = H - 120
    draw.rectangle([(0, footer_y), (W, H)], fill=COLORS["red"])
    draw.text((540, footer_y + 40), random.choice(CAPTION_TEMPLATES), font=font_tiny, fill=COLORS["white"], anchor="mm")
    draw.text((540, footer_y + 85), "Folgen fuer mehr Rankings!", font=font_tiny, fill=COLORS["white"], anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def image_to_video(image_bytes: bytes, duration: int = 5) -> str:
    """Konvertiert ein Bild in ein kurzes MP4-Video fuer TikTok."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(image_bytes)
        img_path = f.name

    video_path = img_path.replace(".jpg", ".mp4")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", img_path,
        "-c:v", "libx264",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1080:1920",
        "-r", "30",
        video_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg Fehler: {result.stderr}")
        raise Exception("Video-Konvertierung fehlgeschlagen")

    print(f"Video erstellt: {video_path}")
    return video_path


def post_video_to_tiktok(video_path: str, caption: str):
    """Postet ein Video auf TikTok via Direct Post."""
    token = TIKTOK_ACCESS_TOKEN.strip()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8",
    }

    video_size = os.path.getsize(video_path)
    print(f"Videogroesse: {video_size // 1024} KB")

    # Schritt 1: Creator Info abfragen (TikTok Pflicht)
    print("Frage Creator Info ab...")
    creator_resp = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/creator_info/query/",
        headers=headers,
        json={},
        timeout=30,
    )
    print(f"Creator Info: {creator_resp.status_code} - {creator_resp.text[:200]}")

    # Schritt 2: Video Post initialisieren
    print("Initialisiere Video Post...")
    init_resp = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/video/init/",
        headers=headers,
        json={
            "post_info": {
                "title": caption[:150],
                "privacy_level": "SELF_ONLY",
                "disable_comment": False,
                "disable_duet": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": video_size,
                "total_chunk_count": 1,
            },
        },
        timeout=30,
    )
    print(f"Init Antwort: {init_resp.status_code} - {init_resp.text[:300]}")
    init_resp.raise_for_status()

    data       = init_resp.json().get("data", {})
    publish_id = data.get("publish_id")
    upload_url = data.get("upload_url")

    if not upload_url:
        print("Fehler: Kein upload_url!")
        return

    # Schritt 3: Video hochladen
    print("Lade Video hoch...")
    with open(video_path, "rb") as f:
        video_bytes = f.read()

    upload_resp = requests.put(
        upload_url,
        data=video_bytes,
        headers={
            "Content-Type":   "video/mp4",
            "Content-Length": str(video_size),
            "Content-Range":  f"bytes 0-{video_size-1}/{video_size}",
        },
        timeout=120,
    )
    print(f"Upload Antwort: {upload_resp.status_code}")
    upload_resp.raise_for_status()

    print(f"Erfolgreich! publish_id: {publish_id}")
    return publish_id


def get_todays_ranking() -> dict:
    day_of_year = datetime.date.today().timetuple().tm_yday
    post_number = int(os.environ.get("POST_NUMBER", "0"))
    index       = (day_of_year + post_number) % len(RANKINGS)
    return RANKINGS[index]


def build_caption(ranking: dict) -> str:
    caption = f"The Voice Germany - {ranking['title']}\n\n"
    for item in ranking["items"]:
        caption += f"{item['rank']}. {item['name']} - {item['song']}\n"
    caption += f"\n{random.choice(CAPTION_TEMPLATES)}\n\n"
    caption += ranking["hashtags"]
    return caption


def run():
    print(f"[{datetime.datetime.now()}] Bot startet...")
    ranking = get_todays_ranking()
    print(f"Ranking: {ranking['title']}")

    print("Erstelle Bild...")
    image_bytes = create_ranking_image(ranking)
    print(f"Bild: {len(image_bytes) // 1024} KB")

    print("Konvertiere zu Video...")
    video_path = image_to_video(image_bytes, duration=8)

    caption = build_caption(ranking)
    print("Poste auf TikTok...")
    post_video_to_tiktok(video_path, caption)

    os.unlink(video_path)
    print(f"[{datetime.datetime.now()}] Fertig!")


if __name__ == "__main__":
    run()
