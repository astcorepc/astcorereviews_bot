import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# === ПЕРЕМЕННЫЕ ИЗ RAILWAY ===
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = os.getenv("CHANNEL_ID")

logging.basicConfig(level=logging.INFO)

# ==========================================
# 1. КЛАВИАТУРЫ
# ==========================================

def main_keyboard():
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton("⭐ Подать отзыв", callback_data="review")],
        [InlineKeyboardButton("🛠 Поддержка", callback_data="support_menu")],
        [InlineKeyboardButton("📢 Наш канал", url="https://t.me/ваш_канал")]
    ]
    return InlineKeyboardMarkup(keyboard)

def rating_keyboard():
    """Кнопки оценки (1-5)"""
    keyboard = [
        [
            InlineKeyboardButton("1 ⭐", callback_data="rate_1"),
            InlineKeyboardButton("2 ⭐", callback_data="rate_2"),
            InlineKeyboardButton("3 ⭐", callback_data="rate_3"),
            InlineKeyboardButton("4 ⭐", callback_data="rate_4"),
            InlineKeyboardButton("5 ⭐", callback_data="rate_5")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def support_topics_keyboard():
    """Меню выбора темы для тикета"""
    keyboard = [
        [InlineKeyboardButton("🖥️ Проблема с ПК", callback_data="support_topic_1")],
        [InlineKeyboardButton("📄 Вопрос по гарантии", callback_data="support_topic_2")],
        [InlineKeyboardButton("💳 Оплата / Доставка", callback_data="support_topic_3")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_keyboard():
    """Клавиатура с одной кнопкой 'Назад'"""
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==========================================
# 2. ОБРАБОТЧИКИ КОМАНД И КНОПОК
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "💻 **Добро пожаловать в AST CORE ПК!**\n\n"
        "Мы ценим каждого клиента. Вы можете оставить отзыв или задать вопрос.",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок главного меню"""
    query = update.callback_query
    await query.answer()

    # --- КНОПКА "ПОДАТЬ ОТЗЫВ" ---
    if query.data == "review":
        await query.edit_message_text(
            "⭐ **Оцените нас от 1 до 5:**",
            reply_markup=rating_keyboard(),
            parse_mode="Markdown"
        )
        return

    # --- КНОПКА "ПОДДЕРЖКА" ---
    if query.data == "support_menu":
        await query.edit_message_text(
            "🛠 **Выберите тему вашего вопроса:**",
            reply_markup=support_topics_keyboard(),
            parse_mode="Markdown"
        )
        return

    # --- КНОПКА "НАЗАД" (ВОЗВРАТ В ГЛАВНОЕ МЕНЮ) ---
    if query.data == "back_to_main":
        # Сбрасываем все состояния
        context.user_data['waiting_for_support'] = False
        context.user_data['waiting_for_review'] = False
        
        await query.edit_message_text(
            "💻 **Главное меню**",
            reply_markup=main_keyboard(),
            parse_mode="Markdown"
        )
        return

# ==========================================
# 3. ОБРАБОТКА ВЫБОРА ОЦЕНКИ (ОТЗЫВЫ)
# ==========================================

async def rating_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь выбрал оценку"""
    query = update.callback_query
    await query.answer()

    rating = int(query.data.split("_")[1])
    context.user_data['rating'] = rating
    context.user_data['waiting_for_review'] = True

    await query.edit_message_text(
        f"📝 **Вы выбрали {rating} ⭐**\n\n"
        "Теперь напишите ваш отзыв текстом.\n"
        "Если хотите — приложите фото (одно).\n\n"
        "Отправьте текст и фото (если есть) одним сообщением.",
        reply_markup=back_keyboard(),  # <-- КНОПКА НАЗАД
        parse_mode="Markdown"
    )

# ==========================================
# 4. ОБРАБОТКА ВЫБОРА ТЕМЫ ТИКЕТА (ПОДДЕРЖКА)
# ==========================================

async def support_topic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь выбрал тему для тикета"""
    query = update.callback_query
    await query.answer()

    topic_map = {
        "support_topic_1": "🖥️ Проблема с ПК",
        "support_topic_2": "📄 Вопрос по гарантии",
        "support_topic_3": "💳 Оплата / Доставка"
    }

    topic = topic_map.get(query.data, "Другое")
    context.user_data['support_topic'] = topic
    context.user_data['waiting_for_support'] = True

    await query.edit_message_text(
        f"📩 **Тема обращения:** {topic}\n\n"
        "Опишите вашу ситуацию максимально подробно.\n"
        "Приложите фото или видео, если это поможет решить вопрос быстрее.\n\n"
        "После отправки мы свяжемся с вами в ближайшее время. ⏳",
        reply_markup=back_keyboard(),  # <-- КНОПКА НАЗАД
        parse_mode="Markdown"
    )

# ==========================================
# 5. ПРИЁМ СООБЩЕНИЙ (ОТЗЫВЫ + ТИКЕТЫ)
# ==========================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка входящих сообщений (текст, фото)"""
    user = update.effective_user

    # --- 5.1. РЕЖИМ ОТЗЫВА ---
    if context.user_data.get('waiting_for_review'):
        text = update.message.caption if update.message.caption else update.message.text
        photo = None
        if update.message.photo:
            photo = update.message.photo[-1].file_id
        elif update.message.document and update.message.document.mime_type and update.message.document.mime_type.startswith('image/'):
            photo = update.message.document.file_id

        if photo and not text:
            await update.message.reply_text(
                "📝 **Пожалуйста, напишите текст отзыва.**",
                parse_mode="Markdown"
            )
            return

        if not text and not photo:
            await update.message.reply_text(
                "Пожалуйста, напишите текст отзыва или приложите фото.",
                reply_markup=main_keyboard()
            )
            return

        await send_review_to_admin(update, context, user, text, photo)
        context.user_data['waiting_for_review'] = False
        return

    # --- 5.2. РЕЖИМ ТИКЕТА ---
    if context.user_data.get('waiting_for_support'):
        text = update.message.caption if update.message.caption else update.message.text
        file_id = None
        file_type = None
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            file_type = "photo"
        elif update.message.document:
            file_id = update.message.document.file_id
            file_type = "document"
        elif update.message.video:
            file_id = update.message.video.file_id
            file_type = "video"

        if not text and not file_id:
            await update.message.reply_text(
                "Пожалуйста, опишите вашу проблему текстом.",
                reply_markup=main_keyboard()
            )
            return

        await send_ticket_to_admin(update, context, user, text, file_id, file_type)
        context.user_data['waiting_for_support'] = False
        return

    # --- 5.3. ЕСЛИ НЕ В РЕЖИМЕ ---
    await update.message.reply_text(
        "Используйте кнопки меню или /start",
        reply_markup=main_keyboard()
    )

# ==========================================
# 6. ОТПРАВКА АДМИНУ (ОТЗЫВЫ)
# ==========================================

async def send_review_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user, text, photo):
    """Отправка отзыва админу"""
    rating = context.user_data.get('rating', 0)

    keyboard = [
        [
            InlineKeyboardButton("✅ Опубликовать", callback_data="publish_review"),
            InlineKeyboardButton("❌ Отклонить", callback_data="reject_review")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = (
        f"📩 **Новый отзыв**\n\n"
        f"👤 @{user.username} (ID: {user.id})\n"
        f"⭐ Оценка: {rating} ⭐\n"
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

    await update.message.reply_text(
        "✅ **Спасибо за ваш отзыв!**\n\n"
        "Он отправлен на модерацию. После проверки мы опубликуем его в канале. ❤️",
        parse_mode="Markdown"
    )

# ==========================================
# 7. ОТПРАВКА АДМИНУ (ТИКЕТЫ)
# ==========================================

async def send_ticket_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user, text, file_id, file_type):
    """Отправка тикета админу"""
    topic = context.user_data.get('support_topic', 'Без темы')

    keyboard = [
        [InlineKeyboardButton("✅ Принято в работу", callback_data="ticket_accepted")],
        [InlineKeyboardButton("❌ Закрыть тикет", callback_data="ticket_closed")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = (
        f"🎫 **Новый тикет в поддержку**\n\n"
        f"👤 @{user.username} (ID: {user.id})\n"
        f"📂 Тема: {topic}\n"
        f"📝 Сообщение:\n{text}"
    )

    if file_id and file_type == "photo":
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=file_id,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    elif file_id and file_type == "document":
        await context.bot.send_document(
            chat_id=ADMIN_ID,
            document=file_id,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    elif file_id and file_type == "video":
        await context.bot.send_video(
            chat_id=ADMIN_ID,
            video=file_id,
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

    await update.message.reply_text(
        "✅ **Ваше обращение принято!**\n\n"
        "Наш специалист свяжется с вами в ближайшее время. ⏳",
        parse_mode="Markdown"
    )

# ==========================================
# 8. ОБРАБОТКА ДЕЙСТВИЙ АДМИНА
# ==========================================

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ нажал кнопку"""
    query = update.callback_query
    await query.answer()

    msg = query.message
    photo = None
    if msg.photo:
        photo = msg.photo[-1].file_id
    elif msg.document and msg.document.mime_type and msg.document.mime_type.startswith('image/'):
        photo = msg.document.file_id

    caption = msg.caption if msg.caption else msg.text

    # --- ОТЗЫВЫ ---
    if query.data == "publish_review":
        if CHANNEL_ID:
            if photo:
                await context.bot.send_photo(chat_id=CHANNEL_ID, photo=photo, caption=caption)
            else:
                await context.bot.send_message(chat_id=CHANNEL_ID, text=caption)

            await query.edit_message_caption(
                caption="✅ **Опубликовано в канале**",
                parse_mode="Markdown"
            ) if photo else await query.edit_message_text(
                text="✅ **Опубликовано в канале**",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                text="⚠️ Канал не настроен. Добавь CHANNEL_ID в Railway.",
                parse_mode="Markdown"
            )
        return

    if query.data == "reject_review":
        await query.edit_message_caption(
            caption="❌ **Отзыв отклонён**",
            parse_mode="Markdown"
        ) if photo else await query.edit_message_text(
            text="❌ **Отзыв отклонён**",
            parse_mode="Markdown"
        )
        return

    # --- ТИКЕТЫ ---
    if query.data == "ticket_accepted":
        await query.edit_message_caption(
            caption="✅ **Тикет принят в работу**\n\nСпециалист скоро свяжется с клиентом.",
            parse_mode="Markdown"
        ) if photo else await query.edit_message_text(
            text="✅ **Тикет принят в работу**\n\nСпециалист скоро свяжется с клиентом.",
            parse_mode="Markdown"
        )
        return

    if query.data == "ticket_closed":
        await query.edit_message_caption(
            caption="❌ **Тикет закрыт**",
            parse_mode="Markdown"
        ) if photo else await query.edit_message_text(
            text="❌ **Тикет закрыт**",
            parse_mode="Markdown"
        )
        return

# ==========================================
# 9. ЗАПУСК
# ==========================================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(review|support_menu|back_to_main)$"))
    app.add_handler(CallbackQueryHandler(rating_handler, pattern="^rate_"))
    app.add_handler(CallbackQueryHandler(support_topic_handler, pattern="^support_topic_"))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^(publish_review|reject_review|ticket_accepted|ticket_closed)$"))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.IMAGE | filters.VIDEO, handle_message))

    print("✅ Бот запущен (отзывы + тикеты + кнопка Назад)!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
