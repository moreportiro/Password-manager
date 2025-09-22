from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import html

import app.keyboard as kb
import app.database.requests as rq

router = Router()


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
            # Экранируем специальные HTML-символы
            escaped_site = html.escape(password_obj.site)
            escaped_login = html.escape(password_obj.login)
            escaped_password = html.escape(password_obj.password)

            await callback.message.edit_text(
                f"🔐 Пароль для <b>{escaped_site}</b>:\n\n"
                f"👤 Логин: <b>{escaped_login}</b>\n"
                f"🔑 Пароль: <b>{escaped_password}</b>\n\n"
                f"⚠️ Не делитесь этим паролем ни с кем!",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="🔄 Заменить пароль", callback_data=f"start_replace_{password_obj.id}")],
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
        "🔐 Менеджер паролей\n\n"
        "Выберите действие:",
        reply_markup=kb.main_inline
    )


@router.callback_query(F.data == "no_passwords")
async def no_passwords(callback: CallbackQuery):
    await callback.answer("📭 У вас пока нет сохраненных паролей", show_alert=True)
