import re
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import app.keyboard as kb


async def validate_site(message: Message, state: FSMContext) -> bool:
    site = message.text.strip()

    if not site:
        await message.answer(
            "❌ Название сайта не может быть пустым. Попробуйте еще раз:",
            reply_markup=kb.cancel_kb
        )
        return False

    # Увеличиваем лимит для зашифрованных данных
    if len(site) > 150:
        await message.answer(
            "❌ Название сайта слишком длинное (макс. 150 символов). Попробуйте еще раз:",
            reply_markup=kb.cancel_kb
        )
        return False

    if not re.search(r'[a-zA-Zа-яА-Я0-9]', site):
        await message.answer(
            "❌ Название сайта должно содержать хотя бы одну букву или цифру. Попробуйте еще раз:",
            reply_markup=kb.cancel_kb
        )
        return False

    await state.update_data(site=site)
    return True


async def validate_login(message: Message, state: FSMContext) -> bool:
    # Пропускаем проверку для команды /skip
    if message.text == "/skip":
        return True

    login = message.text.strip()

    if not login:
        await message.answer(
            "❌ Логин не может быть пустым. Попробуйте еще раз:",
            reply_markup=kb.cancel_kb
        )
        return False

    # Увеличиваем лимит для зашифрованных данных
    if len(login) > 200:
        await message.answer(
            "❌ Логин слишком длинный (макс. 200 символов). Попробуйте еще раз:",
            reply_markup=kb.cancel_kb
        )
        return False

    if not re.search(r'[a-zA-Zа-яА-Я0-9@._-]', login):
        await message.answer(
            "❌ Логин содержит недопустимые символы. Попробуйте еще раз:",
            reply_markup=kb.cancel_kb
        )
        return False

    await state.update_data(login=login)
    return True


async def validate_password(message: Message, state: FSMContext) -> bool:
    password = message.text

    if not password:
        await message.answer(
            "❌ Пароль не может быть пустым. Попробуйте еще раз:",
            reply_markup=kb.cancel_kb
        )
        return False

    if len(password) < 4:
        await message.answer(
            "❌ Пароль слишком короткий (мин. 4 символа). Попробуйте еще раз:",
            reply_markup=kb.cancel_kb
        )
        return False

    # Увеличиваем лимит для зашифрованных данных
    if len(password) > 150:
        await message.answer(
            "❌ Пароль слишком длинный (макс. 150 символов). Попробуйте еще раз:",
            reply_markup=kb.cancel_kb
        )
        return False

    await state.update_data(password=password)
    return True
