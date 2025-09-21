from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

# создание бд
engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):  # основной класс
    pass


class User(Base):  # таблица юзеров
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)


class Password(Base):  # таблица паролей юзеров
    __tablename__ = 'passwords'

    id: Mapped[int] = mapped_column(primary_key=True)
    site: Mapped[str] = mapped_column()
    password: Mapped[str] = mapped_column()
    login: Mapped[str] = mapped_column()
    link: Mapped[int] = mapped_column(ForeignKey('users.id'))


async def async_main():  # создает таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
