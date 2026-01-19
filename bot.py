import telebot
from telebot import types
import yt_dlp
import os
import re
import time

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8483257931:AAFuMKgJO8V6nPpbGB5foCdBZiLBaMirdeQ")
bot = telebot.TeleBot(BOT_TOKEN)

def detect_url(text):
    youtube_regex = r'(https?://(?:www\.)?(?:youtube\.com/(?:watch|shorts|reel)|youtu\.be/)[\w=/?&-]+)'
    insta_regex = r'(https?://(?:www\.)?instagram\.com/(?:reel|p|tv)/[\w/-]+)'
    yt = re.search(youtube_regex, text)
    ig = re.search(insta_regex, text)
    if yt:
        return 'youtube', yt.group()
    elif ig:
        return 'instagram', ig.group()
    else:
        return None, None

def download_video(url, platform):
    timestamp = str(int(time.time()))
    
    if platform == 'instagram':
        ydl_opts = {
            'format': 'best',
            'outtmpl': f'downloads/{timestamp}.%(ext)s',
            'quiet': False,
            'no_warnings': False,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'prefer_ffmpeg': False,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
            },
            'extractor_retries': 3,
            'socket_timeout': 30,
        }
    else:
        ydl_opts = {
            'format': 'best[height<=480]/worst',
            'outtmpl': f'downloads/{timestamp}.%(ext)s',
            'quiet': False,
            'no_warnings': False,
            'prefer_ffmpeg': False,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'extractor_retries': 3,
            'socket_timeout': 30,
        }
    
    try:
        # Create downloads folder
        os.makedirs('downloads', exist_ok=True)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading from {platform}: {url}")
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Video')
            filename = ydl.prepare_filename(info)
            
            # Check if file exists
            if not os.path.exists(filename):
                # Try to find any file with timestamp
                for file in os.listdir('downloads'):
                    if file.startswith(timestamp):
                        filename = os.path.join('downloads', file)
                        break
            
            if os.path.exists(filename):
                print(f"Downloaded: {filename}")
                return filename, title
            else:
                print("File not found after download")
                return None, None
            
    except Exception as e:
        print(f"{platform.capitalize()} download error: {e}")
        import traceback
        traceback.print_exc()
        return None, None

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('📥 Download Reels'))
    markup.add(types.KeyboardButton('ℹ️ Help'))
    
    welcome_text = (
        "🤖 *CROFON Reels Downloader* activated!\n\n"
        "Send Instagram Reel or YouTube Short/Video link, I'll download it for you.\n\n"
        "📢 *Powered by:* @CROFON\n"
        "💬 *Support:* @CROFONCHAT"
    )
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        reply_markup=markup, 
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda msg: msg.text and 'Download' in msg.text)
def download_prompt(message):
    bot.send_message(
        message.chat.id, 
        "📎 Please send Instagram Reel or YouTube Short/Video link!"
    )

@bot.message_handler(func=lambda msg: msg.text and 'Help' in msg.text)
def help_menu(message):
    help_text = """
🤖 *CROFON Reels Downloader Bot*

*Steps:*
1. Press /start
2. Click 📥 Download Reels button
3. Paste Instagram Reel or YouTube Short link
4. Get your video!

*Supported Platforms:*
✅ Instagram Reels/Posts/Videos
✅ YouTube Shorts/Videos

*About:*
Fast downloader powered by yt-dlp

*Powered by:* @CROFON
*Support:* @CROFONCHAT
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Channel", url="https://t.me/CROFON"))
    markup.add(types.InlineKeyboardButton("💬 Support", url="https://t.me/CROFONCHAT"))
    
    bot.send_message(
        message.chat.id, 
        help_text, 
        parse_mode='Markdown', 
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not message.text:
        return
    
    platform, url = detect_url(message.text)
    
    if not platform:
        bot.reply_to(message, "❌ Please send a valid Instagram or YouTube link!")
        return
    
    status = bot.reply_to(message, "⏳ Downloading... Please wait.")
    
    try:
        filename, title = download_video(url, platform)
        
        if filename and os.path.exists(filename):
            try:
                bot.edit_message_text("📤 Uploading...", message.chat.id, status.message_id)
                
                file_size = os.path.getsize(filename)
                print(f"File size: {file_size / (1024*1024):.2f} MB")
                
                if file_size > 50 * 1024 * 1024:
                    bot.edit_message_text(
                        "❌ File is too large (>50MB). Telegram has upload limits.", 
                        message.chat.id, 
                        status.message_id
                    )
                    os.remove(filename)
                    return
                
                with open(filename, 'rb') as video:
                    caption = (
                        f"✅ *{title[:100]}*\n\n"
                        f"📢 *Powered by:* @CROFON\n"
                        f"💬 *Support:* @CROFONCHAT"
                    )
                    bot.send_video(
                        message.chat.id, 
                        video, 
                        caption=caption,
                        parse_mode='Markdown',
                        timeout=180
                    )
                
                bot.delete_message(message.chat.id, status.message_id)
                os.remove(filename)
                print("Video sent successfully!")
                
            except Exception as e:
                print(f"Upload error: {e}")
                import traceback
                traceback.print_exc()
                bot.edit_message_text(
                    "❌ Upload failed. Please try again.", 
                    message.chat.id, 
                    status.message_id
                )
                if os.path.exists(filename):
                    os.remove(filename)
        else:
            bot.edit_message_text(
                "❌ Download failed. Possible reasons:\n"
                "• Video is private\n"
                "• Invalid link\n"
                "• Server issue\n\n"
                "Try again or contact @CROFONCHAT", 
                message.chat.id, 
                status.message_id
            )
    except Exception as e:
        print(f"Handler error: {e}")
        import traceback
        traceback.print_exc()
        bot.edit_message_text(
            "❌ Something went wrong. Please try again.", 
            message.chat.id, 
            status.message_id
        )

if __name__ == '__main__':
    print("🤖 Bot is starting...")
    print(f"Python version: {os.sys.version}")
    print(f"Working directory: {os.getcwd()}")
    bot.polling(none_stop=True, interval=0, timeout=20)
