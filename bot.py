import os, yt_dlp, requests
from telegram.ext import Application, MessageHandler, filters

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

def search_track(query):
    """Ищет трек на YouTube и берёт метаданные"""
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=False)
        if not info or not info.get("entries"):
            return None
        entry = info["entries"][0]
        
        # Пробуем получить обложку
        thumbnail = entry.get("thumbnail", "")
        
        # Артист и название
        title = entry.get("title", query)
        channel = entry.get("channel", "Unknown")
        
        return {
            "title": title,
            "artist": channel,
            "cover_url": thumbnail,
            "webpage_url": entry.get("webpage_url", ""),
        }

def download_audio(url, output_path="track"):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path + ".%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path + ".mp3"

async def handle_message(update, context):
    query = update.message.text.strip()
    await update.message.reply_text(f"🔍 Ищу: {query}...")

    meta = search_track(query)
    if not meta:
        await update.message.reply_text("❌ Трек не найден")
        return

    await update.message.reply_text(f"✅ {meta['title']}\n⬇️ Скачиваю...")

    audio_path = download_audio(meta["webpage_url"])

    # Скачиваем обложку
    try:
        img_data = requests.get(meta["cover_url"]).content
        with open("cover.jpg", "wb") as f:
            f.write(img_data)
        has_cover = True
    except:
        has_cover = False

    caption = f"🎧 {meta['title']}"

    if has_cover:
        with open("cover.jpg", "rb") as photo:
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo,
                caption=caption
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
    if has_cover:
        os.remove("cover.jpg")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
