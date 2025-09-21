from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import app.keyboard as kb
import app.database.requests as rq

router = Router()


@router.callback_query(F.data == "delete_password")
async def delete_password_start(callback: CallbackQuery):
    user = await rq.set_user(callback.from_user.id)
    await callback.message.edit_text(
        "Выберите пароль для удаления:",
        reply_markup=await kb.delete_passwords_keyboard(user.id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith('delete_'))
async def delete_password_confirm(callback: CallbackQuery):
    password_id = int(callback.data.split('_')[1])

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
