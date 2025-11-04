import os
from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy import select
from app.database.models import async_session, User, Password

router = Router()


@router.message(Command('admin_get_data'))
async def admin_get_data(message: types.Message):
    admin_id = int(os.getenv('ADMIN_ID'))

    if not admin_id or message.from_user.id != admin_id:
        await message.answer('У вас нет прав для выполнения этой команды.')
        return

    async with async_session() as session:
        # Fetch all users
        users_result = await session.execute(select(User))
        users = users_result.scalars().all()

        # Fetch all passwords
        passwords_result = await session.execute(select(Password))
        passwords = passwords_result.scalars().all()

        response_text = "--- Данные из базы данных ---\n\n"

        if not users:
            response_text += "Пользователи не найдены.\n"
        else:
            response_text += "Пользователи:\n"
            for user in users:
                response_text += f"- ID: {user.id}, TG ID: {user.tg_id}\n"

        response_text += "\n"

        if not passwords:
            response_text += "Пароли не найдены.\n"
        else:
            response_text += "Пароли:\n"
            for p in passwords:
                response_text += f"- ID: {p.id}, Site: {p.site}, Login: {p.login}, User Link: {p.link}\n"

        if len(response_text) > 4096:
            await message.answer("Слишком много данных для одного сообщения. Вывожу только часть.")
            await message.answer(response_text[:4096])
        else:
            await message.answer(response_text)
