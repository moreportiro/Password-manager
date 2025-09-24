from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

import app.keyboard as kb
import app.database.requests as rq
from app.migration_utils import get_migration_info

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await rq.set_user(message.from_user.id)
    # Получаем информацию о миграции
    migration_info = await get_migration_info(message.from_user.id)

    welcome_text = '🔐 <b>Менеджер паролей</b>\n'

    if migration_info['needs_migration']:
        welcome_text += f"⚠️ Обнаружено {migration_info['password_count']} паролей без мастер-пароля."
        "Для обеспечения безопасности необходимо установить мастер-пароль."
    elif not migration_info['has_master_password']:
        welcome_text += "Для защиты ваших данных рекомендуется установить мастер-пароль.\n\n"

    welcome_text += 'Выберите действие:'
    await message.answer(
        welcome_text,
        reply_markup=kb.main_inline,
        parse_mode='HTML'
    )
