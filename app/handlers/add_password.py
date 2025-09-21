from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import app.keyboard as kb
import app.database.requests as rq
from app.validators import validate_site, validate_login, validate_password
from app.handlers.states import AddPassword
from app.password_generator import generate_yandex_like_password, safe_display_password

router = Router()


@router.callback_query(F.data == "add_password")
async def add_password_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите название сайта или сервиса:",
        reply_markup=kb.cancel_kb
    )
    await state.set_state(AddPassword.site)
    await callback.answer()


@router.message(AddPassword.site)
async def add_site(message: Message, state: FSMContext):
    if await validate_site(message, state):
        await message.answer(
            "Введите логин или email:",
            reply_markup=kb.cancel_kb
        )
        await state.set_state(AddPassword.login)


@router.message(AddPassword.login)
async def add_login(message: Message, state: FSMContext):
    if await validate_login(message, state):
        await message.answer(
            "Введите пароль или сгенерируйте его:",
            reply_markup=kb.generate_password_kb
        )
        await state.set_state(AddPassword.password)


@router.callback_query(F.data == "generate_password", AddPassword.password)
async def generate_password_handler(callback: CallbackQuery, state: FSMContext):
    # Генерируем пароль в стиле Яндекс
    generated_password = generate_yandex_like_password()

    # Сохраняем сгенерированный пароль в состоянии
    await state.update_data(generated_password=generated_password)

    # Безопасно отображаем пароль
    password_display = safe_display_password(generated_password)

    await callback.message.edit_text(
        f"🔐 Сгенерированный пароль: {password_display}\n\n"
        "Вы можете использовать его или выбрать другой вариант:",
        parse_mode='HTML',
        reply_markup=kb.confirm_generated_password_kb
    )
    await callback.answer()


@router.callback_query(F.data == "use_generated_password", AddPassword.password)
async def use_generated_password(callback: CallbackQuery, state: FSMContext):
    # Получаем пользователя из базы данных по Telegram ID
    user = await rq.set_user(callback.from_user.id)
    data = await state.get_data()
    generated_password = data.get('generated_password', '')

    if generated_password:
        # Используем ID пользователя из базы данных
        success = await rq.add_password(user.id, data['site'], data['login'], generated_password)

        if success:
            await callback.message.edit_text(
                f"✅ Пароль для <b>{data['site']}</b> успешно добавлен!",
                parse_mode='HTML'
            )
        else:
            await callback.message.edit_text(
                "❌ Ошибка при сохранении пароля."
            )
    else:
        await callback.answer("❌ Нет сгенерированного пароля. Сгенерируйте сначала.")

    await state.clear()
    await callback.answer()

    # Показываем главное меню
    await callback.message.answer(
        "Главное меню:",
        reply_markup=kb.main_inline
    )


@router.callback_query(F.data == "generate_another_password", AddPassword.password)
async def generate_another_password(callback: CallbackQuery, state: FSMContext):
    # Генерируем новый пароль
    generated_password = generate_yandex_like_password()

    # Сохраняем новый пароль в состоянии
    await state.update_data(generated_password=generated_password)

    # Безопасно отображаем пароль
    password_display = safe_display_password(generated_password)

    await callback.message.edit_text(
        f"🔐 Новый сгенерированный пароль: {password_display}\n\n"
        "Вы можете использовать его или выбрать другой вариант:",
        parse_mode='HTML',
        reply_markup=kb.confirm_generated_password_kb
    )
    await callback.answer()


@router.callback_query(F.data == "enter_own_password", AddPassword.password)
async def enter_own_password(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите ваш пароль:",
        reply_markup=kb.cancel_kb
    )
    await state.set_state(AddPassword.password)
    await callback.answer()


@router.message(AddPassword.password)
async def add_password_final(message: Message, state: FSMContext):
    if await validate_password(message, state):
        data = await state.get_data()

        user = await rq.set_user(message.from_user.id)

        # Проверяем, нет ли уже пароля для этого сайта
        if await rq.check_password_exists(user.id, data['site']):
            # Сохраняем данные в состоянии для возможной замены
            await state.update_data(
                site=data['site'],
                login=data['login'],
                password=message.text
            )

            # Спрашиваем подтверждение замены
            await message.answer(
                f"❌ Пароль для <b>{data['site']}</b> уже существует.\n"
                "Хотите заменить его?",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="✅ Да, заменить", callback_data="confirm_replace_new")],
                    [InlineKeyboardButton(
                        text="❌ Нет, отменить", callback_data="cancel_action")]
                ])
            )
            return

        # Если дубликата нет, сохраняем пароль
        await rq.add_password(user.id, data['site'], data['login'], message.text)
        await state.clear()

        await message.answer(
            f"✅ Пароль для <b>{data['site']}</b> успешно добавлен!",
            parse_mode='HTML',
            reply_markup=kb.main_inline
        )
