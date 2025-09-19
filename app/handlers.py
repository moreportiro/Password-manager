from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import app.keyboard as kb
import app.database.requests as rq

router = Router()

# Состояния для добавления пароля


class AddPassword(StatesGroup):
    site = State()
    password = State()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await rq.set_user(message.from_user.id)
    await message.answer(
        '🔐 Менеджер паролей [beta]\n\n'
        'Выберите действие:',
        reply_markup=kb.main_inline
    )


@router.callback_query(F.data == 'show_passwords')
async def show_passwords(callback: CallbackQuery):
    user = await rq.set_user(callback.from_user.id)
    await callback.message.edit_text(
        '🔐 Ваши пароли:',
        reply_markup=await kb.passwords(user.id)
    )


@router.callback_query(F.data.startswith('password_'))
async def password(callback: CallbackQuery):
    try:
        password_id = int(callback.data.split('_')[1])
        password_obj = await rq.get_password_by_id(password_id)

        if password_obj:
            await callback.message.edit_text(
                f"🔐 Пароль для <b>{password_obj.site}</b>:\n\n"
                f"🔑 Пароль: <b>{password_obj.password}</b>\n\n"
                f"⚠️ Не делитесь этим паролем ни с кем!",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="↩️ Назад к списку", callback_data="back_to_passwords")],
                    [InlineKeyboardButton(
                        text="🏠 На главную", callback_data="to_main")]
                ])
            )
            await callback.answer()
        else:
            await callback.answer("❌ Пароль не найден", show_alert=True)
    except Exception as e:
        print(f"Error showing password: {e}")
        await callback.answer("❌ Ошибка при получении пароля", show_alert=True)


@router.callback_query(F.data == "back_to_passwords")
async def back_to_passwords(callback: CallbackQuery):
    user = await rq.set_user(callback.from_user.id)
    await callback.message.edit_text(
        "🔐 Ваши пароли:",
        reply_markup=await kb.passwords(user.id)
    )


@router.callback_query(F.data == "to_main")
async def to_main(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔐 Менеджер паролей [beta]\n\n"
        "Выберите действие:",
        reply_markup=kb.main_inline
    )


@router.callback_query(F.data == "no_passwords")
async def no_passwords(callback: CallbackQuery):
    await callback.answer("📭 У вас пока нет сохраненных паролей", show_alert=True)

# Добавление пароля - начало


@router.callback_query(F.data == "add_password")
@router.callback_query(F.data == "add_password")
async def add_password_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите название сайта или сервиса:",
        reply_markup=kb.cancel_kb
    )
    await state.set_state(AddPassword.site)
    await callback.answer()

# Обработка отмены


@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Действие отменено.",
        reply_markup=kb.main_inline
    )
    await callback.answer()

# Обработка ввода сайта


@router.message(AddPassword.site)
async def add_site(message: Message, state: FSMContext):
    await state.update_data(site=message.text)
    await message.answer(
        "Введите пароль:",
        reply_markup=kb.cancel_kb
    )
    await state.set_state(AddPassword.password)

# Обработка ввода пароля и сохранение


@router.message(AddPassword.password)
async def add_password_final(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    data = await state.get_data()
    await state.clear()

    user = await rq.set_user(message.from_user.id)
    await rq.add_password(user.id, data['site'], data['password'])

    await message.answer(
        f"✅ Пароль для <b>{data['site']}</b> успешно добавлен!",
        parse_mode='HTML',
        reply_markup=kb.main_inline
    )

# Удаление пароля - показ списка для удаления


@router.callback_query(F.data == "delete_password")
async def delete_password_start(callback: CallbackQuery):
    user = await rq.set_user(callback.from_user.id)
    await callback.message.edit_text(
        "Выберите пароль для удаления:",
        reply_markup=await kb.delete_passwords_keyboard(user.id)
    )
    await callback.answer()

# Обработка удаления пароля


@router.callback_query(F.data.startswith('delete_'))
async def delete_password_confirm(callback: CallbackQuery):
    password_id = int(callback.data.split('_')[1])

    # Создаем клавиатуру подтверждения
    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить",
                              callback_data=f"confirm_delete_{password_id}")],
        [InlineKeyboardButton(text="❌ Нет, отмена",
                              callback_data="cancel_delete")]
    ])

    password_obj = await rq.get_password_by_id(password_id)
    if password_obj:
        await callback.message.edit_text(
            f"Вы уверены, что хотите удалить пароль для <b>{password_obj.site}</b>?",
            parse_mode='HTML',
            reply_markup=confirm_kb
        )
    else:
        await callback.answer("❌ Пароль не найден", show_alert=True)

    await callback.answer()

# Подтверждение удаления


@router.callback_query(F.data.startswith('confirm_delete_'))
async def delete_password_final(callback: CallbackQuery):
    password_id = int(callback.data.split('_')[2])
    success = await rq.delete_password(password_id)

    if success:
        user = await rq.set_user(callback.from_user.id)
        await callback.message.edit_text(
            "✅ Пароль успешно удален!",
            reply_markup=await kb.delete_passwords_keyboard(user.id)
        )
    else:
        await callback.answer("❌ Ошибка при удалении пароля", show_alert=True)

    await callback.answer()

# Отмена удаления


@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery):
    user = await rq.set_user(callback.from_user.id)
    await callback.message.edit_text(
        "Выберите пароль для удаления:",
        reply_markup=await kb.delete_passwords_keyboard(user.id)
    )
    await callback.answer()


@router.callback_query(F.data == "no_passwords_to_delete")
async def no_passwords_to_delete(callback: CallbackQuery):
    await callback.answer("📭 Нет паролей для удаления", show_alert=True)
