import os
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# === ПЕРЕМЕННЫЕ ИЗ RAILWAY ===
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = os.getenv("CHANNEL_ID")
REVIEWS_CHANNEL_ID = os.getenv("REVIEWS_CHANNEL_ID")  # Новый канал для отзывов

logging.basicConfig(level=logging.INFO)

# ==========================================
# 1. КЛАВИАТУРЫ
# ==========================================

def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("⭐ Подать отзыв", callback_data="review")],
        [InlineKeyboardButton("🛠 Поддержка", callback_data="support_menu")],
        [InlineKeyboardButton("💵 Запись на услуги", callback_data="booking")],
        [InlineKeyboardButton("📢 Наш канал", url="https://t.me/astcorepc1")],
        [InlineKeyboardButton("⭐ Канал с отзывами", url="https://t.me/astcorereviews")]  # Новая кнопка
    ]
    return InlineKeyboardMarkup(keyboard)

def rating_keyboard():
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
    keyboard = [
        [InlineKeyboardButton("🖥️ Проблема с ПК", callback_data="support_topic_1")],
        [InlineKeyboardButton("📄 Вопрос по гарантии", callback_data="support_topic_2")],
        [InlineKeyboardButton("💳 Оплата / Доставка", callback_data="support_topic_3")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_services")]
    ]
    return InlineKeyboardMarkup(keyboard)

def services_keyboard():
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
    today = datetime.now().date()
    working_days = []
    for i in range(21):
        check_date = today + timedelta(days=i)
        weekday = check_date.weekday()
        if weekday in [0, 2, 4]:
            day_names = {0: "ПН", 2: "СР", 4: "ПТ"}
            day_schedule = {0: "11:00 – 17:00", 2: "12:00 – 18:00", 4: "11:00 – 17:00"}
            date_str = check_date.strftime("%d.%m")
            working_days.append((check_date.isoformat(), f"{day_names[weekday]} ({date_str})", day_schedule[weekday]))
    return working_days[:6]

def date_keyboard():
    working_days = get_working_days()
    keyboard = []
    for date_iso, display, schedule in working_days:
        keyboard.append([InlineKeyboardButton(f"📅 {display} ({schedule})", callback_data=f"date_{date_iso}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_services")])
    return InlineKeyboardMarkup(keyboard)

def get_time_slots_for_day(date_iso):
    date_obj = datetime.fromisoformat(date_iso)
    weekday = date_obj.weekday()
    schedule = {0: {"start": 11, "end": 17}, 2: {"start": 12, "end": 18}, 4: {"start": 11, "end": 17}}
    if weekday not in schedule:
        return []
    start_hour = schedule[weekday]["start"]
    end_hour = schedule[weekday]["end"]
    slots = []
    for hour in range(start_hour, end_hour + 1):
        slots.append(f"{hour:02d}:00")
    return slots

def time_keyboard(date_iso):
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

def clear_user_data(context):
    keys_to_clear = [
        'waiting_for_review', 'waiting_for_support', 'waiting_for_contact',
        'waiting_for_budget', 'waiting_for_wishes', 'waiting_for_extras',
        'selected_service', 'selected_service_id', 'selected_date', 'selected_time',
        'rating', 'budget', 'wishes', 'extras', 'contact', 'support_topic',
        'review_text', 'review_photo'  # Добавляем для хранения отзыва
    ]
    for key in keys_to_clear:
        if key in context.user_data:
            del context.user_data[key]

# ==========================================
# 2. ОБРАБОТЧИКИ КОМАНД И КНОПОК
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_user_data(context)
    await update.message.reply_text(
        "💻 **Добро пожаловать в AST CORE ПК!**\n\n"
        "Вы можете:\n"
        "⭐ Оставить отзыв\n"
        "🛠 Задать вопрос в поддержку\n"
        "💵 Записаться на услугу",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "review":
        clear_user_data(context)
        await query.edit_message_text("⭐ **Оцените нас от 1 до 5:**", reply_markup=rating_keyboard(), parse_mode="Markdown")
        return

    if query.data == "support_menu":
        clear_user_data(context)
        await query.edit_message_text("🛠 **Выберите тему вопроса:**", reply_markup=support_topics_keyboard(), parse_mode="Markdown")
        return

    if query.data == "booking":
        clear_user_data(context)
        await query.edit_message_text("💵 **Выберите услугу:**", reply_markup=services_keyboard(), parse_mode="Markdown")
        return

    if query.data == "back_to_main":
        clear_user_data(context)
        await query.edit_message_text("💻 **Главное меню**", reply_markup=main_keyboard(), parse_mode="Markdown")
        return

    if query.data == "back_to_services":
        context.user_data['waiting_for_contact'] = False
        context.user_data['waiting_for_budget'] = False
        context.user_data['waiting_for_wishes'] = False
        context.user_data['waiting_for_extras'] = False
        await query.edit_message_text("💵 **Выберите услугу:**", reply_markup=services_keyboard(), parse_mode="Markdown")
        return

    if query.data == "back_to_booking_date":
        if context.user_data.get('selected_service'):
            await query.edit_message_text(
                f"📅 **Выберите дату:**\n\nУслуга: {context.user_data.get('selected_service')}\n\nПН: 11:00 – 17:00\nСР: 12:00 – 18:00\nПТ: 11:00 – 17:00",
                reply_markup=date_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("💵 **Выберите услугу:**", reply_markup=services_keyboard(), parse_mode="Markdown")
        return

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
        context.user_data['selected_service_id'] = query.data

        # === СБОРКА ИЗ ВАШИХ КОМПЛЕКТУЮЩИХ ===
        if query.data == "service_4":
            context.user_data['budget'] = "Не требуется"
            context.user_data['wishes'] = "Не указаны"
            context.user_data['extras'] = None
            context.user_data['waiting_for_wishes'] = True
            await query.edit_message_text(
                f"✅ **Выбрана услуга:**\n{service}\n\n📝 **Напишите пожелания по сборке:**\n\nНапример: для игр, для работы, какой процессор, видеокарта и т.д.",
                reply_markup=back_keyboard(),
                parse_mode="Markdown"
            )
            return

        # === СБОРКА ПОД КЛЮЧ ===
        elif query.data == "service_5":
            context.user_data['budget'] = "Не указан"
            context.user_data['wishes'] = "Не указаны"
            context.user_data['extras'] = "Нет"
            context.user_data['waiting_for_budget'] = True
            await query.edit_message_text(
                f"✅ **Выбрана услуга:**\n{service}\n\n💰 **Какой бюджет?**\n\nНапишите сумму в рублях (например: 80 000 ₽)",
                reply_markup=back_keyboard(),
                parse_mode="Markdown"
            )
            return

        # === ОСТАЛЬНЫЕ УСЛУГИ ===
        else:
            context.user_data['budget'] = "Не требуется"
            context.user_data['wishes'] = "Нет"
            context.user_data['extras'] = "Нет"
            await query.edit_message_text(
                f"✅ **Выбрана услуга:**\n{service}\n\n📅 **Выберите дату:**\n\nПН: 11:00 – 17:00\nСР: 12:00 – 18:00\nПТ: 11:00 – 17:00",
                reply_markup=date_keyboard(),
                parse_mode="Markdown"
            )
        return

    if query.data.startswith("date_"):
        date_str = query.data.replace("date_", "")
        context.user_data['selected_date'] = date_str
        date_obj = datetime.fromisoformat(date_str)
        date_formatted = date_obj.strftime("%d.%m.%Y")
        weekday_names = {0: "ПН", 2: "СР", 4: "ПТ"}
        weekday = weekday_names.get(date_obj.weekday(), "")
        await query.edit_message_text(
            f"✅ **Услуга:** {context.user_data.get('selected_service')}\n📅 **Дата:** {date_formatted} ({weekday})\n\n🕐 **Выберите время:**",
            reply_markup=time_keyboard(date_str),
            parse_mode="Markdown"
        )
        return

    if query.data.startswith("time_"):
        time_str = query.data.replace("time_", "")
        context.user_data['selected_time'] = time_str
        date_obj = datetime.fromisoformat(context.user_data.get('selected_date'))
        date_formatted = date_obj.strftime("%d.%m.%Y")
        weekday_names = {0: "ПН", 2: "СР", 4: "ПТ"}
        weekday = weekday_names.get(date_obj.weekday(), "")
        service_id = context.user_data.get('selected_service_id', '')

        # === ДЛЯ "ИЗ ВАШИХ КОМПЛЕКТУЮЩИХ" — ДОПОЛНЕНИЯ ===
        if service_id == "service_4" and context.user_data.get('extras') is None:
            context.user_data['waiting_for_extras'] = True
            await query.edit_message_text(
                f"✅ **Услуга:** {context.user_data.get('selected_service')}\n📅 **Дата:** {date_formatted} ({weekday})\n🕐 **Время:** {time_str}\n📝 **Пожелания:** {context.user_data.get('wishes', 'Не указаны')}\n\n➕ **Дополнения за дополнительную плату:**\nНапишите, что вы хотите добавить:\n\n• Установка дополнительного ПО\n• Дополнительные вентиляторы\n• Внешний вид (подсветка, корпус, кастомные провода и т.д.)\n• Другие дополнения (опишите)\n\nЕсли у вас есть дополнения, опишите их выше. Если нет — просто напишите 'Нет'.",
                reply_markup=back_keyboard(),
                parse_mode="Markdown"
            )
            return

        # === ДЛЯ "ПОД КЛЮЧ" — проверяем, есть ли пожелания ===
        if service_id == "service_5" and context.user_data.get('wishes') == "Не указаны":
            context.user_data['waiting_for_wishes'] = True
            await query.edit_message_text(
                f"✅ **Услуга:** {context.user_data.get('selected_service')}\n📅 **Дата:** {date_formatted} ({weekday})\n🕐 **Время:** {time_str}\n💰 **Бюджет:** {context.user_data.get('budget', 'Не указан')}\n\n📝 **Напишите пожелания по сборке:**\n\nНапример: для игр, для работы, какой процессор, видеокарта и т.д.",
                reply_markup=back_keyboard(),
                parse_mode="Markdown"
            )
            return

        # === ФИНАЛЬНОЕ СООБЩЕНИЕ (с учетом типа услуги) ===
        is_build_service = service_id in ["service_4", "service_5"]
        
        if is_build_service:
            msg = (
                f"✅ **Услуга:** {context.user_data.get('selected_service')}\n"
                f"📅 **Дата:** {date_formatted} ({weekday})\n"
                f"🕐 **Время:** {time_str}\n"
                f"💰 **Бюджет:** {context.user_data.get('budget', 'Не указан')}\n"
                f"📝 **Пожелания:** {context.user_data.get('wishes', 'Нет')}\n"
                f"➕ **Дополнения:** {context.user_data.get('extras', 'Нет')}\n\n"
                f"📱 **Введите контактный телефон или @username:**"
            )
        else:
            msg = (
                f"✅ **Услуга:** {context.user_data.get('selected_service')}\n"
                f"📅 **Дата:** {date_formatted} ({weekday})\n"
                f"🕐 **Время:** {time_str}\n\n"
                f"📱 **Введите контактный телефон или @username:**"
            )

        await query.edit_message_text(msg, reply_markup=back_keyboard(), parse_mode="Markdown")
        context.user_data['waiting_for_contact'] = True
        return

# ==========================================
# 3. ОБРАБОТЧИКИ ВЫБОРА ОЦЕНКИ И ТЕМ ТИКЕТА
# ==========================================

async def rating_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    rating = int(query.data.split("_")[1])
    context.user_data['rating'] = rating
    context.user_data['waiting_for_review'] = True
    await query.edit_message_text(
        f"📝 **Вы выбрали {rating} ⭐**\n\nНапишите текст отзыва.\nМожно приложить фото.",
        reply_markup=back_keyboard(),
        parse_mode="Markdown"
    )

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
        f"📩 **Тема:** {topic}\n\nОпишите ситуацию подробно. Можно приложить фото/видео.",
        reply_markup=back_keyboard(),
        parse_mode="Markdown"
    )

# ==========================================
# 4. ПРИЁМ СООБЩЕНИЙ
# ==========================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.caption if update.message.caption else update.message.text
    photo = None
    video = None

    # Проверяем, есть ли фото или видео
    if update.message.photo:
        photo = update.message.photo[-1].file_id
    elif update.message.video:
        video = update.message.video.file_id
    elif update.message.document and update.message.document.mime_type and update.message.document.mime_type.startswith('image/'):
        photo = update.message.document.file_id

    # ==========================================
    # 1. ВВОД БЮДЖЕТА
    # ==========================================
    if context.user_data.get('waiting_for_budget'):
        if text:
            context.user_data['budget'] = text
            context.user_data['waiting_for_budget'] = False
            context.user_data['waiting_for_wishes'] = True
            await update.message.reply_text(
                f"✅ **Бюджет сохранён:** {text}\n\n📝 **Напишите пожелания по сборке:**\n\nНапример: для игр, для работы, какой процессор, видеокарта и т.д.",
                reply_markup=back_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "💰 **Пожалуйста, напишите ваш бюджет в рублях.**",
                parse_mode="Markdown"
            )
        return

    # ==========================================
    # 2. ВВОД ПОЖЕЛАНИЙ
    # ==========================================
    if context.user_data.get('waiting_for_wishes'):
        if text:
            context.user_data['wishes'] = text
            context.user_data['waiting_for_wishes'] = False

            if context.user_data.get('selected_service_id') == "service_4":
                context.user_data['waiting_for_extras'] = True
                await update.message.reply_text(
                    f"✅ **Пожелания сохранены:**\n{text}\n\n➕ **Дополнения за дополнительную плату:**\nНапишите, что вы хотите добавить:\n\n• Установка дополнительного ПО\n• Дополнительные вентиляторы\n• Внешний вид (подсветка, корпус, кастомные провода и т.д.)\n• Другие дополнения (опишите)\n\nЕсли у вас есть дополнения, опишите их выше. Если нет — просто напишите 'Нет'.",
                    reply_markup=back_keyboard(),
                    parse_mode="Markdown"
                )
                return
            else:
                await update.message.reply_text(
                    f"✅ **Пожелания сохранены:**\n{text}\n\n📅 **Теперь выберите дату:**\n\nПН: 11:00 – 17:00\nСР: 12:00 – 18:00\nПТ: 11:00 – 17:00",
                    reply_markup=date_keyboard(),
                    parse_mode="Markdown"
                )
                return
        else:
            await update.message.reply_text(
                "📝 **Пожалуйста, напишите ваши пожелания по сборке.**",
                parse_mode="Markdown"
            )
            return

    # ==========================================
    # 3. ВВОД ДОПОЛНЕНИЙ
    # ==========================================
    if context.user_data.get('waiting_for_extras'):
        if text:
            context.user_data['extras'] = text
            context.user_data['waiting_for_extras'] = False
            await update.message.reply_text(
                f"✅ **Дополнения сохранены:**\n{text}\n\n📅 **Теперь выберите дату:**\n\nПН: 11:00 – 17:00\nСР: 12:00 – 18:00\nПТ: 11:00 – 17:00",
                reply_markup=date_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "➕ **Пожалуйста, напишите дополнения или 'Нет'.**",
                parse_mode="Markdown"
            )
        return

    # ==========================================
    # 4. ВВОД КОНТАКТОВ
    # ==========================================
    if context.user_data.get('waiting_for_contact'):
        if text:
            context.user_data['contact'] = text
            context.user_data['waiting_for_contact'] = False
            await send_booking_to_admin(update, context, user)
            await update.message.reply_text(
                "✅ **Запись принята!**\n\nМенеджер свяжется с вами. ⏳\n\nВернуться в меню: /start",
                reply_markup=main_keyboard(),
                parse_mode="Markdown"
            )
            clear_user_data(context)
        else:
            await update.message.reply_text(
                "📱 **Пожалуйста, введите ваш контактный телефон или Telegram @username:**",
                parse_mode="Markdown"
            )
        return

    # ==========================================
    # 5. ОТЗЫВЫ
    # ==========================================
    if context.user_data.get('waiting_for_review'):
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

        # Сохраняем отзыв в user_data для последующей отправки уведомления
        context.user_data['review_text'] = text or "Без текста"
        context.user_data['review_photo'] = photo
        context.user_data['review_user_id'] = user.id
        context.user_data['review_username'] = user.username
        
        await send_review_to_admin(update, context, user, text or "Без текста", photo)
        
        # Отправляем сообщение пользователю о модерации
        await update.message.reply_text(
            "✅ **Ваш отзыв отправлен на модерацию!**\n\n"
            "Мы проверим его и, если всё хорошо, опубликуем в нашем канале с отзывами. 📢\n\n"
            "Вы получите уведомление о результате модерации.",
            parse_mode="Markdown"
        )
        
        context.user_data['waiting_for_review'] = False
        # НЕ очищаем user_data полностью, чтобы сохранить данные для уведомления
        # Очищаем только флаги ожидания
        context.user_data['waiting_for_review'] = False
        return

    # ==========================================
    # 6. ТИКЕТЫ (с поддержкой видео)
    # ==========================================
    if context.user_data.get('waiting_for_support'):
        file_id = None
        file_type = None
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            file_type = "photo"
        elif update.message.video:
            file_id = update.message.video.file_id
            file_type = "video"
        elif update.message.document:
            file_id = update.message.document.file_id
            file_type = "document"

        if not text and not file_id:
            await update.message.reply_text(
                "Пожалуйста, опишите вашу проблему текстом.",
                reply_markup=main_keyboard()
            )
            return

        await send_ticket_to_admin(update, context, user, text or "Без текста", file_id, file_type)
        context.user_data['waiting_for_support'] = False
        clear_user_data(context)
        return

    # ==========================================
    # 7. НЕ В РЕЖИМЕ
    # ==========================================
    await update.message.reply_text(
        "Используйте кнопки меню или /start",
        reply_markup=main_keyboard()
    )

# ==========================================
# 5. ОТПРАВКИ АДМИНУ
# ==========================================

async def send_booking_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    service = context.user_data.get('selected_service', 'Не выбрана')
    date_str = context.user_data.get('selected_date', 'Не выбрана')
    time_str = context.user_data.get('selected_time', 'Не выбрано')
    contact = context.user_data.get('contact', 'Не указан')
    budget = context.user_data.get('budget', 'Не указан')
    wishes = context.user_data.get('wishes', 'Нет')
    extras = context.user_data.get('extras', 'Нет')
    try:
        date_obj = datetime.fromisoformat(date_str)
        date_formatted = date_obj.strftime("%d.%m.%Y")
        weekday_names = {0: "ПН", 2: "СР", 4: "ПТ"}
        weekday = weekday_names.get(date_obj.weekday(), "")
        date_display = f"{date_formatted} ({weekday})"
    except:
        date_display = date_str
    keyboard = [[InlineKeyboardButton("✅ Подтвердить", callback_data="booking_confirm"), InlineKeyboardButton("❌ Отменить", callback_data="booking_cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    caption = f"💵 **НОВАЯ ЗАПИСЬ**\n\n👤 @{user.username} (ID: {user.id})\n📱 Контакт: {contact}\n🛠 {service}\n📅 {date_display}\n🕐 {time_str}\n"
    if budget and budget != "Не требуется" and budget != "Не указан":
        caption += f"💰 Бюджет: {budget}\n"
    if wishes and wishes != "Нет" and wishes != "Не указаны":
        caption += f"📝 Пожелания:\n{wishes}\n"
    if extras and extras != "Нет":
        caption += f"➕ Дополнения:\n{extras}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=caption, reply_markup=reply_markup, parse_mode="Markdown")

async def send_review_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user, text, photo):
    rating = context.user_data.get('rating', 0)
    # Сохраняем ID пользователя для отправки уведомления
    context.user_data['review_user_id'] = user.id
    context.user_data['review_username'] = user.username
    
    keyboard = [
        [InlineKeyboardButton("✅ Опубликовать", callback_data="publish_review"), 
         InlineKeyboardButton("❌ Отклонить", callback_data="reject_review")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    caption = f"📩 **Новый отзыв**\n\n👤 @{user.username} (ID: {user.id})\n⭐ Оценка: {rating} ⭐\n📝 {text}"
    if photo:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo, caption=caption, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=ADMIN_ID, text=caption, reply_markup=reply_markup, parse_mode="Markdown")

async def send_ticket_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user, text, file_id, file_type):
    topic = context.user_data.get('support_topic', 'Без темы')
    keyboard = [[InlineKeyboardButton("✅ Принято", callback_data="ticket_accepted"), InlineKeyboardButton("❌ Закрыть", callback_data="ticket_closed")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    caption = f"🎫 **Новый тикет**\n\n👤 @{user.username} (ID: {user.id})\n📂 Тема: {topic}\n📝 {text}"
    
    if file_id and file_type == "photo":
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=caption, reply_markup=reply_markup, parse_mode="Markdown")
    elif file_id and file_type == "video":
        await context.bot.send_video(chat_id=ADMIN_ID, video=file_id, caption=caption, reply_markup=reply_markup, parse_mode="Markdown")
    elif file_id and file_type == "document":
        await context.bot.send_document(chat_id=ADMIN_ID, document=file_id, caption=caption, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=ADMIN_ID, text=caption, reply_markup=reply_markup, parse_mode="Markdown")
    
    await update.message.reply_text(
        "✅ **Обращение принято!**\n\nСпециалист свяжется с вами. ⏳",
        parse_mode="Markdown"
    )

# ==========================================
# 6. ОБРАБОТЧИК АДМИНА (исправлен для видео и уведомлений)
# ==========================================

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    msg = query.message
    photo = None
    video = None
    document = None
    
    # Проверяем, что пришло
    if msg.photo:
        photo = msg.photo[-1].file_id
    elif msg.video:
        video = msg.video.file_id
    elif msg.document and msg.document.mime_type and msg.document.mime_type.startswith('image/'):
        photo = msg.document.file_id
    elif msg.document:
        document = msg.document.file_id
    
    caption = msg.caption if msg.caption else msg.text

    # --- ЗАПИСЬ ---
    if query.data == "booking_confirm":
        await query.edit_message_text(text=f"✅ **Запись ПОДТВЕРЖДЕНА!**\n\n{caption}", parse_mode="Markdown")
        return
    if query.data == "booking_cancel":
        await query.edit_message_text(text=f"❌ **Запись ОТМЕНЕНА**\n\n{caption}", parse_mode="Markdown")
        return

    # --- ОТЗЫВЫ ---
    if query.data == "publish_review":
        # Извлекаем ID пользователя из caption
        import re
        user_id_match = re.search(r"ID: (\d+)", caption)
        user_id = int(user_id_match.group(1)) if user_id_match else None
        
        # Публикуем в канал отзывов
        if REVIEWS_CHANNEL_ID:
            # Убираем из текста информацию об ID пользователя
            clean_caption = re.sub(r"\(ID: \d+\)", "", caption)
            clean_caption = re.sub(r"👤 @\w+", "👤 Клиент", clean_caption)
            
            if photo:
                await context.bot.send_photo(chat_id=REVIEWS_CHANNEL_ID, photo=photo, caption=clean_caption)
            else:
                await context.bot.send_message(chat_id=REVIEWS_CHANNEL_ID, text=clean_caption)
            
            # Отправляем уведомление пользователю
            if user_id:
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="✅ **Ваш отзыв опубликован в нашем канале с отзывами!**\n\n"
                             "Спасибо, что поделились своим мнением! 🙏\n\n"
                             "📢 Посмотреть отзыв можно здесь: https://t.me/astcorereviews",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logging.error(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
            
            if photo:
                await query.edit_message_caption(caption="✅ **Опубликовано в канале отзывов**", parse_mode="Markdown")
            else:
                await query.edit_message_text(text="✅ **Опубликовано в канале отзывов**", parse_mode="Markdown")
        else:
            await query.edit_message_text(text="⚠️ Канал отзывов не настроен. Добавь REVIEWS_CHANNEL_ID в Railway.", parse_mode="Markdown")
        return

    if query.data == "reject_review":
        # Извлекаем ID пользователя из caption
        import re
        user_id_match = re.search(r"ID: (\d+)", caption)
        user_id = int(user_id_match.group(1)) if user_id_match else None
        
        # Отправляем уведомление об отклонении
        if user_id:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="❌ **Ваш отзыв не прошел модерацию.**\n\n"
                         "К сожалению, мы не можем опубликовать его в нашем канале.\n\n"
                         "Вы можете оставить новый отзыв, нажав на кнопку 'Подать отзыв' в меню. 💬",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logging.error(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
        
        if photo:
            await query.edit_message_caption(caption="❌ **Отзыв отклонён**", parse_mode="Markdown")
        else:
            await query.edit_message_text(text="❌ **Отзыв отклонён**", parse_mode="Markdown")
        return

    # --- ТИКЕТЫ (исправлено: теперь работает с видео) ---
    if query.data == "ticket_accepted":
        if photo or video or document:
            await query.edit_message_caption(
                caption="✅ **Тикет принят в работу**\n\nСпециалист скоро свяжется с клиентом.",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                text="✅ **Тикет принят в работу**\n\nСпециалист скоро свяжется с клиентом.",
                parse_mode="Markdown"
            )
        return

    if query.data == "ticket_closed":
        if photo or video or document:
            await query.edit_message_caption(
                caption="❌ **Тикет закрыт**",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                text="❌ **Тикет закрыт**",
                parse_mode="Markdown"
            )
        return

# ==========================================
# 7. ЗАПУСК
# ==========================================

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(review|support_menu|booking|back_to_main|back_to_services|back_to_booking_date|service_.*|date_.*|time_.*)$"))
    app.add_handler(CallbackQueryHandler(rating_handler, pattern="^rate_"))
    app.add_handler(CallbackQueryHandler(support_topic_handler, pattern="^support_topic_"))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^(publish_review|reject_review|ticket_accepted|ticket_closed|booking_confirm|booking_cancel)$"))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL, handle_message))
    print("✅ Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
