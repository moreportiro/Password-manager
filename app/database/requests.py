from app.database.models import async_session
from app.database.models import User, Password
from sqlalchemy import select, delete
from app.crypto import cipher
from app.auth_manager import auth_manager


async def set_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            user = User(tg_id=tg_id, master_password_hash=None)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def set_master_password(tg_id: int, master_password_hash: str):
    """Устанавливает мастер-пароль для пользователя"""
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            user.master_password_hash = master_password_hash
            await session.commit()
            return True
        return False


async def get_user_by_tg_id(tg_id: int):
    """Получает пользователя по Telegram ID"""
    async with async_session() as session:
        return await session.scalar(select(User).where(User.tg_id == tg_id))


async def has_master_password(tg_id: int) -> bool:
    """Проверяет, установлен ли мастер-пароль у пользователя"""
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return user and user.master_password_hash is not None


async def reset_user_data(tg_id: int):
    """Полностью сбрасывает данные пользователя (пароли и мастер-пароль)"""
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            # Удаляем все пароли пользователя
            await session.execute(delete(Password).where(Password.link == user.id))
            # Сбрасываем мастер-пароль
            user.master_password_hash = None
            await session.commit()
            # Очищаем сессию аутентификации
            auth_manager.logout_user(tg_id)
            return True
        return False


async def get_passwords(user_id):
    async with async_session() as session:
        # Получаем пользователя для получения tg_id
        user = await session.scalar(select(User).where(User.id == user_id))
        if not user:
            return []

        result = await session.execute(select(Password).where(Password.link == user_id))
        passwords = result.scalars().all()
        # Получаем мастер-пароль из сессии
        master_password = auth_manager.get_master_password(user.tg_id)

        # Расшифровываем данные для каждого пароля
        for pwd in passwords:
            pwd.site = cipher.decrypt(pwd.site, user.tg_id, master_password)
            pwd.login = cipher.decrypt(pwd.login, user.tg_id, master_password)
            pwd.password = cipher.decrypt(
                pwd.password, user.tg_id, master_password)

        return passwords


async def get_password_by_id(password_id):
    async with async_session() as session:
        password = await session.scalar(select(Password).where(Password.id == password_id))
        if password:
            # Получаем пользователя для получения tg_id
            user = await session.scalar(select(User).where(User.id == password.link))
            if user:
                # Получаем мастер-пароль из сессии
                master_password = auth_manager.get_master_password(user.tg_id)
                # Расшифровываем данные
                password.site = cipher.decrypt(
                    password.site, user.tg_id, master_password)
                password.login = cipher.decrypt(
                    password.login, user.tg_id, master_password)
                password.password = cipher.decrypt(
                    password.password, user.tg_id, master_password)
        return password


async def get_password_by_site(user_id, site):
    async with async_session() as session:
        # Получаем пользователя для получения tg_id
        user = await session.scalar(select(User).where(User.id == user_id))
        if not user:
            return None
        # Получаем мастер-пароль из сессии
        master_password = auth_manager.get_master_password(user.tg_id)
        # Шифруем site для поиска в БД
        encrypted_site = cipher.encrypt(site, user.tg_id, master_password)

        return await session.scalar(
            select(Password).where(
                Password.link == user_id,
                Password.site == encrypted_site
            )
        )


async def add_password(user_id, site, login, password):
    async with async_session() as session:
        # Получаем пользователя для получения tg_id
        user = await session.scalar(select(User).where(User.id == user_id))
        if not user:
            return None
        # Получаем мастер-пароль из сессии
        master_password = auth_manager.get_master_password(user.tg_id)
        # Шифруем данные перед сохранением
        encrypted_site = cipher.encrypt(site, user.tg_id, master_password)
        encrypted_login = cipher.encrypt(login, user.tg_id, master_password)
        encrypted_password = cipher.encrypt(
            password, user.tg_id, master_password)

        new_password = Password(
            site=encrypted_site,
            login=encrypted_login,
            password=encrypted_password,
            link=user_id
        )
        session.add(new_password)
        await session.commit()

        # Расшифровываем для возврата
        new_password.site = site
        new_password.login = login
        new_password.password = password

        return new_password


async def update_password(password_id, site, login, password):
    async with async_session() as session:
        # Находим существующий пароль
        existing_password = await session.scalar(
            select(Password).where(Password.id == password_id)
        )

        if existing_password:
            # Получаем пользователя для получения tg_id
            user = await session.scalar(select(User).where(User.id == existing_password.link))
            if not user:
                return False
            # Получаем мастер-пароль из сессии
            master_password = auth_manager.get_master_password(user.tg_id)
            # Шифруем новые данные
            encrypted_site = cipher.encrypt(site, user.tg_id, master_password)
            encrypted_login = cipher.encrypt(
                login, user.tg_id, master_password)
            encrypted_password = cipher.encrypt(
                password, user.tg_id, master_password)

            # Обновляем данные
            existing_password.site = encrypted_site
            existing_password.login = encrypted_login
            existing_password.password = encrypted_password
            await session.commit()
            return True
        return False


async def delete_password(password_id):
    async with async_session() as session:
        password = await session.scalar(select(Password).where(Password.id == password_id))
        if password:
            await session.delete(password)
            await session.commit()
            return True
        return False


async def check_password_exists(user_id, site):
    async with async_session() as session:
        # Получаем пользователя для получения tg_id
        user = await session.scalar(select(User).where(User.id == user_id))
        if not user:
            return False
        # Получаем мастер-пароль из сессии
        master_password = auth_manager.get_master_password(user.tg_id)
        # Шифруем site для поиска в БД
        encrypted_site = cipher.encrypt(site, user.tg_id, master_password)

        existing = await session.scalar(
            select(Password).where(
                Password.link == user_id,
                Password.site == encrypted_site
            )
        )
        return existing is not None
