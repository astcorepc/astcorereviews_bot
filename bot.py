import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

logging.basicConfig(level=logging.INFO)

def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("⭐ Оставить отзыв", callback_data="review")],
        [InlineKeyboardButton("🛠 Поддержка и гарантия", callback_data="support")],
        [InlineKeyboardButton("📢 Наш Telegram-канал", url="https://t.me/ваш_канал")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💻 **Добро пожаловать в AST CORE ПК!**\n\n"
        "Мы ценим каждого клиента. Расскажите о своем опыте или задайте вопрос.",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "review":
        context.user_data['waiting_for_review'] = True
        await query.edit_message_text(
            "✍️ **Напишите ваш отзыв одним сообщением.**\n\n"
            "Расскажите:\n"
            "• Как прошла покупка?\n"
            "• Как показал себя ПК?\n"
            "• Что понравилось / что улучшить?\n\n"
            "Спасибо за честность! 🙏",
            parse_mode="Markdown"
        )

    elif query.data == "support":
        await query.edit_message_text(
            "🛠 **Поддержка и гарантия**\n\n"
            "• По вопросам гарантии пишите сюда: @ваш_менеджер\n"
            "• Или на почту: support@astcore.ru\n"
            "• Мы на связи ежедневно с 10:00 до 22:00 ⚡",
            parse_mode="Markdown"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if context.user_data.get('waiting_for_review'):
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 **Новый отзыв!**\n\n"
                 f"👤 @{user.username} (ID: {user.id})\n"
                 f"📝 Текст:\n{text}"
        )

        await update.message.reply_text(
            "✅ **Спасибо за ваш отзыв!**\n\n"
            "Он очень важен для нас и поможет стать лучше. ❤️\n"
            "Вернуться в меню: /start",
            parse_mode="Markdown"
        )
        context.user_data['waiting_for_review'] = False

    else:
        await update.message.reply_text(
            "Используйте кнопки меню или /start",
            reply_markup=main_keyboard()
        )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
