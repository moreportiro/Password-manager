from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import app.database.requests as rq
import app.keyboard as kb
from app.auth_manager import auth_manager


class AuthMiddleware(BaseMiddleware):
    """
    Middleware для проверки аутентификации перед доступом к защищенным функциям
    """

    # Список callback_data, которые требуют аутентификации
    PROTECTED_CALLBACKS = {
        'show_passwords',
        'add_password',
        'delete_password',
    }

    # Callback_data, которые начинаются с этих префиксов и требуют аутентификации
    PROTECTED_PREFIXES = {
        'password_',
        'delete_',
        'replace_',
    }

    # Состояния, которые требуют аутентификации
    PROTECTED_STATES = {
        'AddPassword',
        'ReplacePassword',
    }

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:

        # Определяем, нужна ли проверка аутентификации
        needs_auth = False

        if isinstance(event, CallbackQuery):
            callback_data = event.data

            # Проверяем защищенные callback_data
            if callback_data in self.PROTECTED_CALLBACKS:
                needs_auth = True

            # Проверяем защищенные префиксы
            for prefix in self.PROTECTED_PREFIXES:
                if callback_data.startswith(prefix):
                    needs_auth = True
                    break

        elif isinstance(event, Message):
            # Проверяем состояние пользователя
            state: FSMContext = data.get('state')
            if state:
                current_state = await state.get_state()
                if current_state:
                    state_group = current_state.split(':')[0]
                    if state_group in self.PROTECTED_STATES:
                        needs_auth = True

        # Если аутентификация не нужна, продолжаем выполнение
        if not needs_auth:
            return await handler(event, data)

        # Проверяем аутентификацию
        tg_id = event.from_user.id

        # Проверяем, установлен ли мастер-пароль
        has_master = await rq.has_master_password(tg_id)

        if not has_master:
            # Мастер-пароль не установлен - требуем установки
            if isinstance(event, CallbackQuery):
                await event.answer("Необходимо установить мастер-пароль", show_alert=True)
                state = data['state']
                await event.message.edit_text(
                    "🔐 <b>Установка мастер-пароля</b>\n"
                    "Для защиты ваших паролей необходимо установить мастер-пароль.\n\n"
                    "<b>Требования к мастер-паролю:</b>\n"
                    "• Минимум 8 символов\n"
                    "• Должен содержать буквы и цифры\n"
                    "• Рекомендуются спецсимволы\n"
                    "• Разный регистр букв (если нет спецсимволов)\n\n"
                    "⚠️ <b>ВАЖНО:</b> Запомните этот пароль! При его утере все данные будут потеряны.\n\n"
                    "Введите новый мастер-пароль:",
                    reply_markup=kb.cancel_kb,
                    parse_mode='HTML'
                )
                await state.set_state('MasterPassword:setup_new')
                return

        # Мастер-пароль установлен - проверяем аутентификацию
        if not auth_manager.is_authenticated(tg_id):
            # Пользователь не аутентифицирован - требуем ввода мастер-пароля
            if isinstance(event, CallbackQuery):
                await event.answer("Необходимо ввести мастер-пароль", show_alert=True)
                state = data['state']
                await event.message.edit_text(
                    "🔐 <b>Введите мастер-пароль\n</b>"
                    "Мастер-пароль защищает все ваши сохраненные пароли.\n"
                    "Без него никто не сможет получить доступ к вашим данным.\n",
                    reply_markup=kb.cancel_with_reset_kb,
                    parse_mode='HTML'
                )
                await state.set_state('MasterPassword:enter_existing')
                return

        # Пользователь аутентифицирован - продолжаем выполнение
        return await handler(event, data)
