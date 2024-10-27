import telebot
from telebot import types
import yt_dlp
import time

# Replace with your actual bot token and channel username
BOT_TOKEN = "6108327795:AAEO9RyKWl3OViBLicHB4tB0duS0QsLz-Ss"  # Replace with your bot token
CHANNEL_USERNAME = "Virtex_offical"  # Replace with your channel username

bot = telebot.TeleBot(BOT_TOKEN)

# Function to check if a user is subscribed to the channel
def is_member(user_id):
    try:
        member_status = bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
        print(f"User  {user_id} status: {member_status.status}")  # Debug line
        return member_status.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Error checking membership: {e}")
        return False

@bot.message_handler(commands=['start'])
def start(message):
    if is_member(message.from_user.id):
        bot.send_message(message.chat.id, "You're already a member! Send me a YouTube link to download.")
    else:
        markup = types.InlineKeyboardMarkup()
        join_button = types.InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")
        confirm_button = types.InlineKeyboardButton("Confirm", callback_data="check_membership")
        markup.add(join_button, confirm_button)
        bot.send_message(message.chat.id, "Please join our channel to use the bot:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_membership")
def callback_check_membership(call):
    if is_member(call.from_user.id):
        bot.edit_message_text("Great! You've joined the channel. Now you can send me YouTube links to download.",
                              chat_id=call.message.chat.id, message_id=call.message.message_id)
        start(call.message)  # Call the start function again
    else:
        bot.answer_callback_query(call.id, "You haven't joined the channel yet. Please join and try again.")

@bot.message_handler(func=lambda message: 'youtube.com' in message.text or 'youtu.be' in message.text)
def handle_youtube_link(message):
    if not is_member(message.from_user.id):
        start(message)
        return

    url = message.text
    bot.send_message(message.chat.id, "Please wait while I process the video link...")
    try:
        ydl_opts = {}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            print(f"Extracted info: {info}")  # Debug logging
            resolutions = ["144p", "240p", "360p", "480p", "720p", "1080p"]
            available_resolutions = [res for res in resolutions if any(stream['resolution'] == res for stream in info['formats'])]
            print(f"Available resolutions: {available_resolutions}")  # Debug logging

            if available_resolutions:
                markup = types.InlineKeyboardMarkup()
                for res in available_resolutions:
                    markup.add(types.InlineKeyboardButton(res, callback_data=f"download_{res}_{url}"))
                bot.send_message(message.chat.id, "Choose video quality:", reply_markup=markup)
            else:
                ydl_opts = {'format': 'best'}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                bot.send_message(message.chat.id, "Downloading video in full quality...")
                filename = ydl.prepare_filename(info)
                with open(filename, 'rb') as video_file: 
                    bot.send_video(message.chat.id, video_file, supports_streaming=True,
                                   caption=f"Downloaded video: {info['title']}")

    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("download_"))
def callback_download_video(call):
    data = call.data.split("_")
    resolution = data[1]
    url = "_".join(data[2:])  # Reconstruct the URL

    try:
        ydl_opts = {'format': f'bestvideo[height={resolution}]'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        bot.send_message(call.message.chat.id, f"Downloading video in {resolution}...")

        # Send the downloaded video using the correct filename
        filename = ydl.prepare_filename(info)
        with open(filename, 'rb') as video_file: 
                        bot.send_video(call.message.chat.id, video_file, supports_streaming=True,
                           caption=f"Downloaded video: {info['title']}")

    except Exception as e:
        bot.send_message(call.message.chat.id, f"Error: {e}")

if __name__ == "__main__":
    bot.infinity_polling()