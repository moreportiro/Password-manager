from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import app.keyboard as kb
import app.database.requests as rq
from app.validators import validate_login, validate_password
from app.handlers.states import ReplacePassword

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
            "Введите новый пароль:",
            reply_markup=kb.cancel_kb
        )
        await state.set_state(ReplacePassword.password)
    elif await validate_login(message, state):
        await message.answer(
            "Введите новый пароль:",
            reply_markup=kb.cancel_kb
        )
        await state.set_state(ReplacePassword.password)


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
