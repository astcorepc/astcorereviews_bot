import os
import logging
from datetime import datetime, timedelta
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
        [InlineKeyboardButton("💵 Запись на услуги", callback_data="booking")],
        [InlineKeyboardButton("📢 Наш канал", url="https://t.me/astcorepc1")]
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

def services_keyboard():
    """Выбор услуги из прайс-листа"""
    keyboard = [
        [InlineKeyboardButton("🧹 Чистка ПК от пыли - 1 000 ₽", callback_data="service_1")],
        [InlineKeyboardButton("🌡 Чистка ПК + замена термоинтерфейсов - 2 000 ₽", callback_data="service_2")],
        [InlineKeyboardButton("🎮 Обслуживание видеокарты - 1 500 ₽", callback_data="service_3")],
        [InlineKeyboardButton("⚙️ Сборка ПК (из ваших комплектующих) - 2 500 ₽", callback_data="service_4")],
        [InlineKeyboardButton("⚙️ Сборка ПК (под ключ) - 4 000 ₽", callback_data="service_5")],
        [InlineKeyboardButton("💾 Установка SSD/HDD - 750 ₽", callback_data="service_6")],
        [InlineKeyboardButton("🖥 Установка Windows + драйверы - 1 000 ₽", callback_data="service_7")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_working_days():
    """Возвращает ближайшие рабочие дни (ПН, СР, ПТ) с их расписанием"""
    today = datetime.now().date()
    working_days = []
    
    # Идём вперёд на 21 день, чтобы найти все ПН, СР, ПТ
    for i in range(21):
        check_date = today + timedelta(days=i)
        weekday = check_date.weekday()  # 0=ПН, 1=ВТ, 2=СР, 3=ЧТ, 4=ПТ
        
        if weekday in [0, 2, 4]:  # ПН, СР, ПТ
            day_names = {
                0: "ПН",
                2: "СР", 
                4: "ПТ"
            }
            day_schedule = {
                0: "11:00 – 17:00",
                2: "12:00 – 18:00",
                4: "11:00 – 17:00"
            }
            date_str = check_date.strftime("%d.%m")
            working_days.append((
                check_date.isoformat(), 
                f"{day_names[weekday]} ({date_str})",
                day_schedule[weekday]
            ))
    
    return working_days[:6]  # Берём первые 6 доступных дней

def date_keyboard():
    """Выбор даты (только ПН, СР, ПТ) с указанием времени работы"""
    working_days = get_working_days()
    keyboard = []
    
    for i, (date_iso, display, schedule) in enumerate(working_days):
        keyboard.append([
            InlineKeyboardButton(
                f"📅 {display} ({schedule})", 
                callback_data=f"date_{date_iso}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_services")])
    return InlineKeyboardMarkup(keyboard)

def get_time_slots_for_day(date_iso):
    """Возвращает доступные слоты времени для конкретного дня"""
    date_obj = datetime.fromisoformat(date_iso)
    weekday = date_obj.weekday()
    
    # Расписание по дням
    schedule = {
        0: {"start": 11, "end": 17},  # ПН
        2: {"start": 12, "end": 18},  # СР
        4: {"start": 11, "end": 17}   # ПТ
    }
    
    if weekday not in schedule:
        return []
    
    start_hour = schedule[weekday]["start"]
    end_hour = schedule[weekday]["end"]
    
    slots = []
    for hour in range(start_hour, end_hour + 1):
        slots.append(f"{hour:02d}:00")
    
    return slots

def time_keyboard(date_iso):
    """Выбор времени (только доступные слоты для дня)"""
    slots = get_time_slots_for_day(date_iso)
    keyboard = []
    row = []
    
    for i, slot in enumerate(slots):
        row.append(InlineKeyboardButton(slot, callback_data=f"time_{slot}"))
        if len(row) == 3 or i == len(slots) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_booking_date")])
    return InlineKeyboardMarkup(keyboard)

# ==========================================
# 2. ОБРАБОТЧИКИ КОМАНД И КНОПОК
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "💻 **Добро пожаловать в AST CORE ПК!**\n\n"
        "Мы ценим каждого клиента.\n\n"
        "Вы можете:\n"
        "⭐ Оставить отзыв\n"
        "🛠 Задать вопрос в поддержку\n"
        "💵 Записаться на услугу",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок главного меню"""
    query = update.callback_query
    await query.answer()

    if query.data == "review":
        await query.edit_message_text(
            "⭐ **Оцените нас от 1 до 5:**",
            reply_markup=rating_keyboard(),
            parse_mode="Markdown"
        )
        return

    if query.data == "support_menu":
        await query.edit_message_text(
            "🛠 **Выберите тему вашего вопроса:**",
            reply_markup=support_topics_keyboard(),
            parse_mode="Markdown"
        )
        return

    if query.data == "booking":
        await query.edit_message_text(
            "💵 **Выберите услугу из списка:**",
            reply_markup=services_keyboard(),
            parse_mode="Markdown"
        )
        return

    if query.data == "back_to_main":
        context.user_data['waiting_for_support'] = False
        context.user_data['waiting_for_review'] = False
        context.user_data['booking_step'] = None
        
        await query.edit_message_text(
            "💻 **Главное меню**",
            reply_markup=main_keyboard(),
            parse_mode="Markdown"
        )
        return

    if query.data == "back_to_services":
        await query.edit_message_text(
            "💵 **Выберите услугу из списка:**",
            reply_markup=services_keyboard(),
            parse_mode="Markdown"
        )
        return

    if query.data == "back_to_booking_date":
        if context.user_data.get('selected_service'):
            await query.edit_message_text(
                f"📅 **Выберите дату для записи:**\n\n"
                f"Услуга: {context.user_data.get('selected_service')}\n\n"
                "Рабочие дни:\n"
                "ПН: 11:00 – 17:00\n"
                "СР: 12:00 – 18:00\n"
                "ПТ: 11:00 – 17:00",
                reply_markup=date_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "💵 **Выберите услугу из списка:**",
                reply_markup=services_keyboard(),
                parse_mode="Markdown"
            )
        return

    # --- ОБРАБОТКА ВЫБОРА УСЛУГИ ---
    if query.data.startswith("service_"):
        services_map = {
            "service_1": "🧹 Чистка ПК от пыли - 1 000 ₽",
            "service_2": "🌡 Чистка ПК + замена термоинтерфейсов - 2 000 ₽",
            "service_3": "🎮 Обслуживание видеокарты - 1 500 ₽",
            "service_4": "⚙️ Сборка ПК (из ваших комплектующих) - 2 500 ₽",
            "service_5": "⚙️ Сборка ПК (под ключ) - 4 000 ₽",
            "service_6": "💾 Установка SSD/HDD - 750 ₽",
            "service_7": "🖥 Установка Windows + драйверы - 1 000 ₽"
        }
        service = services_map.get(query.data, "Неизвестная услуга")
        context.user_data['selected_service'] = service
        context.user_data['booking_step'] = 'date'
        
        await query.edit_message_text(
            f"✅ **Выбрана услуга:**\n{service}\n\n"
            "📅 **Теперь выберите дату:**\n\n"
            "Рабочие дни:\n"
            "ПН: 11:00 – 17:00\n"
            "СР: 12:00 – 18:00\n"
            "ПТ: 11:00 – 17:00",
            reply_markup=date_keyboard(),
            parse_mode="Markdown"
        )
        return

    # --- ОБРАБОТКА ВЫБОРА ДАТЫ ---
    if query.data.startswith("date_"):
        date_str = query.data.replace("date_", "")
        context.user_data['selected_date'] = date_str
        context.user_data['booking_step'] = 'time'
        
        date_obj = datetime.fromisoformat(date_str)
        date_formatted = date_obj.strftime("%d.%m.%Y")
        weekday_names = {0: "ПН", 2: "СР", 4: "ПТ"}
        weekday = weekday_names.get(date_obj.weekday(), "")
        
        await query.edit_message_text(
            f"✅ **Услуга:** {context.user_data.get('selected_service')}\n"
            f"📅 **Дата:** {date_formatted} ({weekday})\n\n"
            "🕐 **Выберите удобное время:**",
            reply_markup=time_keyboard(date_str),
            parse_mode="Markdown"
        )
        return

    # --- ОБРАБОТКА ВЫБОРА ВРЕМЕНИ ---
    if query.data.startswith("time_"):
        time_str = query.data.replace("time_", "")
        context.user_data['selected_time'] = time_str
        context.user_data['booking_step'] = 'contacts'
        
        date_obj = datetime.fromisoformat(context.user_data.get('selected_date'))
        date_formatted = date_obj.strftime("%d.%m.%Y")
        weekday_names = {0: "ПН", 2: "СР", 4: "ПТ"}
        weekday = weekday_names.get(date_obj.weekday(), "")
        
        await query.edit_message_text(
            f"✅ **Услуга:** {context.user_data.get('selected_service')}\n"
            f"📅 **Дата:** {date_formatted} ({weekday})\n"
            f"🕐 **Время:** {time_str}\n\n"
            "📱 **Введите ваш контактный телефон или Telegram @username:**\n\n"
            "Наш менеджер свяжется с вами для подтверждения.",
            parse_mode="Markdown"
        )
        context.user_data['waiting_for_contact'] = True
        return

# ==========================================
# 3. ОБРАБОТКА ВЫБОРА ОЦЕНКИ (ОТЗЫВЫ)
# ==========================================

async def rating_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        reply_markup=back_keyboard(),
        parse_mode="Markdown"
    )

# ==========================================
# 4. ОБРАБОТКА ВЫБОРА ТЕМЫ ТИКЕТА
# ==========================================

async def support_topic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        reply_markup=back_keyboard(),
        parse_mode="Markdown"
    )

# ==========================================
# 5. ПРИЁМ СООБЩЕНИЙ
# ==========================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # --- РЕЖИМ ЗАПИСИ (ввод контактов) ---
    if context.user_data.get('waiting_for_contact'):
        contact = update.message.text
        if not contact:
            await update.message.reply_text(
                "📱 **Пожалуйста, введите ваш контактный телефон или Telegram @username:**",
                parse_mode="Markdown"
            )
            return

        context.user_data['contact'] = contact
        context.user_data['waiting_for_contact'] = False
        
        await send_booking_to_admin(update, context, user)
        
        await update.message.reply_text(
            "✅ **Ваша запись принята!**\n\n"
            "Наш менеджер свяжется с вами для подтверждения в ближайшее время. ⏳\n\n"
            "Вернуться в меню: /start",
            parse_mode="Markdown"
        )
        return

    # --- РЕЖИМ ОТЗЫВА ---
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

    # --- РЕЖИМ ТИКЕТА ---
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

    await update.message.reply_text(
        "Используйте кнопки меню или /start",
        reply_markup=main_keyboard()
    )

# ==========================================
# 6. ОТПРАВКА АДМИНУ (ЗАПИСЬ)
# ==========================================

async def send_booking_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    """Отправка записи админу"""
    service = context.user_data.get('selected_service', 'Не выбрана')
    date_str = context.user_data.get('selected_date', 'Не выбрана')
    time_str = context.user_data.get('selected_time', 'Не выбрано')
    contact = context.user_data.get('contact', 'Не указан')

    try:
        date_obj = datetime.fromisoformat(date_str)
        date_formatted = date_obj.strftime("%d.%m.%Y")
        weekday_names = {0: "ПН", 2: "СР", 4: "ПТ"}
        weekday = weekday_names.get(date_obj.weekday(), "")
        date_display = f"{date_formatted} ({weekday})"
    except:
        date_display = date_str

    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить запись", callback_data="booking_confirm"),
            InlineKeyboardButton("❌ Отменить запись", callback_data="booking_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = (
        f"💵 **НОВАЯ ЗАПИСЬ НА УСЛУГУ**\n\n"
        f"👤 Клиент: @{user.username} (ID: {user.id})\n"
        f"📱 Контакт: {contact}\n"
        f"🛠 Услуга:\n{service}\n"
        f"📅 Дата: {date_display}\n"
        f"🕐 Время: {time_str}"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=caption,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==========================================
# 7. ОТПРАВКА АДМИНУ (ОТЗЫВЫ)
# ==========================================

async def send_review_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user, text, photo):
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
# 8. ОТПРАВКА АДМИНУ (ТИКЕТЫ)
# ==========================================

async def send_ticket_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user, text, file_id, file_type):
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
# 9. ОБРАБОТКА ДЕЙСТВИЙ АДМИНА
# ==========================================

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    msg = query.message
    photo = None
    if msg.photo:
        photo = msg.photo[-1].file_id
    elif msg.document and msg.document.mime_type and msg.document.mime_type.startswith('image/'):
        photo = msg.document.file_id

    caption = msg.caption if msg.caption else msg.text

    # --- ЗАПИСЬ ---
    if query.data == "booking_confirm":
        await query.edit_message_text(
            text=f"✅ **Запись ПОДТВЕРЖДЕНА!**\n\n{caption}",
            parse_mode="Markdown"
        )
        return

    if query.data == "booking_cancel":
        await query.edit_message_text(
            text=f"❌ **Запись ОТМЕНЕНА**\n\n{caption}",
            parse_mode="Markdown"
        )
        return

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
# 10. ЗАПУСК
# ==========================================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(review|support_menu|booking|back_to_main|back_to_services|back_to_booking_date|service_.*|date_.*|time_.*)$"))
    app.add_handler(CallbackQueryHandler(rating_handler, pattern="^rate_"))
    app.add_handler(CallbackQueryHandler(support_topic_handler, pattern="^support_topic_"))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^(publish_review|reject_review|ticket_accepted|ticket_closed|booking_confirm|booking_cancel)$"))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.IMAGE | filters.VIDEO, handle_message))

    print("✅ Бот запущен (отзывы + тикеты + запись на услуги)!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
