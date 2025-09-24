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
    if message.text == "/skip":
        return True

    login = message.text.strip()

    if not login:
        await message.answer(
            "❌ Логин не может быть пустым. Попробуйте еще раз:",
            reply_markup=kb.cancel_kb
        )
        return False

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

    if len(password) > 150:
        await message.answer(
            "❌ Пароль слишком длинный (макс. 150 символов). Попробуйте еще раз:",
            reply_markup=kb.cancel_kb
        )
        return False

    await state.update_data(password=password)
    return True


async def validate_master_password(password: str) -> tuple[bool, str]:
    """
    Валидация мастер-пароля по требованиям Яндекса:
    - Минимум 8 символов
    - Обязательно буквы и цифры
    - Желательно спецсимволы
    """
    if len(password) < 8:
        return False, "❌ Мастер-пароль должен содержать минимум 8 символов"

    if len(password) > 128:
        return False, "❌ Мастер-пароль слишком длинный (макс. 128 символов)"

    # проверка букв
    if not re.search(r'[a-zA-Zа-яА-Я]', password):
        return False, "❌ Мастер-пароль должен содержать буквы"

    # проверка цифр
    if not re.search(r'[0-9]', password):
        return False, "❌ Мастер-пароль должен содержать цифры"

    # хотя бы один спецсимвол
    has_special = re.search(
        r'[!@#$%^&*()_+\-=\[\]{};\':\"\|,.<>/?`~]', password)

    if not has_special:
        # если нет спецсимволов, требует смешанный регистр для компенсации
        has_upper = re.search(r'[A-ZА-Я]', password)
        has_lower = re.search(r'[a-zа-я]', password)

        if not (has_upper and has_lower):
            return False, "❌ Мастер-пароль должен содержать буквы разного регистра или спецсимволы\n"

    return True, "✅ Мастер-пароль соответствует требованиям безопасности\n"
