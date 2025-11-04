import asyncio
import os
from aiogram import Bot, Dispatcher
from app.handlers import router
from aiogram.types import BotCommand
from app.database.models import async_main
from dotenv import load_dotenv


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Запустить бота")
    ]
    await bot.set_my_commands(commands)


async def main():
    load_dotenv()
    await async_main()
    # подключение бота
    bot = Bot(token=os.getenv('BOT_TOKEN'))
    dp = Dispatcher()  # обработчик
    await set_bot_commands(bot)
    dp.include_router(router)
    await dp.start_polling(bot)  # мониторит обновление бота

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')
