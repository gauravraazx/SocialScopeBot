import telebot
from telebot import types
import yt_dlp
import instaloader
import os
import re

BOT_TOKEN = "8483257931:AAFuMKgJO8V6nPpbGB5foCdBZiLBaMirdeQ"
bot = telebot.TeleBot(BOT_TOKEN)

def detect_url(text):
    youtube_regex = r'(https?://(?:www\.)?(?:youtube\.com/(?:watch|shorts|reel)|youtu\.be/)[\w=/?&-]+)'
    insta_regex = r'(https?://(?:www\.)?instagram\.com/(?:reel|p)/[\w/-]+)'
    yt = re.search(youtube_regex, text)
    ig = re.search(insta_regex, text)
    if yt:
        return 'youtube', yt.group()
    elif ig:
        return 'instagram', ig.group()
    else:
        return None, None

def download_instagram(url):
    try:
        L = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False
        )
        
        # Extract shortcode from URL
        shortcode = url.split('/')[-2] if url.split('/')[-1] == '' else url.split('/')[-1]
        shortcode = shortcode.split('?')[0]  # Remove query parameters
        
        # Get post
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        # Download
        L.download_post(post, target='temp_insta')
        
        # Find video file
        video_file = None
        for file in os.listdir('temp_insta'):
            if file.endswith('.mp4'):
                video_file = os.path.join('temp_insta', file)
                break
        
        if video_file:
            # Rename to simple name
            new_name = f"{shortcode}.mp4"
            os.rename(video_file, new_name)
            
            # Clean up other files
            for file in os.listdir('temp_insta'):
                try:
                    os.remove(os.path.join('temp_insta', file))
                except:
                    pass
            try:
                os.rmdir('temp_insta')
            except:
                pass
            
            return new_name, post.caption[:100] if post.caption else "Instagram Reel"
        
        return None, None
        
    except Exception as e:
        print(f"Instagram download error: {e}")
        # Cleanup on error
        try:
            if os.path.exists('temp_insta'):
                for file in os.listdir('temp_insta'):
                    try:
                        os.remove(os.path.join('temp_insta', file))
                    except:
                        pass
                os.rmdir('temp_insta')
        except:
            pass
        return None, None

def download_youtube(url):
    ydl_opts = {
        'format': 'best[height<=720]',
        'outtmpl': '%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'YouTube Video')
            filename = ydl.prepare_filename(info)
            # Ensure .mp4 extension
            if not filename.endswith('.mp4'):
                base = os.path.splitext(filename)[0]
                filename = base + '.mp4'
            return filename, title
    except Exception as e:
        print(f"YouTube download error: {e}")
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
Fast downloader powered by instaloader & yt-dlp

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
    
    # Download based on platform
    if platform == 'instagram':
        filename, title = download_instagram(url)
    else:  # youtube
        filename, title = download_youtube(url)
    
    if filename and os.path.exists(filename):
        try:
            bot.edit_message_text("📤 Uploading...", message.chat.id, status.message_id)
            
            with open(filename, 'rb') as video:
                caption = (
                    f"✅ *{title}*\n\n"
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
                "❌ Upload failed. File might be too large.", 
                message.chat.id, 
                status.message_id
            )
            if os.path.exists(filename):
                os.remove(filename)
    else:
        bot.edit_message_text(
            "❌ Download failed. Please check:\n"
            "• Link is correct\n"
            "• Account is not private\n"
            "• Video still exists", 
            message.chat.id, 
            status.message_id
        )

if __name__ == '__main__':
    print("🤖 Bot is starting...")
    bot.polling(none_stop=True, interval=0, timeout=20)
