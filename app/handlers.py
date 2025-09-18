from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import app.keyboard as kb

router = Router()


@router.message(CommandStart())  # обработчик сообщений
async def cmd_start(message: Message):
    # answer - сообщение, reply_markup - открыть клавиатуру
    await message.answer('Привет', reply_markup=kb.main)
    await message.reply('Kak Dela')  # reply - ответ на сообщение


@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('Help')


@router.message(F.text == 'Пароли')
async def password(message: Message):
    await message.answer('Выберите', reply_markup=kb.password)


@router.callback_query(F.data == '1')  # обработчик колбека
async def one(callback: CallbackQuery):
    # уведомление, кнопка не подсвечивается после, show_alert - всплывыющее окно
    await callback.answer('OnEOnE', show_alert=True)
    await callback.message.answer('oneoneoneone')
