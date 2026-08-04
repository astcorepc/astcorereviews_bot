import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# === ПЕРЕМЕННЫЕ ИЗ RAILWAY ===
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = os.getenv("CHANNEL_ID")

logging.basicConfig(level=logging.INFO)

# === ГЛАВНОЕ МЕНЮ ===
def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("⭐ Подать отзыв", callback_data="review")],
        [InlineKeyboardButton("🛠 Поддержка и гарантия", callback_data="support")],
        [InlineKeyboardButton("📢 Наш Telegram-канал", url="https://t.me/ваш_канал")]
    ]
    return InlineKeyboardMarkup(keyboard)

# === КЛАВИАТУРА ДЛЯ ОЦЕНКИ (текстовые звёзды) ===
def rating_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("⭐ 1", callback_data="rate_1"),
            InlineKeyboardButton("⭐⭐ 2", callback_data="rate_2"),
            InlineKeyboardButton("⭐⭐⭐ 3", callback_data="rate_3"),
            InlineKeyboardButton("⭐⭐⭐⭐ 4", callback_data="rate_4"),
            InlineKeyboardButton("⭐⭐⭐⭐⭐ 5", callback_data="rate_5")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💻 **Добро пожаловать в AST CORE ПК!**\n\n"
        "Мы ценим каждого клиента. Расскажите о своем опыте или задайте вопрос.",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

# === ОБРАБОТКА КНОПОК ГЛАВНОГО МЕНЮ ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "review":
        await query.edit_message_text(
            "⭐ **Оцените нас от 1 до 5:**",
            reply_markup=rating_keyboard(),
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

# === ОБРАБОТКА ВЫБОРА ОЦЕНКИ ===
async def rating_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    rating = int(query.data.split("_")[1])
    context.user_data['rating'] = rating

    stars = "⭐" * rating

    await query.edit_message_text(
        f"📝 **Вы выбрали {stars}**\n\n"
        "Теперь напишите ваш отзыв текстом.\n"
        "Если хотите — приложите фото (одно).\n\n"
        "Просто отправьте сообщение с текстом и фото (если нужно).",
        parse_mode="Markdown"
    )
    context.user_data['waiting_for_review'] = True

# === ПРИЁМ СООБЩЕНИЙ (ТЕКСТ + ФОТО) ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Проверяем, есть ли текст
    text = update.message.text
    # Проверяем, есть ли фото (берём самое качественное)
    photo = update.message.photo[-1].file_id if update.message.photo else None

    # Если мы ждём отзыв
    if context.user_data.get('waiting_for_review'):
        # Если есть фото, но нет текста — просим написать текст
        if photo and not text:
            await update.message.reply_text(
                "📝 **Пожалуйста, напишите текст отзыва.**\n\n"
                "Вы можете отправить его вместе с фото.",
                parse_mode="Markdown"
            )
            return

        # Если нет ни текста, ни фото — игнорируем
        if not text and not photo:
            await update.message.reply_text(
                "Пожалуйста, напишите текст отзыва.",
                reply_markup=main_keyboard()
            )
            return

        # Сохраняем данные
        context.user_data['review_text'] = text or "Без текста"
        context.user_data['review_photo'] = photo
        context.user_data['review_author'] = user.id

        # Отправляем админу
        await send_to_admin(update, context)

        # Подтверждение пользователю
        await update.message.reply_text(
            "✅ **Спасибо за ваш отзыв!**\n\n"
            "Он отправлен на модерацию. После проверки мы опубликуем его в нашем канале. ❤️",
            parse_mode="Markdown"
        )
        context.user_data['waiting_for_review'] = False

    else:
        await update.message.reply_text(
            "Используйте кнопки меню или /start",
            reply_markup=main_keyboard()
        )

# === ОТПРАВКА АДМИНУ НА МОДЕРАЦИЮ ===
async def send_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = context.user_data.get('review_text')
    rating = context.user_data.get('rating', 0)
    photo = context.user_data.get('review_photo')
    stars = "⭐" * rating

    keyboard = [
        [
            InlineKeyboardButton("✅ Опубликовать", callback_data="publish"),
            InlineKeyboardButton("❌ Отклонить", callback_data="reject")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = (
        f"📩 **Новый отзыв на модерацию**\n\n"
        f"👤 @{user.username} (ID: {user.id})\n"
        f"⭐ Оценка: {stars}\n"
        f"📝 Текст:\n{text}"
    )

    if photo:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=caption,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

# === ОБРАБОТКА ДЕЙСТВИЙ АДМИНА ===
async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    msg = query.message
    photo = msg.photo[-1].file_id if msg.photo else None
    caption = msg.caption if msg.caption else msg.text

    if query.data == "publish":
        if CHANNEL_ID:
            if photo:
                await context.bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=photo,
                    caption=caption
                )
            else:
                await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=caption
                )

            if msg.photo:
                await query.edit_message_caption(
                    caption="✅ **Отзыв опубликован в канале!**",
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text(
                    text="✅ **Отзыв опубликован в канале!**",
                    parse_mode="Markdown"
                )
        else:
            await query.edit_message_text(
                text="⚠️ Канал не настроен. Добавь переменную CHANNEL_ID в Railway.",
                parse_mode="Markdown"
            )

    elif query.data == "reject":
        if msg.photo:
            await query.edit_message_caption(
                caption="❌ **Отзыв отклонён.**",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                text="❌ **Отзыв отклонён.**",
                parse_mode="Markdown"
            )

# === ЗАПУСК ===
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(review|support)$"))
    app.add_handler(CallbackQueryHandler(rating_handler, pattern="^rate_"))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^(publish|reject)$"))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    print("✅ Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
