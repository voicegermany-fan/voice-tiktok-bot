"""
The Voice Germany TikTok Bot
Schneidet zufaellig 3 Clips zusammen mit Ranking-Overlay und postet auf TikTok.
"""

import os
import json
import random
import datetime
import requests
import subprocess
import glob
import textwrap
import io

TIKTOK_CLIENT_KEY    = os.environ["TIKTOK_CLIENT_KEY"]
TIKTOK_CLIENT_SECRET = os.environ["TIKTOK_CLIENT_SECRET"]
TIKTOK_ACCESS_TOKEN  = os.environ["TIKTOK_ACCESS_TOKEN"]

CAPTION_TEMPLATES = [
    "Welcher Auftritt hat dich am meisten begeistert? Kommentiere unten!",
    "Bist du einverstanden? Schreib deinen Favoriten in die Kommentare!",
    "Welcher Moment war dein Favorit?",
    "Folgen fuer taeglich neue The Voice Highlights!",
    "Wer war DEIN Favorit? Lass es uns wissen!",
]

HASHTAGS = "#TheVoiceGermany #TheVoiceKids #BlindAudition #Musik #Talent #Viral #Top3 #Ranking"


def get_clip_info(clip_path: str) -> dict:
    """Liest Metadaten aus dem Dateinamen.
    Format: Name_Song_Staffel.mp4
    Beispiel: Andrea-Berg_Du-hast-mich_Staffel-3.mp4
    """
    filename = os.path.splitext(os.path.basename(clip_path))[0]
    parts = filename.split("_")

    name    = parts[0].replace("-", " ") if len(parts) > 0 else "Unbekannt"
    song    = parts[1].replace("-", " ") if len(parts) > 1 else "Unbekannt"
    staffel = parts[2].replace("-", " ") if len(parts) > 2 else ""

    return {"name": name, "song": song, "staffel": staffel, "path": clip_path}


def get_video_duration(path: str) -> float:
    """Gibt die Laenge eines Videos in Sekunden zurueck."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except Exception:
        return 30.0


def create_combined_video(clips: list, output_path: str):
    """Schneidet 3 Clips zusammen mit Ranking-Overlay."""

    # Temporaere Dateien fuer jeden Clip
    temp_clips = []

    for i, clip in enumerate(clips):
        rank     = i + 1
        name     = clip["name"]
        song     = clip["song"]
        staffel  = clip["staffel"]
        duration = get_video_duration(clip["path"])

        # Maximale Clip-Laenge: 20 Sekunden (damit Gesamtvideo ~60s)
        clip_duration = min(duration, 20)
        # Mittleren Teil des Clips nehmen
        start = max(0, (duration - clip_duration) / 2)

        temp_path = f"/tmp/clip_{rank}.mp4"
        temp_clips.append(temp_path)

        # Overlay-Text
        rank_emoji = {1: "1.", 2: "2.", 3: "3."}[rank]
        line1 = f"PLATZ {rank}"
        line2 = name[:25]
        line3 = f"\"{song[:30]}\""
        line4 = staffel[:20] if staffel else ""

        # FFmpeg: Clip schneiden + auf 1080x1920 skalieren + Text-Overlay
        drawtext_cmds = [
            # Schwarzer Hintergrund-Banner oben
            f"drawbox=x=0:y=0:w=iw:h=180:color=black@0.75:t=fill",
            # Platz-Nummer gross
            f"drawtext=text='{line1}':fontsize=72:fontcolor=white:x=(w-text_w)/2:y=20:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            # Name
            f"drawtext=text='{line2}':fontsize=44:fontcolor=white:x=(w-text_w)/2:y=100:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            # Song
            f"drawtext=text='{line3}':fontsize=32:fontcolor=#aaaaaa:x=(w-text_w)/2:y=155:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

        if line4:
            drawtext_cmds.append(
                f"drawtext=text='{line4}':fontsize=28:fontcolor=#888888:x=(w-text_w)/2:y=200:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            )

        vf_filter = ",".join(drawtext_cmds)
        vf_filter = f"scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,{vf_filter}"

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", clip["path"],
            "-t", str(clip_duration),
            "-vf", vf_filter,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-r", "30",
            "-pix_fmt", "yuv420p",
            temp_path
        ]

        print(f"Verarbeite Clip {rank}: {name} - {song}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FFmpeg Fehler: {result.stderr[-500:]}")
            raise Exception(f"Clip {rank} fehlgeschlagen")

    # Alle Clips zusammenfuegen
    print("Fuege Clips zusammen...")
    concat_file = "/tmp/concat.txt"
    with open(concat_file, "w") as f:
        for p in temp_clips:
            f.write(f"file '{p}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Concat Fehler: {result.stderr[-500:]}")
        raise Exception("Zusammenfuegen fehlgeschlagen")

    # Temp-Dateien loeschen
    for p in temp_clips:
        if os.path.exists(p):
            os.unlink(p)

    print(f"Video fertig: {output_path}")


def post_video_to_tiktok(video_path: str, caption: str):
    token = TIKTOK_ACCESS_TOKEN.strip()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8",
    }

    video_size = os.path.getsize(video_path)
    print(f"Videogroesse: {video_size // 1024} KB")

    print("Frage Creator Info ab...")
    creator_resp = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/creator_info/query/",
        headers=headers,
        json={},
        timeout=30,
    )
    print(f"Creator Info: {creator_resp.status_code}")

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
    print(f"Init: {init_resp.status_code} - {init_resp.text[:200]}")
    init_resp.raise_for_status()

    data       = init_resp.json().get("data", {})
    publish_id = data.get("publish_id")
    upload_url = data.get("upload_url")

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
        timeout=300,
    )
    print(f"Upload: {upload_resp.status_code}")
    upload_resp.raise_for_status()

    print(f"Erfolgreich gepostet! publish_id: {publish_id}")
    return publish_id


def build_caption(clips: list) -> str:
    caption = "Top 3 The Voice Germany Momente\n\n"
    for i, clip in enumerate(clips):
        caption += f"{i+1}. {clip['name']} - \"{clip['song']}\"\n"
    caption += f"\n{random.choice(CAPTION_TEMPLATES)}\n\n"
    caption += HASHTAGS
    return caption


def run():
    print(f"[{datetime.datetime.now()}] Bot startet...")

    # Alle Clips aus dem clips/ Ordner laden
    clip_files = glob.glob("clips/*.mp4") + glob.glob("clips/*.MP4")

    if len(clip_files) < 3:
        print(f"Fehler: Nur {len(clip_files)} Clips gefunden. Mindestens 3 benoetigt!")
        return

    # Zufaellig 3 Clips auswaehlen
    selected = random.sample(clip_files, 3)
    clips    = [get_clip_info(c) for c in selected]

    print(f"Ausgewaehlte Clips:")
    for i, c in enumerate(clips):
        print(f"  {i+1}. {c['name']} - {c['song']}")

    # Video erstellen
    output_path = "/tmp/final_video.mp4"
    create_combined_video(clips, output_path)

    # Caption erstellen
    caption = build_caption(clips)

    # Auf TikTok posten
    print("Poste auf TikTok...")
    post_video_to_tiktok(output_path, caption)

    # Aufraumen
    if os.path.exists(output_path):
        os.unlink(output_path)

    print(f"[{datetime.datetime.now()}] Fertig!")


if __name__ == "__main__":
    run()
