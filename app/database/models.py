from sqlalchemy import BigInteger, ForeignKey, Text
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
    # Увеличиваем размер для зашифрованных данных
    site: Mapped[str] = mapped_column(Text)
    # Увеличиваем размер для зашифрованных данных
    password: Mapped[str] = mapped_column(Text)
    # Увеличиваем размер для зашифрованных данных
    login: Mapped[str] = mapped_column(Text)
    link: Mapped[int] = mapped_column(ForeignKey('users.id'))


async def async_main():  # создает таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
