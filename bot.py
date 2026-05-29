import os, yt_dlp, requests
from telegram.ext import Application, MessageHandler, filters

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

def search_and_download(query):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "track.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "default_search": "scsearch",  # SoundCloud поиск
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"scsearch1:{query}", download=True)
        if not info or not info.get("entries"):
            return None
        entry = info["entries"][0]
        return {
            "title": entry.get("title", query),
            "artist": entry.get("uploader", "Unknown"),
            "cover_url": entry.get("thumbnail", None),
        }

async def handle_message(update, context):
    query = update.message.text.strip()
    await update.message.reply_text(f"🔍 Ищу: {query}...")

    try:
        meta = search_and_download(query)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
        return

    if not meta:
        await update.message.reply_text("❌ Трек не найден")
        return

    await update.message.reply_text(f"✅ {meta['title']}\n📤 Отправляю в канал...")

    # Обложка
    if meta["cover_url"]:
        try:
            img_data = requests.get(meta["cover_url"]).content
            with open("cover.jpg", "wb") as f:
                f.write(img_data)
            with open("cover.jpg", "rb") as photo:
                await context.bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=photo,
                    caption=f"🎧 {meta['title']}"
                )
            os.remove("cover.jpg")
        except:
            pass

    # Аудио
    with open("track.mp3", "rb") as audio:
        await context.bot.send_audio(
            chat_id=CHANNEL_ID,
            audio=audio,
            title=meta["title"],
            performer=meta["artist"],
        )

    os.remove("track.mp3")
    await update.message.reply_text("✅ Готово!")

app = Application.builder().token(BOT_TOKEN).build()
ydl_opts = {
    "format": "bestaudio/best",
    "outtmpl": "track.%(ext)s",
    "quiet": True,
    "no_warnings": True,
    "default_search": "scsearch",
    "ffmpeg_location": "/usr/bin/ffmpeg",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }],
}
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
