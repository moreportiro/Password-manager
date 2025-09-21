from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.database.requests import get_passwords
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Главное меню с inline-кнопками
main_inline = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔐 Мои пароли',
                          callback_data='show_passwords')],
    [InlineKeyboardButton(text='➕ Добавить пароль', callback_data='add_password'),
     InlineKeyboardButton(text='🗑️ Удалить пароль', callback_data='delete_password')]
])

# Клавиатура для отмены действия
cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_action')]
])

# Клавиатура для генерации пароля
generate_password_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🎲 Сгенерировать пароль',
                          callback_data='generate_password')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_action')]
])

# Клавиатура для подтверждения использования сгенерированного пароля
confirm_generated_password_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Использовать этот пароль',
                          callback_data='use_generated_password')],
    [InlineKeyboardButton(text='🔄 Сгенерировать другой',
                          callback_data='generate_another_password')],
    [InlineKeyboardButton(text='📝 Ввести свой пароль',
                          callback_data='enter_own_password')]
])


async def passwords(user_id):
    try:
        all_passwords = await get_passwords(user_id)
        keyboard = InlineKeyboardBuilder()

        if all_passwords:
            for password in all_passwords:
                keyboard.add(InlineKeyboardButton(
                    text=f"🌐 {password.site}",
                    callback_data=f"password_{password.id}"
                ))
        else:
            keyboard.add(InlineKeyboardButton(
                text="📭 Нет паролей",
                callback_data="no_passwords"
            ))

        keyboard.add(InlineKeyboardButton(
            text='🏠 На главную',
            callback_data='to_main'
        ))
        return keyboard.adjust(2).as_markup()
    except Exception as e:
        print(f"Error in passwords(): {e}")
        error_keyboard = InlineKeyboardBuilder()
        error_keyboard.add(InlineKeyboardButton(
            text="❌ Ошибка загрузки",
            callback_data="error"
        ))
        error_keyboard.add(InlineKeyboardButton(
            text='🏠 На главную',
            callback_data='to_main'
        ))
        return error_keyboard.adjust(1).as_markup()


async def delete_passwords_keyboard(user_id):
    try:
        all_passwords = await get_passwords(user_id)
        keyboard = InlineKeyboardBuilder()

        if all_passwords:
            for password in all_passwords:
                keyboard.add(InlineKeyboardButton(
                    text=f"🗑️ {password.site}",
                    callback_data=f"delete_{password.id}"
                ))
        else:
            keyboard.add(InlineKeyboardButton(
                text="📭 Нет паролей для удаления",
                callback_data="no_passwords_to_delete"
            ))

        keyboard.add(InlineKeyboardButton(
            text='🏠 На главную',
            callback_data='to_main'
        ))
        return keyboard.adjust(2).as_markup()
    except Exception as e:
        print(f"Error in delete_passwords_keyboard(): {e}")
        error_keyboard = InlineKeyboardBuilder()
        error_keyboard.add(InlineKeyboardButton(
            text="❌ Ошибка загрузки",
            callback_data="error"
        ))
        error_keyboard.add(InlineKeyboardButton(
            text='🏠 На главную',
            callback_data='to_main'
        ))
        return error_keyboard.adjust(1).as_markup()
