from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

import app.keyboard as kb
import app.database.requests as rq
from app.crypto import cipher
from app.auth_manager import auth_manager
from app.validators import validate_master_password
from app.migration_utils import migrate_user_passwords_to_master_password, get_migration_info
from .states import MasterPassword

router = Router()


async def require_master_password(callback: CallbackQuery):
    """Запрашивает ввод мастер-пароля"""
    await callback.message.edit_text(
        "🔐 <b>Введите мастер-пароль</b>\n"
        "Мастер-пароль защищает все ваши сохраненные пароли.\n"
        "Без него никто не сможет получить доступ к вашим данным.",
        reply_markup=kb.cancel_kb,
        parse_mode='HTML'
    )
    return MasterPassword.enter_existing


async def require_master_password_setup(callback: CallbackQuery):
    """Запрашивает установку нового мастер-пароля"""
    await callback.message.edit_text(
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
    return MasterPassword.setup_new


@router.message(StateFilter(MasterPassword.setup_new))
async def process_master_password_setup(message: Message, state: FSMContext):
    """Обрабатывает установку нового мастер-пароля"""
    master_password = message.text

    # Удаляем сообщение с паролем для безопасности
    try:
        await message.delete()
    except:
        pass

    # Валидируем мастер-пароль
    is_valid, validation_message = await validate_master_password(master_password)

    if not is_valid:
        await message.answer(
            f"{validation_message}Попробуйте еще раз:",
            reply_markup=kb.cancel_kb
        )
        return

    # Сохраняем пароль для подтверждения
    await state.update_data(master_password=master_password)
    await state.set_state(MasterPassword.setup_confirm)

    await message.answer(
        f"{validation_message}"
        "🔄 <b>Подтвердите мастер-пароль</b>\n\n"
        "Введите мастер-пароль еще раз для подтверждения:",
        reply_markup=kb.cancel_kb,
        parse_mode='HTML'
    )


@router.message(StateFilter(MasterPassword.setup_confirm))
async def process_master_password_confirm(message: Message, state: FSMContext):
    """Обрабатывает подтверждение мастер-пароля"""
    confirmation_password = message.text

    # Удаляем сообщение с паролем
    try:
        await message.delete()
    except:
        pass

    # Получаем сохраненный пароль
    data = await state.get_data()
    original_password = data.get('master_password')

    if confirmation_password != original_password:
        await message.answer(
            "❌ Пароли не совпадают!\n"
            "Введите мастер-пароль еще раз для подтверждения:",
            reply_markup=kb.cancel_kb
        )
        return
    # Получаем информацию о миграции
    user = await rq.get_user_by_tg_id(message.from_user.id)
    migration_info = await get_migration_info(message.from_user.id)

    # Хешируем и сохраняем мастер-пароль
    password_hash = cipher.hash_master_password(original_password)
    success = await rq.set_master_password(message.from_user.id, password_hash)

    if success:
        # Аутентифицируем пользователя
        auth_manager.authenticate_user(message.from_user.id, original_password)
        success_message = "✅ <b>Мастер-пароль успешно установлен!</b>\n"

        # Если нужна миграция, выполняем её
        if migration_info['needs_migration']:
            try:
                migrated_count = await migrate_user_passwords_to_master_password(
                    user.id, message.from_user.id, original_password
                )
                success_message += f"🔄 Мигрировано {migrated_count} паролей к новой схеме шифрования."
            except Exception as e:
                print(
                    f"Ошибка миграции для пользователя {message.from_user.id}: {e}")
                success_message += "⚠️ Частичная ошибка при миграции. Некоторые пароли могут потребовать повторного ввода."

        success_message += "Теперь ваши пароли защищены дополнительным уровнем безопасности."
        "Выберите действие:"
        await state.clear()
        await message.answer(
            success_message,
            reply_markup=kb.main_inline,
            parse_mode='HTML'
        )
    else:
        await message.answer(
            "❌ Ошибка при сохранении мастер-пароля. Попробуйте еще раз.",
            reply_markup=kb.main_inline
        )
        await state.clear()


@router.message(StateFilter(MasterPassword.enter_existing))
async def process_master_password_enter(message: Message, state: FSMContext):
    """Обрабатывает ввод существующего мастер-пароля"""
    master_password = message.text

    # Удаляем сообщение с паролем
    try:
        await message.delete()
    except:
        pass

    # Получаем пользователя и проверяем мастер-пароль
    user = await rq.get_user_by_tg_id(message.from_user.id)
    if not user or not user.master_password_hash:
        await message.answer(
            "❌ У вас не установлен мастер-пароль.",
            reply_markup=kb.main_inline
        )
        await state.clear()
        return

    # Проверяем пароль
    if cipher.verify_master_password(master_password, user.master_password_hash):
        # Аутентифицируем пользователя
        auth_manager.authenticate_user(message.from_user.id, master_password)

        await state.clear()
        await message.answer(
            "✅ <b>Добро пожаловать!\n</b>"
            "Мастер-пароль принят. Выберите действие:",
            reply_markup=kb.main_inline,
            parse_mode='HTML'
        )
    else:
        await message.answer(
            "❌ <b>Неверный мастер-пароль!\n</b>"
            "Попробуйте еще раз или нажмите Отмена для возврата в главное меню.\n\n"
            "🔄 Забыли пароль? Используйте /reset_master_password для полного сброса данных.",
            reply_markup=kb.cancel_kb,
            parse_mode='HTML'
        )


@router.callback_query(F.data == "reset_master_password")
async def process_reset_master_password(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает запрос на сброс мастер-пароля"""
    await callback.message.edit_text(
        "⚠️ <b>ВНИМАНИЕ!\n\n</b>"
        "Сброс мастер-пароля приведет к <b>ПОЛНОМУ УДАЛЕНИЮ</b> всех ваших сохраненных паролей!\n"
        "Это действие <b>НЕОБРАТИМО</b>.\n"
        "Вы уверены, что хотите продолжить?\n"
        "Отправьте <code>ПОДТВЕРЖДАЮ СБРОС</code> для подтверждения:",
        reply_markup=kb.cancel_kb,
        parse_mode='HTML'
    )
    await state.set_state(MasterPassword.reset_confirm)


@router.message(StateFilter(MasterPassword.reset_confirm))
async def process_reset_confirmation(message: Message, state: FSMContext):
    """Обрабатывает подтверждение сброса мастер-пароля"""
    if message.text == "ПОДТВЕРЖДАЮ СБРОС":
        success = await rq.reset_user_data(message.from_user.id)

        if success:
            await state.clear()
            await message.answer(
                "✅ <b>Данные успешно сброшены</b>\n\n"
                "Все ваши пароли и мастер-пароль удалены.\n"
                "Теперь вы можете установить новый мастер-пароль.\n\n"
                "Выберите действие:",
                reply_markup=kb.main_inline,
                parse_mode='HTML'
            )
        else:
            await message.answer(
                "❌ Ошибка при сбросе данных. Попробуйте еще раз.",
                reply_markup=kb.main_inline
            )
            await state.clear()
    else:
        await message.answer(
            "❌ Неверный код подтверждения."
            "Для подтверждения сброса отправьте точно: <code>ПОДТВЕРЖДАЮ СБРОС</code>",
            reply_markup=kb.cancel_kb,
            parse_mode='HTML'
        )


# Команда для сброса мастер-пароля
@router.message(F.text == "/reset_master_password")
async def cmd_reset_master_password(message: Message, state: FSMContext):
    """Команда для сброса мастер-пароля"""
    await state.clear()
    await process_reset_master_password(CallbackQuery(
        id="cmd",
        from_user=message.from_user,
        message=message,
        data="reset_master_password"
    ), state)
