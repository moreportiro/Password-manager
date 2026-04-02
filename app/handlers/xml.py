"""
app/handlers/xml.py
Хэндлеры для экспорта и импорта паролей в формате XML.

Уже подключён в __init__.py — просто добавь строки из комментария внизу файла.
"""

import io
from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.xml_manager import export_passwords_to_xml, import_passwords_from_xml, XMLImportError
from app.auth_manager import auth_manager
import app.database.requests as rq
import app.keyboard as kb

router = Router()


class XMLStates(StatesGroup):
    waiting_for_xml_file = State()


# ─── ЭКСПОРТ ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "export_xml")
async def cmd_export_xml(callback, state: FSMContext):
    tg_id = callback.from_user.id

    # Проверяем аутентификацию через auth_manager (как в остальных хэндлерах)
    if not auth_manager.is_authenticated(tg_id):
        await callback.answer("🔒 Сначала введите мастер-пароль", show_alert=True)
        return

    # Получаем пользователя из БД (нужен user.id для запросов)
    user = await rq.set_user(tg_id)
    passwords = await rq.get_all_passwords(user.id)

    if not passwords:
        await callback.answer("📭 У вас нет сохранённых паролей для экспорта", show_alert=True)
        return

    # get_all_passwords возвращает уже расшифрованные объекты
    # (как в view_passwords.py — там выводится password_obj.login/password напрямую)
    entries = [
        {
            "id": row.id,
            "site": row.site,
            "login": row.login,
            "password": row.password,
        }
        for row in passwords
    ]

    try:
        xml_bytes = export_passwords_to_xml(entries)
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при создании XML: {e}",
            reply_markup=kb.main_inline
        )
        return

    filename = f"passwords_{tg_id}.xml"
    file = BufferedInputFile(xml_bytes, filename=filename)

    await callback.message.delete()
    await callback.message.answer_document(
        document=file,
        caption=(
            "✅ <b>Экспорт выполнен успешно!</b>\n\n"
            f"📦 Записей: <b>{len(entries)}</b>\n\n"
            "⚠️ <b>Внимание:</b> файл содержит ваши пароли в открытом виде.\n"
            "Храните его в безопасном месте и не передавайте третьим лицам."
        ),
        parse_mode="HTML",
    )
    await callback.message.answer("Выберите действие:", reply_markup=kb.main_inline)
    await callback.answer()


# ─── ИМПОРТ: шаг 1 — запрос файла ───────────────────────────────────────────

@router.callback_query(F.data == "import_xml")
async def cmd_import_xml_start(callback, state: FSMContext):
    tg_id = callback.from_user.id

    if not auth_manager.is_authenticated(tg_id):
        await callback.answer("🔒 Сначала введите мастер-пароль", show_alert=True)
        return

    await state.set_state(XMLStates.waiting_for_xml_file)
    await callback.message.edit_text(
        "📎 <b>Импорт паролей из XML</b>\n\n"
        "Отправьте XML-файл, экспортированный ранее из этого бота.\n\n"
        "• Дубликаты (по названию сайта) будут пропущены\n"
        "• Существующие пароли не изменятся\n\n"
        "Для отмены нажмите кнопку ниже.",
        parse_mode="HTML",
        reply_markup=kb.cancel_kb
    )
    await callback.answer()


# ─── ИМПОРТ: шаг 2 — обработка файла ────────────────────────────────────────

@router.message(XMLStates.waiting_for_xml_file, F.document)
async def cmd_import_xml_process(message: Message, state: FSMContext):
    await state.clear()
    tg_id = message.from_user.id
    doc = message.document

    # Проверяем расширение
    if not doc.file_name.lower().endswith(".xml"):
        await message.answer(
            "❌ Файл должен иметь расширение <b>.xml</b>\n"
            "Попробуйте ещё раз или вернитесь в меню.",
            parse_mode="HTML",
            reply_markup=kb.main_inline
        )
        return

    # Скачиваем содержимое
    file = await message.bot.get_file(doc.file_id)
    buf = io.BytesIO()
    await message.bot.download_file(file.file_path, destination=buf)
    xml_bytes = buf.getvalue()

    # Разбираем XML
    try:
        entries = import_passwords_from_xml(xml_bytes)
    except XMLImportError as e:
        await message.answer(
            f"❌ <b>Ошибка формата файла:</b>\n<code>{e}</code>",
            parse_mode="HTML",
            reply_markup=kb.main_inline
        )
        return

    if not entries:
        await message.answer(
            "📭 В файле не найдено ни одной записи.",
            reply_markup=kb.main_inline
        )
        return

    # Получаем пользователя (нужен user.id для rq.add_password)
    user = await rq.set_user(tg_id)
    existing = await rq.get_all_passwords(user.id)
    existing_sites = {row.site.lower() for row in existing}

    imported = 0
    skipped = 0

    for entry in entries:
        if entry["site"].lower() in existing_sites:
            skipped += 1
            continue

        # add_password принимает (user.id, site, login, password) как строки —
        # шифрование происходит внутри rq.add_password, как при обычном добавлении
        await rq.add_password(user.id, entry["site"], entry["login"], entry["password"])
        existing_sites.add(entry["site"].lower())
        imported += 1

    await message.answer(
        f"✅ <b>Импорт завершён!</b>\n\n"
        f"➕ Добавлено: <b>{imported}</b>\n"
        f"⏭ Пропущено (уже есть): <b>{skipped}</b>",
        parse_mode="HTML",
        reply_markup=kb.main_inline
    )


# ─── Получен не-документ в режиме ожидания файла ────────────────────────────

@router.message(XMLStates.waiting_for_xml_file)
async def cmd_import_xml_wrong_input(message: Message):
    await message.answer(
        "📎 Пожалуйста, отправьте XML-файл как <b>документ</b> (не как фото или текст).",
        parse_mode="HTML"
    )
