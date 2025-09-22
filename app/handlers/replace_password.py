from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import app.keyboard as kb
import app.database.requests as rq
from app.validators import validate_login, validate_password
from app.handlers.states import ReplacePassword
from app.password_generator import generate_yandex_like_password, safe_display_password

router = Router()


@router.callback_query(F.data == "confirm_replace_new")
async def confirm_replace_new_password(callback: CallbackQuery, state: FSMContext):
    try:
        # Получаем пользователя из базы данных по Telegram ID
        user = await rq.set_user(callback.from_user.id)
        data = await state.get_data()

        # Используем ID пользователя из базы данных
        existing_password = await rq.get_password_by_site(user.id, data['site'])

        if existing_password:
            success = await rq.update_password(
                existing_password.id,
                data['site'],
                data['login'],
                data['password']
            )

            if success:
                await callback.message.edit_text(
                    f"✅ Пароль для <b>{data['site']}</b> успешно обновлен!",
                    parse_mode='HTML'
                )
            else:
                await callback.message.edit_text(
                    "❌ Произошла ошибка при обновлении пароля."
                )
        else:
            await callback.message.edit_text(
                "❌ Пароль для замены не найден."
            )

        await state.clear()
        await callback.answer()

        await callback.message.answer(
            "Главное меню:",
            reply_markup=kb.main_inline
        )
    except Exception as e:
        print(f"Error replacing password: {e}")
        await callback.answer("❌ Ошибка при замене пароля", show_alert=True)


@router.callback_query(F.data.startswith('start_replace_'))
async def start_replace_password(callback: CallbackQuery, state: FSMContext):
    try:
        password_id = int(callback.data.split('_')[2])
        password_obj = await rq.get_password_by_id(password_id)

        if password_obj:
            await state.update_data(
                target_password_id=password_obj.id,
                site=password_obj.site,
                login=password_obj.login
            )

            await callback.message.edit_text(
                f"🔄 Замена пароля для <b>{password_obj.site}</b>\n\n"
                f"Текущий логин: <b>{password_obj.login}</b>\n\n"
                "Введите новый логин (или нажмите /skip чтобы оставить текущий):",
                parse_mode='HTML',
                reply_markup=kb.cancel_kb
            )
            await state.set_state(ReplacePassword.login)
            await callback.answer()
        else:
            await callback.answer("❌ Пароль не найден", show_alert=True)
    except Exception as e:
        print(f"Error starting password replacement: {e}")
        await callback.answer("❌ Ошибка при начале замены пароля", show_alert=True)


@router.message(ReplacePassword.login)
async def replace_login(message: Message, state: FSMContext):
    if message.text == "/skip":
        data = await state.get_data()
        await state.update_data(login=data['login'])

        await message.answer(
            "Введите новый пароль или сгенерируйте его:",
            reply_markup=kb.generate_password_kb
        )
        await state.set_state(ReplacePassword.password)
    elif await validate_login(message, state):
        await message.answer(
            "Введите новый пароль или сгенерируйте его:",
            reply_markup=kb.generate_password_kb
        )
        await state.set_state(ReplacePassword.password)


@router.callback_query(F.data == "generate_password", ReplacePassword.password)
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


@router.callback_query(F.data == "use_generated_password", ReplacePassword.password)
async def use_generated_password(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    generated_password = data.get('generated_password', '')

    if generated_password:
        success = await rq.update_password(
            data['target_password_id'],
            data['site'],
            data['login'],
            generated_password
        )

        if success:
            await callback.message.edit_text(
                f"✅ Пароль для <b>{data['site']}</b> успешно обновлен!",
                parse_mode='HTML'
            )
        else:
            await callback.message.edit_text(
                "❌ Ошибка при обновлении пароля."
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


@router.callback_query(F.data == "generate_another_password", ReplacePassword.password)
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


@router.callback_query(F.data == "enter_own_password", ReplacePassword.password)
async def enter_own_password(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите ваш пароль:",
        reply_markup=kb.cancel_kb
    )
    await state.set_state(ReplacePassword.password)
    await callback.answer()


@router.message(ReplacePassword.password)
async def replace_password_final(message: Message, state: FSMContext):
    if await validate_password(message, state):
        data = await state.get_data()

        success = await rq.update_password(
            data['target_password_id'],
            data['site'],
            data['login'],
            message.text
        )

        await state.clear()

        if success:
            await message.answer(
                f"✅ Пароль для <b>{data['site']}</b> успешно обновлен!",
                parse_mode='HTML',
                reply_markup=kb.main_inline
            )
        else:
            await message.answer(
                "❌ Произошла ошибка при обновлении пароля.",
                reply_markup=kb.main_inline
            )
