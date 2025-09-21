from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

import app.keyboard as kb
import app.database.requests as rq

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await rq.set_user(message.from_user.id)
    await message.answer(
        '🔐 Менеджер паролей\n\n'
        'Выберите действие:',
        reply_markup=kb.main_inline
    )
