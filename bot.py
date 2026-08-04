import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# === НАСТРОЙКИ (переменные из Railway) ===
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))           # твой ID
CHANNEL_ID = os.getenv("CHANNEL_ID")            # ID канала (например -1001234567890)

logging.basicConfig(level=logging.INFO)

# === Главное меню ===
def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("⭐ Подать отзыв", callback_data="review")],
        [InlineKeyboardButton("🛠 Поддержка", callback_data="support")],
        [InlineKeyboardButton("📢 Наш канал", url="https://t.me/ваш_канал")]
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

# === Обработка кнопок ===
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
            "По любым вопросам пишите:\n"
            "@ваш_менеджер\n\n"
            "Мы на связи ежедневно с 10:00 до 22:00 ⚡",
            parse_mode="Markdown"
        )

# === Приём текста (отзыв от пользователя) ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if context.user_data.get('waiting_for_review'):
        # Сохраняем отзыв в память (чтобы потом опубликовать)
        context.user_data['pending_review'] = text
        context.user_data['review_author'] = user.id

        # Кнопки для админа
        keyboard = [
            [
                InlineKeyboardButton("✅ Опубликовать", callback_data="publish"),
                InlineKeyboardButton("❌ Отклонить", callback_data="reject")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправляем отзыв админу на модерацию
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 **Новый отзыв на модерацию**\n\n"
                 f"👤 @{user.username} (ID: {user.id})\n"
                 f"📝 Текст:\n{text}",
            reply_markup=reply_markup
        )

        # Подтверждение пользователю
        await update.message.reply_text(
            "✅ **Спасибо за ваш отзыв!**\n\n"
            "Он отправлен на модерацию. После проверки мы опубликуем его в нашем канале. ❤️",
            parse_mode="Markdown"
        )
        context.user_data['waiting_for_review'] = False
        context.user_data['pending_review'] = None

    else:
        await update.message.reply_text(
            "Используйте кнопки меню или /start",
            reply_markup=main_keyboard()
        )

# === Обработка действий админа (публикация / отклонение) ===
async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Получаем текст отзыва из сообщения (то, что отправил админ)
    review_text = query.message.text
       # Получаем текст сообщения, на которое нажали
    review_text = query.message.text
    
    # Ищем текст отзыва (берем всё, что идет после последнего перехода на новую строку)
    if "\n" in review_text:
        review_body = review_text.split("\n")[-1]
       # Получаем текст сообщения, на которое нажали
    review_text = query.message.text
    
    # Пытаемся вытащить текст отзыва. Если не получается - ставим заглушку.
    if "\n" in review_text:
        # Берем всё, что после последнего переноса строки
        review_body = review_text.split("\n")[-1]
    else:
               # --- ЗАЩИТА ОТ ОШИБКИ (ВСТАВИТЬ СЮДА) ---
        try:
            # Пытаемся взять текст отзыва (как бы ты его ни получал)
            review_body = context.user_data.get('review_body', '')
            if not review_body:
                # Если в памяти пусто, берем из текста сообщения
                review_text = query.message.text
                if "\n" in review_text:
                    review_body = review_text.split("\n")[-1]
                else:
                    review_body = review_text
        except:
            review_body = "Ошибка при получении текста отзыва"
        # --------------------------------------------

        text = f"⭐ **Новый отзыв о нас!**\n\n{review_body}"
        review_body = review_text

    # --- ЗАЩИТА ОТ ПУСТОГО ТЕКСТА (ДОБАВЛЕНО) ---
    if not review_body:
        review_body = "Текст отзыва не указан (пустое сообщение)"
    # ------------------------------------------

        if query.data == "publish":
            # Публикуем в канал
            if CHANNEL_ID:
                await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=f"⭐ **Новый отзыв о нас!**\n\n{review_body if review_body else 'Текст не указан'}"
                )
                
                await query.edit_message_text(
                    text=f"✅ **Отзыв опубликован в канале!**\n\n{review_body if review_body else 'Текст не указан'}"
                )
            else:
                await query.edit_message_text(
                    text="⚠️ Канал не настроен. Добавь переменную CHANNEL_ID в Railway."
                )
    elif query.data == "reject":
        await query.edit_message_text(
            text=f"❌ **Отзыв отклонён**\n\n{review_body}"
        )

# === Запуск ===
# === Запуск ===
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(review|support)$"))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^(publish|reject)$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # --- ДОБАВИТЬ ОБРАБОТЧИК ОШИБОК ВНУТРЬ MAIN ---
    app.add_error_handler(error_handler)

    print("✅ Бот запущен и готов к работе!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


# --- САМА ФУНКЦИЯ ОБРАБОТЧИКА (вне main) ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"💥 ОШИБКА В БОТЕ: {context.error}")
    import traceback
    traceback.print_exc()


# --- ЗАПУСК БОТА (в самом конце файла) ---
if __name__ == "__main__":
    main()
