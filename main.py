import asyncio
from aiogram import Bot, Dispatcher
from app.handlers import router
from app.database.models import async_main


async def main():
    await async_main()
    # подключение бота
    bot = Bot(token='8215499307:AAGDgFRBN_F8Tk8gw3v01AT-AMdBNUJgWzA')
    dp = Dispatcher()  # обработчик
    dp.include_router(router)
    await dp.start_polling(bot)  # мониторит обновление бота

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')
