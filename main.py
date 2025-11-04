import asyncio
import os
from aiogram import Bot, Dispatcher
from app.handlers import router
from aiogram.types import BotCommand, BotCommandScopeChat
from app.database.models import async_main
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# для деплоя открыл сервер
app = Flask(__name__)

@app.route('/')
def home():
    return "ага"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)


async def set_bot_commands(bot: Bot):
    user_commands = [
        BotCommand(command="/start", description="Запустить бота")
    ]
    await bot.set_my_commands(user_commands)

    admin_id = int(os.getenv('ADMIN_ID'))
    if admin_id:
        admin_commands = [
            BotCommand(command="/start", description="Запустить бота"),
            BotCommand(command="/admin_get_data", description="Получить данные из БД")
        ]
        await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin_id))


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
        flask_thread = Thread(target=run_flask)
        flask_thread.start()
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')
