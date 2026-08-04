import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# === НАСТРОЙКИ (переменные из Railway) ===
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = os.getenv("CHANNEL_ID")

logging.basicConfig(level=logging.INFO)

# === Главное меню ===
def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("⭐ Подать отзыв", callback_data="review")],
        [InlineKeyboardButton("🛠 Поддержка", callback_data="support")],
        [InlineKeyboardButton("📢 Наш канал", url="https://t.me/ваш_канал")]
    ]
    return InlineKeyboardMarkup(keyboard)

# === Клавиатура для выбора звезд ===
def stars_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("1 ⭐", callback_data="star_1"),
            InlineKeyboardButton("2 ⭐", callback_data="star_2"),
            InlineKeyboardButton("3 ⭐", callback_data="star_3")
        ],
        [
            InlineKeyboardButton("4 ⭐", callback_data="star_4"),
            InlineKeyboardButton("5 ⭐", callback_data="star_5")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# === Команда /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💻 **Добро пожаловать в AST CORE ПК!**\n\n"
        "Нажмите кнопку, чтобы оставить отзыв о нашем сервисе.",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

# === Обработка кнопок (выбор звезд) ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "review":
        await query.edit_message_text(
            "⭐ **Оцените нашу работу от 1 до 5:**\n\n"
            "Выберите количество звезд:",
            reply_markup=stars_keyboard(),
            parse_mode="Markdown"
        )

    elif query.data.startswith("star_"):
        stars = int(query.data.split("_")[1])
        context.user_data['review_rating'] = stars
        context.user_data['waiting_for_review'] = True

        if stars == 1:
            stars_text = "звезда"
        elif 2 <= stars <= 4:
            stars_text = "звезды"
        else:
            stars_text = "звезд"

        await query.edit_message_text(
            f"✅ **Вы выбрали {stars} {stars_text}**\n\n"
            "✍️ Теперь **напишите ваш отзыв** одним сообщением.\n\n"
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
            "По любым вопросам пишите:\n"
            "@ваш_менеджер\n\n"
            "Мы на связи ежедневно с 10:00 до 22:00 ⚡",
            parse_mode="Markdown"
        )

# === Приём текста и отправка админу ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if context.user_data.get('waiting_for_review'):
        rating = context.user_data.get('review_rating', 5)
        stars_symbols = "⭐" * rating

        # Сохраняем данные
        context.user_data['pending_review'] = text
        context.user_data['review_author_username'] = user.username
        context.user_data['review_author_fullname'] = user.full_name

        keyboard = [
            [
                InlineKeyboardButton("✅ Опубликовать", callback_data="publish"),
                InlineKeyboardButton("❌ Отклонить", callback_data="reject")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправляем админу
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 **Новый отзыв на модерацию**\n\n"
                 f"👤 @{user.username} (ID: {user.id})\n"
                 f"⭐ Оценка: {stars_symbols} ({rating}/5)\n"
                 f"📝 Текст:\n{text}",
            reply_markup=reply_markup
        )

        # Ответ пользователю
        await update.message.reply_text(
            "✅ **Спасибо за ваш отзыв!**\n\n"
            "Он отправлен на модерацию. После проверки мы опубликуем его в нашем канале. ❤️",
            parse_mode="Markdown"
        )
        
        context.user_data['waiting_for_review'] = False

    else:
        await update.message.reply_text(
            "Используйте кнопку /start в меню, чтобы начать.",
            reply_markup=main_keyboard()
        )

# === Обработка действий админа (публикация) ===
async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Парсим сообщение админа
    full_text = query.message.text
    lines = full_text.split("\n")
    
    # Ищем юзера
    username_line = ""
    for line in lines:
        if line.startswith("👤"):
            username_line = line
            break
    
    username = "Пользователь"
    if "@" in username_line:
        username = username_line.split("@")[1].split()[0]
        username = f"@{username}"
    
    # Ищем оценку (звезды и дробь)
    stars_symbols = ""
    rating_count = 5 # по умолчанию
    for line in lines:
        if line.startswith("⭐ Оценка:"):
            parts = line.split(":")[1].strip().split()
            if parts:
                stars_symbols = parts[0] # забираем звезды
                for part in parts:
                    if part.startswith("(") and part.endswith(")"):
                        rating_count = part
                        break
            break
    
    if rating_count == 5 and stars_symbols:
        rating_count = f"({len(stars_symbols)}/5)"

    # Ищем текст отзыва
    review_body = "Текст не указан"
    for i, line in enumerate(lines):
        if line.startswith("📝 Текст:"):
            review_body = line.replace("📝 Текст:", "").strip()
            if i + 1 < len(lines):
                review_body += "\n" + "\n".join(lines[i+1:])
            break

    if query.data == "publish":
        if CHANNEL_ID:
            # ПУБЛИКАЦИЯ БЕЗ ЖИРНОГО ШРИФТА, С НУЖНЫМИ ЭМОДЗИ
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"📖 Новый Отзыв\n\n"
                     f"⭐ Оценка: {stars_symbols} {rating_count}\n\n"
                     f"👤 {username}\n\n"
                     f"📝 {review_body}"
            )
            
            await query.edit_message_text(
                text="✅ **Отзыв опубликован в канале!**"
            )
        else:
            await query.edit_message_text(
                text="⚠️ Канал не настроен. Добавь переменную CHANNEL_ID в Railway."
            )

    elif query.data == "reject":
        await query.edit_message_text(
            text="❌ **Отзыв отклонён**"
        )

# === Запуск ===
def main():
    app = Application.builder().token(TOKEN).build()

    # Кнопка "Меню"
    async def post_init(application):
        await application.bot.set_my_commands([
            BotCommand("start", "Показать главное меню")
        ])
    app.post_init = post_init

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(review|support|star_\\d+)$"))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^(publish|reject)$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.add_error_handler(error_handler)

    print("✅ Бот запущен и готов к работе!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"💥 ОШИБКА В БОТЕ: {context.error}")
    import traceback
    traceback.print_exc()

if __name__ == "__main__":
    main()
