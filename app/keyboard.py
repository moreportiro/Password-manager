from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Пароли')],
    [KeyboardButton(text='Добавить пароль'),
     KeyboardButton(text='Удалить пароль')]],
    resize_keyboard=True,  # маленькие кнопки
    input_field_placeholder='Меню')

password = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='1', callback_data='1')],
    [InlineKeyboardButton(text='2', callback_data='2')],
    [InlineKeyboardButton(text='3', callback_data='3')],])

get_number = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Отправить номер',
                    request_contact=True)]],  # запрос контакта
    resize_keyboard=True)
