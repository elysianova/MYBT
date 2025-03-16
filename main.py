import os
import shutil
import logging
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import yt_dlp

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(name)

def start(update, context):
    update.message.reply_text(
        "Hello! Send me a YouTube link, and I'll convert it to a high-quality MP3 for you. This bot was created by @DIGITE_ME."
    )

def download_audio(url):
    # Find ffmpeg path
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        logger.error("FFmpeg not found. Please install it.")
        raise Exception("FFmpeg not found. Please install it.")

    logger.info(f"Using FFmpeg at: {ffmpeg_path}")

    # Extract video info (title)
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)  # Get video metadata
        video_title = info.get('title', 'unknown_song')  # Get the title, fallback to 'unknown_song'

    # Clean the title to be a valid filename
    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in video_title)

    # Define filename without extension
    output_path_no_ext = f"{safe_title}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path_no_ext,  # No .mp3 extension here
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'ffmpeg_location': ffmpeg_path,
        'quiet': False,  # Show yt-dlp logs
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        logger.error(f"yt-dlp failed: {e}")
        raise

    # Since yt-dlp appends '.mp3' automatically, check for the final file
    mp3_filename = output_path_no_ext + ".mp3"
    if os.path.exists(mp3_filename):
        logger.info(f"File created successfully: {mp3_filename}")
        return mp3_filename
    else:
        logger.error(f"File was not created: {mp3_filename}")
        raise Exception("File was not created.")

def handle_message(update, context):
    text = update.message.text.strip()
    if "youtube.com" in text or "youtu.be" in text:
        update.message.reply_text("Processing your YouTube link, please wait...")

        try:
            final_filename = download_audio(text)

            if os.path.exists(final_filename):
                with open(final_filename, 'rb') as audio_file:
                    update.message.reply_audio(audio=audio_file)
                os.remove(final_filename)
            else:
                update.message.reply_text("Error: File was not created.")
                logger.error(f"File was not found: {final_filename}")

        except Exception as e:
            logger.error(f"Error processing video: {e}")
            update.message.reply_text("Sorry, there was an error processing your request.")
    else:
        update.message.reply_text("Please send a valid YouTube link.")

def main():
    TOKEN = "8187797805:AAH_ZvZcd_uqFBxQgCXD6XfWHwoAJjcehXc"  # Replace with your bot token
    if not TOKEN:
        logger.error("BOT_TOKEN environment variable not set")
        return

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if name == 'main':
    main()
