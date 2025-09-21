from app.database.models import async_session
from app.database.models import User, Password
from sqlalchemy import select, delete


async def set_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            user = User(tg_id=tg_id)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def get_passwords(user_id):
    async with async_session() as session:
        result = await session.execute(select(Password).where(Password.link == user_id))
        return result.scalars().all()


async def get_password_by_id(password_id):
    async with async_session() as session:
        return await session.scalar(select(Password).where(Password.id == password_id))


async def add_password(user_id, site, login, password):
    async with async_session() as session:
        new_password = Password(
            site=site,
            login=login,
            password=password,
            link=user_id
        )
        session.add(new_password)
        await session.commit()
        return new_password


async def delete_password(password_id):
    async with async_session() as session:
        password = await session.scalar(select(Password).where(Password.id == password_id))
        if password:
            await session.delete(password)
            await session.commit()
            return True
        return False
