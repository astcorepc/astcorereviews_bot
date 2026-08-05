# === ОТЗЫВЫ — ОДОБРИТЬ (С ФОТО И ВИДЕО, ЧИСТЫЙ ТЕКСТ) ===
if query.data == "review_approve":
    if CHANNEL_ID:
        # Получаем сохранённые медиа и чистый текст
        review_photo = context.user_data.get('review_photo')
        review_video = context.user_data.get('review_video')
        review_clean_text = context.user_data.get('review_clean_text', 'Без текста')
        rating = context.user_data.get('rating', 0)
        
        # Формируем ЧИСТЫЙ текст для канала (без служебной информации)
        # Оценка: 3 ★ (как и просил пользователь)
        channel_text = f"⭐ **Оценка: {rating} ★**\n\n{review_clean_text}"
        
        # Отправляем в канал с медиа
        if review_photo:
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=review_photo,
                caption=channel_text,
                parse_mode="Markdown"
            )
        elif review_video:
            await context.bot.send_video(
                chat_id=CHANNEL_ID,
                video=review_video,
                caption=channel_text,
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=channel_text,
                parse_mode="Markdown"
            )
        
        # Уведомляем пользователя
        user_id = context.user_data.get('review_user_id')
        if user_id:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="✅ **Ваш отзыв одобрен и опубликован в нашем канале!**\n\nСпасибо, что поделились своим мнением. ❤️",
                    parse_mode="Markdown"
                )
            except:
                pass
        
        # Обновляем сообщение у админа
        if review_photo or review_video:
            await query.edit_message_caption(
                caption="✅ **Отзыв одобрен и опубликован в канале!**\n\nПользователь уведомлён.",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                text="✅ **Отзыв одобрен и опубликован в канале!**\n\nПользователь уведомлён.",
                parse_mode="Markdown"
            )
    else:
        await query.edit_message_text(
            text="⚠️ Канал не настроен. Добавь CHANNEL_ID в Railway.",
            parse_mode="Markdown"
        )
    return
