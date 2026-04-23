import logging
import asyncio

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

# ================= НАСТРОЙКИ (ВСТАВЬТЕ СВОИ ДАННЫЕ ТУТ) =================
BOT_TOKEN = "8631591243:AAEOvymZJCIGXMzUSTeI78n1JwjBDCPEnys"
CHANNEL_ID = "1003418019731"  # Укажите юзернейм канала (с @) или ID (например, -100...)
# ========================================================================

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_formatted_chat_id(chat_id: str):
    """Приводит ID к правильному формату для Telegram."""
    chat_id = str(chat_id).strip()
    if chat_id.startswith('@'):
        return chat_id
    if not chat_id.startswith('-'):
        # Если это просто цифры, добавляем -100 (стандарт для каналов)
        if not chat_id.startswith('100'):
            return f"-100{chat_id}"
        else:
            return f"-{chat_id}"
    return chat_id

async def check_subscription(user_id: int) -> bool:
    """Проверяет, подписан ли пользователь на канал."""
    target_chat = get_formatted_chat_id(CHANNEL_ID)
    try:
        member = await bot.get_chat_member(chat_id=target_chat, user_id=user_id)
        # Статусы, которые считаются подпиской
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Ошибка проверки подписки в {target_chat}: {e}")
        # Если произошла ошибка (например, бот не админ), разрешаем писать,
        # чтобы не блокировать чат полностью из-за ошибки настройки.
        return True

@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_chat_message(message: types.Message):
    """Обработка всех сообщений в группах и супергруппах."""
    if not message.from_user or message.from_user.is_bot:
        return

    # Проверяем подписку
    is_subscribed = await check_subscription(message.from_user.id)
    
    if not is_subscribed:
        try:
            # 1. Удаляем сообщение пользователя
            await message.delete()
            logger.info(f"Удалено сообщение от {message.from_user.id} (нет подписки)")

            # 2. Формируем ссылку на канал для кнопки
            if str(CHANNEL_ID).startswith('@'):
                channel_link = f"https://t.me/{CHANNEL_ID[1:]}"
            else:
                # Если это ID, пытаемся получить ссылку через API или ставим заглушку
                try:
                    chat_info = await bot.get_chat(get_formatted_chat_id(CHANNEL_ID))
                    channel_link = chat_info.invite_link or "https://t.me/telegram"
                except:
                    channel_link = "https://t.me/telegram"

            # 3. Создаем инлайн-кнопку
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📢 Подписаться на канал", url=channel_link)]
            ])
            
            # 4. Отправляем предупреждение с упоминанием
            user_mention = message.from_user.mention_html()
            warning_msg = await message.answer(
                f"Уважаемый {user_mention}, перед тем как отправлять сообщение в чат, пожалуйста подпишитесь на канал.",
                reply_markup=kb,
                parse_mode="HTML"
            )
            
            # 5. Удаляем предупреждение через 20 секунд, чтобы не забивать чат
            await asyncio.sleep(20)
            await warning_msg.delete()

        except Exception as e:
            logger.error(f"Ошибка в handle_chat_message: {e}")

async def main():
    target_chat = get_formatted_chat_id(CHANNEL_ID)
    logger.info(f"Запуск бота... Целевой канал: {target_chat}")
    
    # Проверка прав бота в канале при запуске
    try:
        chat = await bot.get_chat(target_chat)
        logger.info(f"Связь установлена! Канал: {chat.title}")
    except Exception as e:
        logger.error(f"КРИТИЧЕСКАЯ ОШИБКА: Бот не видит канал {target_chat}!")
        logger.error(f"Причина: {e}")
        logger.error("Убедитесь, что: 1. ID/Юзернейм верный. 2. Бот добавлен в КАНАЛ как АДМИНИСТРАТОР.")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
