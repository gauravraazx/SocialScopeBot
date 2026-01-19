import telebot
from telebot import types
import yt_dlp
import os
import re

BOT_TOKEN = "8483257931:AAFuMKgJO8V6nPpbGB5foCdBZiLBaMirdeQ"
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
    # Instagram ke liye special options
    if platform == 'instagram':
        ydl_opts = {
            'format': 'best',
            'outtmpl': '%(id)s.%(ext)s',
            'quiet': False,
            'no_warnings': False,
            'cookiefile': None,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        }
    else:
        # YouTube ke liye options
        ydl_opts = {
            'format': 'best[height<=720]',
            'outtmpl': '%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
        }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading from {platform}: {url}")
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Video')
            filename = ydl.prepare_filename(info)
            
            # Ensure .mp4 extension
            if not filename.endswith('.mp4'):
                base = os.path.splitext(filename)[0]
                new_filename = base + '.mp4'
                if os.path.exists(filename):
                    os.rename(filename, new_filename)
                    filename = new_filename
            
            print(f"Downloaded: {filename}")
            return filename, title
            
    except Exception as e:
        print(f"{platform.capitalize()} download error: {e}")
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
    
    filename, title = download_video(url, platform)
    
    if filename and os.path.exists(filename):
        try:
            bot.edit_message_text("📤 Uploading...", message.chat.id, status.message_id)
            
            # Check file size
            file_size = os.path.getsize(filename)
            if file_size > 50 * 1024 * 1024:  # 50MB limit
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
                    timeout=120
                )
            
            bot.delete_message(message.chat.id, status.message_id)
            os.remove(filename)
            
        except Exception as e:
            print(f"Upload error: {e}")
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
            "• Network issue\n\n"
            "Try again or contact support.", 
            message.chat.id, 
            status.message_id
        )

if __name__ == '__main__':
    print("🤖 Bot is starting...")
    bot.polling(none_stop=True, interval=0, timeout=20)
