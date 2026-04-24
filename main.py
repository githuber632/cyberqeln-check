import logging
import asyncio

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "8631591243:AAEOvymZJCIGXMzUSTeI78n1JwjBDCPEnys"
# Если это числовой ID, пишем его БЕЗ кавычек и БЕЗ @, либо строкой с -100
CHANNEL_ID = "-1003418019731" 
# =============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def check_subscription(user_id: int) -> bool:
    try:
        # Прямо используем CHANNEL_ID
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        # Если бот не может проверить (например, не админ), временно разрешаем
        # ВНИМАНИЕ: Если здесь будет ошибка 'chat not found', бот не будет удалять сообщения.
        return False # Поменял на False, чтобы при ошибке он считал пользователя НЕ подписанным (для теста)

@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_chat_message(message: types.Message):
    # Игнорируем посты канала в комментариях
    if message.is_automatic_forward or message.sender_chat:
        return

    # Игнорируем ботов
    if message.from_user and message.from_user.is_bot:
        return

    # Проверяем подписку
    is_subscribed = await check_subscription(message.from_user.id)
    
    if not is_subscribed:
        try:
            await message.delete()
            
            # Ссылка на канал (замените на реальную ссылку, если ID числовой)
            channel_link = "https://t.me/cyberqeln_uz" # Ссылка для приватных каналов или юзернейм
            
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📢 Подписаться на канал", url=channel_link)]
            ])
            
            user_mention = message.from_user.mention_html()
            warning_msg = await message.answer(
                f"Уважаемый {user_mention}, перед тем как отправлять сообщение в чат, пожалуйста подпишитесь на канал.",
                reply_markup=kb,
                parse_mode="HTML"
            )
            
            await asyncio.sleep(15)
            await warning_msg.delete()
        except Exception as e:
            logger.error(f"Ошибка при удалении: {e}")

async def main():
    logger.info(f"Запуск... Канал: {CHANNEL_ID}")
    try:
        chat = await bot.get_chat(CHANNEL_ID)
        logger.info(f"Связь установлена: {chat.title}")
    except Exception as e:
        logger.error(f"ОШИБКА: Бот не видит канал {CHANNEL_ID}. Проверьте ID и права админа. Ошибка: {e}")

    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
