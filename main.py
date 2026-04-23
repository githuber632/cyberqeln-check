import logging
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

# ОПРЕДЕЛЯЕМ ПУТЬ К .ENV ФАЙЛУ ЯВНО
BASE_DIR = Path(__file__).resolve().parent
dotenv_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=dotenv_path)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if not BOT_TOKEN:
    print(f"ОШИБКА: BOT_TOKEN не найден в {dotenv_path}")
    exit(1)

# Инициализация бота
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
    target_chat = get_formatted_chat_id(CHANNEL_ID)
    try:
        member = await bot.get_chat_member(chat_id=target_chat, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Ошибка проверки подписки в {target_chat}: {e}")
        # Если бот не админ или чат не найден, разрешаем писать, чтобы не блокировать чат совсем
        return True

@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_chat_message(message: types.Message):
    if not message.from_user or message.from_user.is_bot:
        return

    is_subscribed = await check_subscription(message.from_user.id)
    
    if not is_subscribed:
        try:
            await message.delete()
            
            # Формируем ссылку на канал
            if str(CHANNEL_ID).startswith('@'):
                channel_link = f"https://t.me/{CHANNEL_ID[1:]}"
            else:
                # Попробуем получить ссылку на чат, если мы админы
                try:
                    chat_info = await bot.get_chat(get_formatted_chat_id(CHANNEL_ID))
                    channel_link = chat_info.invite_link or "https://t.me/telegram"
                except:
                    channel_link = "https://t.me/telegram"

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📢 Подписаться", url=channel_link)]
            ])
            
            warning_msg = await message.answer(
                f"Уважаемый {message.from_user.mention_html()}, перед тем как отправлять сообщение в чат, пожалуйста подпишитесь на канал.",
                reply_markup=kb,
                parse_mode="HTML"
            )
            
            await asyncio.sleep(20)
            await warning_msg.delete()
        except Exception as e:
            logger.error(f"Ошибка в handle_chat_message: {e}")

async def main():
    target_chat = get_formatted_chat_id(CHANNEL_ID)
    logger.info(f"Бот запущен. Целевой канал: {target_chat}")
    
    # Проверка доступа к каналу при старте
    try:
        chat = await bot.get_chat(target_chat)
        logger.info(f"Успешное подключение к каналу: {chat.title}")
    except Exception as e:
        logger.error(f"ВНИМАНИЕ: Бот не видит канал {target_chat}. Ошибка: {e}")
        logger.error("Убедитесь, что бот добавлен в КАНАЛ как АДМИНИСТРАТОР.")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
