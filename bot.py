import os, asyncio, yt_dlp, requests, spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from telegram.ext import Application, MessageHandler, filters

BOT_TOKEN = os.environ["8899070657:AAG7EXb4Mb8cYux59xAO0D2rC-Oujt_PQDc"]
CHANNEL_ID = os.environ["@MAINMusiccc"]

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.environ["8cfa98461e014f22905095b56567c554"],
    client_secret=os.environ["959ac2e5d6604c04b1380c01f9125370"]
))

def search_spotify(query):
    results = sp.search(q=query, type="track", limit=1)
    tracks = results["tracks"]["items"]
    if not tracks:
        return None
    track = tracks[0]
    return {
        "title": track["name"],
        "artist": track["artists"][0]["name"],
        "cover_url": track["album"]["images"][0]["url"],
    }

def download_audio(query):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "track.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"ytsearch1:{query}"])
    return "track.mp3"

async def handle_message(update, context):
    query = update.message.text.strip()
    await update.message.reply_text(f"🔍 Ищу: {query}...")

    meta = search_spotify(query)
    if not meta:
        await update.message.reply_text("❌ Не найдено на Spotify")
        return

    full_title = f"{meta['artist']} – {meta['title']}"
    await update.message.reply_text(f"✅ {full_title}\n⬇️ Скачиваю...")

    audio_path = download_audio(full_title)

    img_data = requests.get(meta["cover_url"]).content
    with open("cover.jpg", "wb") as f:
        f.write(img_data)

    with open("cover.jpg", "rb") as photo:
        await context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=photo,
            caption=f"🎧 {full_title}"
        )
    with open(audio_path, "rb") as audio:
        await context.bot.send_audio(
            chat_id=CHANNEL_ID,
            audio=audio,
            title=meta["title"],
            performer=meta["artist"],
        )

    await update.message.reply_text("✅ Отправлено в канал!")
    os.remove(audio_path)
    os.remove("cover.jpg")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
