import aiohttp
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# 🔗 Kanal username (masalan, @kanal_nomi)
CHANNEL_USERNAME = "@sizning_kanalingiz"

# 🔗 GitHub’dagi JSON fayl manzili (raw formatda)
CONTESTS_URL = "https://raw.githubusercontent.com/USERNAME/REPO/main/contests.json"


# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 Kanalga o'tish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton("✅ Tekshirish", callback_data="check_subscription")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text="Iltimos, quyidagi kanalga obuna bo‘ling:",
        reply_markup=reply_markup
    )


# Obuna holatini tekshirish
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        status = member.status

        if status in ["member", "administrator", "creator"]:
            reply_keyboard = [
                ["🏆 Contests", "🎯 Ishtirok etish"],
                ["📜 Terms"]
            ]
            markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

            await query.message.reply_text(
                text=f"Assalomu alaykum, {query.from_user.first_name} 👋\n\n"
                     f"Pastdagi menyulardan birini tanlang:",
                reply_markup=markup
            )
        else:
            await query.message.reply_text(
                text="Siz hali kanalga obuna bo‘lmagansiz ❌. Iltimos, avval obuna bo‘ling."
            )

    except Exception as e:
        print("Xatolik:", e)
        await query.message.reply_text("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko‘ring.")


# 🏆 Contests menyusi — GitHub JSON’dan o‘qish
async def contests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(CONTESTS_URL) as response:
                if response.status == 200:
                    data = await response.json()
                else:
                    await update.message.reply_text("⚠️ Tanlovlar ro‘yxatini yuklab bo‘lmadi.")
                    return

        if not data:
            await update.message.reply_text("📭 Hozircha faol tanlovlar mavjud emas.")
            return

        message = "🏆 Hozirda faol tanlovlar:\n\n"
        for contest in data:
            message += (
                f"📌 <b>{contest['title']}</b>\n"
                f"{contest['description']}\n"
                f"🗓️ Muddat: {contest['deadline']}\n"
                f"🎁 Sovrin: {contest['prize']}\n\n"
            )

        await update.message.reply_html(message)

    except Exception as e:
        print("Xatolik:", e)
        await update.message.reply_text("❌ Ma’lumotlarni olishda xatolik yuz berdi.")


# 🎯 Ishtirok etish menyusi
async def participate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text="🎯 Ishtirok etish uchun quyidagi bosqichlarni bajaring:\n\n"
             "1️⃣ - Kanalga obuna bo‘ling ✅\n"
             "2️⃣ - Postlarni do‘stlaringiz bilan ulashing 📢\n"
             "3️⃣ - Ismingizni va foydalanuvchi nomingizni yuboring 📩\n\n"
             "Biz siz bilan bog‘lanamiz!"
    )


# 📜 Terms menyusi
async def terms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text="📜 Tanlov shartlari:\n\n"
             "• Faqat kanal obunachilari ishtirok etishi mumkin.\n"
             "• Har bir foydalanuvchi faqat bitta ishtirok huquqiga ega.\n"
             "• G‘oliblar adolatli tanlov asosida aniqlanadi.\n"
             "• Natijalar kanal orqali e’lon qilinadi 🏁"
    )


def main():
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN_HERE").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_subscription, pattern="check_subscription"))
    app.add_handler(MessageHandler(filters.Text("🏆 Contests"), contests))
    app.add_handler(MessageHandler(filters.Text("🎯 Ishtirok etish"), participate))
    app.add_handler(MessageHandler(filters.Text("📜 Terms"), terms))

    print("🤖 Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
