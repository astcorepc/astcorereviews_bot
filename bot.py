import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# === ПЕРЕМЕННЫЕ ИЗ RAILWAY ===
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = os.getenv("CHANNEL_ID")  # например -1002123456789

logging.basicConfig(level=logging.INFO)

# === КЛАВИАТУРА РЕЙТИНГА (звёзды) ===
def rating_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("⭐", callback_data="rate_1"),
            InlineKeyboardButton("⭐⭐", callback_data="rate_2"),
            InlineKeyboardButton("⭐⭐⭐", callback_data="rate_3"),
            InlineKeyboardButton("⭐⭐⭐⭐", callback_data="rate_4"),
            InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="rate_5")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# === ГЛАВНОЕ МЕНЮ ===
def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("⭐ Подать отзыв", callback_data="review")],
        [InlineKeyboardButton("🛠 Поддержка", callback_data="support")],
        [InlineKeyboardButton("📢 Наш канал", url="https://t.me/ваш_канал")]
    ]
    return InlineKeyboardMarkup(keyboard)

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💻 **Добро пожаловать в AST CORE ПК!**\n\n"
        "Нажмите «Подать отзыв», чтобы оценить нас.",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

# === ОБРАБОТКА КНОПОК ГЛАВНОГО МЕНЮ ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "review":
        # Показываем звёзды
        await query.edit_message_text(
            "⭐ **Оцените нас от 1 до 5:**",
            reply_markup=rating_keyboard(),
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

# === ОБРАБОТКА РЕЙТИНГА (звёзды) ===
async def rating_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    rating = int(query.data.split("_")[1])  # 1..5
    context.user_data['rating'] = rating

    # Рисуем звёзды текстом
    stars = "⭐" * rating
    await query.edit_message_text(
        f"📝 **Вы выбрали {stars}**\n\n"
        "Теперь напишите ваш отзыв текстом.\n"
        "Если хотите — приложите фото (одно).\n\n"
        "Напишите текст и отправьте.",
        parse_mode="Markdown"
    )
    context.user_data['waiting_for_review_text'] = True

# === ПРИЁМ ТЕКСТА И ФОТО ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Получаем текст и фото
    text = update.message.text
    photo = None
    if update.message.photo:
        photo = update.message.photo[-1].file_id  # берём лучшее качество

    # Если мы ждём текст отзыва
    if context.user_data.get('waiting_for_review_text') and text:
        context.user_data['review_text'] = text
        context.user_data['review_photo'] = photo
        context.user_data['review_author'] = user.id

        # Отправляем админу на модерацию
        await send_to_admin(update, context)

        # Подтверждение пользователю
        await update.message.reply_text(
            "✅ **Спасибо за ваш отзыв!**\n\n"
            "Он отправлен на модерацию. После проверки мы опубликуем его в канале. ❤️",
            parse_mode="Markdown"
        )
        context.user_data['waiting_for_review_text'] = False

    else:
        await update.message.reply_text(
            "Используйте кнопки меню или /start",
            reply_markup=main_keyboard()
        )

# === ОТПРАВКА АДМИНУ ===
async def send_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = context.user_data.get('review_text')
    rating = context.user_data.get('rating', 0)
    photo = context.user_data.get('review_photo')
    stars = "⭐" * rating

    # Кнопки для админа
    keyboard = [
        [
            InlineKeyboardButton("✅ Опубликовать", callback_data="publish"),
            InlineKeyboardButton("❌ Отклонить", callback_data="reject")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Формируем сообщение админу
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

    # Извлекаем текст и фото из сообщения админа
    msg = query.message
    text = msg.caption if msg.caption else msg.text
    photo = msg.photo[-1].file_id if msg.photo else None

    if query.data == "publish":
        if CHANNEL_ID:
            if photo:
                await context.bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=photo,
                    caption=text
                )
            else:
                await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=text
                )
            await query.edit_message_caption(
                caption="✅ **Отзыв опубликован в канале!**",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_caption(
                caption="⚠️ Канал не настроен. Добавь переменную CHANNEL_ID в Railway.",
                parse_mode="Markdown"
            )

    elif query.data == "reject":
        await query.edit_message_caption(
            caption="❌ **Отзыв отклонён.**",
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
