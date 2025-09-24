import asyncio
from app.database.models import async_session, User, Password
from app.crypto import cipher
from app.auth_manager import auth_manager
from sqlalchemy import select


async def migrate_user_passwords_to_master_password(user_id: int, tg_id: int, master_password: str):
    """
    Мигрирует существующие пароли пользователя для работы с мастер-паролем.
    Расшифровывает данные старым ключом (только tg_id) и зашифровывает новым ключом (tg_id + master_password)
    """
    async with async_session() as session:
        # Получаем все пароли пользователя
        result = await session.execute(select(Password).where(Password.link == user_id))
        passwords = result.scalars().all()

        migrated_count = 0

        for password_entry in passwords:
            try:
                # Расшифровываем старым способом (без мастер-пароля)
                old_site = cipher.decrypt(password_entry.site, tg_id, None)
                old_login = cipher.decrypt(password_entry.login, tg_id, None)
                old_password = cipher.decrypt(
                    password_entry.password, tg_id, None)

                # Зашифровываем новым способом (с мастер-паролем)
                new_site = cipher.encrypt(old_site, tg_id, master_password)
                new_login = cipher.encrypt(old_login, tg_id, master_password)
                new_password = cipher.encrypt(
                    old_password, tg_id, master_password)

                # Обновляем в базе данных
                password_entry.site = new_site
                password_entry.login = new_login
                password_entry.password = new_password

                migrated_count += 1

            except Exception as e:
                print(f"Ошибка миграции пароля ID {password_entry.id}: {e}")
                continue

        # Сохраняем изменения
        await session.commit()

        return migrated_count


async def check_needs_migration(tg_id: int) -> bool:
    """
    Проверяет, нужна ли миграция для пользователя:
    - Есть ли у него сохраненные пароли
    - Не установлен ли мастер-пароль
    """
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            return False

        # Если мастер-пароль уже установлен, миграция не нужна
        if user.master_password_hash:
            return False

        # Проверяем, есть ли сохраненные пароли
        result = await session.execute(select(Password).where(Password.link == user.id))
        passwords = result.scalars().all()

        return len(passwords) > 0


async def get_migration_info(tg_id: int) -> dict:
    """
    Возвращает информацию о необходимости миграции
    """
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            return {
                'needs_migration': False,
                'has_passwords': False,
                'has_master_password': False,
                'password_count': 0
            }

        # Подсчитываем количество паролей
        result = await session.execute(select(Password).where(Password.link == user.id))
        passwords = result.scalars().all()
        password_count = len(passwords)

        return {
            'needs_migration': password_count > 0 and not user.master_password_hash,
            'has_passwords': password_count > 0,
            'has_master_password': user.master_password_hash is not None,
            'password_count': password_count
        }
