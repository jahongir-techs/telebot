import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
import requests
import logging
import os
from flask import Flask, request

# Logging sozlamalari: batafsil loglar uchun
logging.basicConfig(level=logging.INFO)  # Production uchun INFO levelga o'tkazdim, debug uchun DEBUG qilishingiz mumkin

# Environment variables orqali конфигурация (mukammal va xavfsizroq)
# Masalan, Heroku yoki VPS da os.environ orqali o'rnating
CHANNEL_USERNAME = os.environ.get('CHANNEL_USERNAME', '@havolardf')
CONTESTS_URL = os.environ.get('CONTESTS_URL', 'https://raw.githubusercontent.com/USERNAME/REPO/main/contests.json')  # Real URL bilan almashtiring
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7897761159:AAFkmR8-RKnHD1kn2p-Va7ZSjaC5uyeBcps')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', "https://havolalardfbot.onrender.com")  # Masalan: 'https://your-app-name.herokuapp.com/webhook' – deployment da o'rnating
PORT = int(os.environ.get('PORT', 5000))  # Heroku uchun PORT env var

if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL environment variable not set! Deployment uchun kerak.")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Flask app webhook uchun
app = Flask(__name__)

# Webhook endpoint
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return '', 200
        else:
            return 'Unsupported Media Type', 415
    return 'OK', 200  # GET uchun Telegram webhookni tasdiqlash

# 🔹 /start komandasi: avtomatik obuna tekshirish
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    try:
        logging.info(f"Checking membership for user {user_id} in channel {CHANNEL_USERNAME}")
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        logging.info(f"Member status: {member.status}")

        if member.status in ["member", "administrator", "creator"]:
            # Obuna bo'lgan – menyu ko'rsatish
            markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add("🏆 Contests", "🎯 Ishtirok etish", "📜 Terms")

            bot.send_message(
                message.chat.id,
                f"Assalomu alaykum, {message.from_user.first_name} 👋\n\n"
                f"Pastdagi menyulardan birini tanlang:",
                reply_markup=markup
            )
        else:
            # Obuna bo'lmagan – obuna bo'lishni talab qilish
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"))

            bot.send_message(
                message.chat.id,
                "❌ Siz hali kanalga obuna bo‘lmagansiz.\n\n"
                "Iltimos, botimizdan to'liq foydalanish uchun "
                "quyidagi kanalga obuna bo‘ling va keyin /start ni qayta bosing:",
                reply_markup=keyboard
            )

    except telebot.Exception as e:  # telebot xatolarini maxsus tutish
        logging.error(f"Telebot error in start: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Qayta urinib ko‘ring yoki admin bilan bog‘laning.")
    except Exception as e:
        logging.error(f"Unexpected error in start: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Qayta urinib ko‘ring yoki admin bilan bog‘laning.")

# 🔹 /getchannelid – debug uchun (production da o'chirib qo'yishingiz mumkin)
@bot.message_handler(commands=["getchannelid"])
def getchannelid(message):
    try:
        logging.info("Getting channel info...")
        chat = bot.get_chat(CHANNEL_USERNAME)
        id_msg = f"Channel ID: {chat.id}"
        logging.info(id_msg)
        bot.send_message(message.chat.id, id_msg)
    except Exception as e:
        error_msg = f"Xatolik: {str(e)}"
        logging.error(error_msg)
        bot.send_message(message.chat.id, error_msg)

# 🔹 Contests menyusi
@bot.message_handler(func=lambda m: m.text == "🏆 Contests")
def contests(message):
    try:
        r = requests.get(CONTESTS_URL, timeout=10)  # Timeout qo'shdim, network muammolari uchun
        if r.status_code != 200:
            bot.send_message(message.chat.id, "⚠️ Tanlovlar ro‘yxatini yuklab bo‘lmadi.")
            return

        data = r.json()
        if not data:
            bot.send_message(message.chat.id, "📭 Hozircha faol tanlovlar yo‘q.")
            return

        msg = "🏆 Hozirda faol tanlovlar:\n\n"
        for contest in data:
            msg += (
                f"📌 <b>{contest.get('title', 'Noma’lum')}</b>\n"
                f"{contest.get('description', '')}\n"
                f"🗓️ Muddat: {contest.get('deadline', 'Noma’lum')}\n"
                f"🎁 Sovrin: {contest.get('prize', 'Noma’lum')}\n\n"
            )  # .get() qo'shdim, agar key bo'lmasa crash bo'lmasligi uchun

        bot.send_message(message.chat.id, msg)
    except requests.RequestException as e:
        logging.error(f"Requests error in contests: {e}")
        bot.send_message(message.chat.id, "❌ Ma’lumotlarni olishda xatolik yuz berdi (network muammosi).")
    except ValueError as e:  # JSON decode error
        logging.error(f"JSON error in contests: {e}")
        bot.send_message(message.chat.id, "❌ Ma’lumotlarni olishda xatolik yuz berdi (JSON formati noto'g'ri).")
    except Exception as e:
        logging.error(f"Unexpected error in contests: {e}")
        bot.send_message(message.chat.id, "❌ Ma’lumotlarni olishda xatolik yuz berdi.")

# 🔹 Ishtirok etish
@bot.message_handler(func=lambda m: m.text == "🎯 Ishtirok etish")
def participate(message):
    bot.send_message(
        message.chat.id,
        "🎯 Ishtirok etish uchun quyidagilarni bajaring:\n\n"
        "1️⃣ Kanalga obuna bo‘ling ✅\n"
        "2️⃣ Postlarni do‘stlaringiz bilan ulashing 📢\n"
        "3️⃣ Ismingizni va username’ingizni yuboring 📩\n\n"
        "Biz siz bilan bog‘lanamiz!"
    )

# 🔹 Terms
@bot.message_handler(func=lambda m: m.text == "📜 Terms")
def terms(message):
    bot.send_message(
        message.chat.id,
        "📜 Tanlov shartlari:\n\n"
        "• Faqat kanal obunachilari ishtirok etadi.\n"
        "• Har bir foydalanuvchi faqat bitta ishtirok huquqiga ega.\n"
        "• G‘oliblar adolatli tanlov asosida aniqlanadi.\n"
        "• Natijalar kanal orqali e’lon qilinadi 🏁"
    )

# Barcha boshqa xabarlar uchun (mukammallik uchun: spam oldini olish)
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Iltimos, menyudan foydalaning yoki /start ni bosing.")

# Webhookni sozlash
if __name__ == '__main__':
    logging.info("Setting up webhook...")
    bot.remove_webhook()  # Old webhookni o'chirish
    bot.set_webhook(url=WEBHOOK_URL)
    logging.info(f"Webhook set to {WEBHOOK_URL}")
    app.run(host='0.0.0.0', port=PORT, debug=False)  # Production uchun debug=False