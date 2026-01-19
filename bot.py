import telebot
from telebot import types
import yt_dlp
import os
import re
import time

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8483257931:AAHk9MzXEk6awPDTLA5wIZXRpDEwI3tfHs0")
bot = telebot.TeleBot(BOT_TOKEN)

def detect_instagram_url(text):
    insta_regex = r'(https?://(?:www\.)?instagram\.com/(?:reel|p|tv)/[\w/-]+)'
    match = re.search(insta_regex, text)
    return match.group() if match else None

def download_instagram_reel(url):
    timestamp = str(int(time.time()))
    
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
    
    try:
        os.makedirs('downloads', exist_ok=True)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading Instagram reel: {url}")
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Instagram Reel')
            filename = ydl.prepare_filename(info)
            
            if not os.path.exists(filename):
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
        print(f"Instagram download error: {e}")
        import traceback
        traceback.print_exc()
        return None, None

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('📥 Download Instagram Reel'))
    markup.add(types.KeyboardButton('ℹ️ Help'))
    
    welcome_text = (
        "🎬 *Instagram Reels Downloader Bot*\n\n"
        "Download Instagram Reels easily and quickly!\n\n"
        "Just send me an Instagram reel link and I'll download it for you.\n\n"
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
        "📎 Please send Instagram Reel link!\n\n"
        "Example: https://www.instagram.com/reel/xyz123/"
    )

@bot.message_handler(func=lambda msg: msg.text and 'Help' in msg.text)
def help_menu(message):
    help_text = """
🎬 *Instagram Reels Downloader Bot*

*How to Use:*
1. Press /start
2. Click 📥 Download Instagram Reel button
3. Send Instagram Reel link
4. Get your video!

*Supported Links:*
✅ instagram.com/reel/...
✅ instagram.com/p/...

*Features:*
• Fast Download Speed
• High Quality Videos
• Easy to Use
• Free Service

*Note:* Private account reels cannot be downloaded.

📢 *Powered by:* @CROFON
💬 *Support:* @CROFONCHAT
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
    
    url = detect_instagram_url(message.text)
    
    if not url:
        bot.reply_to(
            message, 
            "❌ Please send a valid Instagram Reel link!\n\n"
            "Example: https://www.instagram.com/reel/xyz123/"
        )
        return
    
    status = bot.reply_to(message, "⏳ Downloading... Please wait.")
    
    try:
        filename, title = download_instagram_reel(url)
        
        if filename and os.path.exists(filename):
            try:
                bot.edit_message_text("📤 Uploading...", message.chat.id, status.message_id)
                
                file_size = os.path.getsize(filename)
                print(f"File size: {file_size / (1024*1024):.2f} MB")
                
                if file_size > 50 * 1024 * 1024:
                    bot.edit_message_text(
                        "❌ File is too large (>50MB).\n"
                        "Telegram has a 50MB upload limit.", 
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
                print("Instagram reel sent successfully!")
                
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
                "❌ Download failed!\n\n"
                "*Possible Reasons:*\n"
                "• Video is private\n"
                "• Invalid link\n"
                "• Account is private\n"
                "• Network issue\n\n"
                "Please try again or contact @CROFONCHAT", 
                message.chat.id, 
                status.message_id,
                parse_mode='Markdown'
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
    print("🎬 Instagram Reels Downloader Bot Starting...")
    print(f"Python version: {os.sys.version}")
    print(f"Working directory: {os.getcwd()}")
    bot.polling(none_stop=True, interval=0, timeout=20)
