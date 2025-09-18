from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import app.keyboard as kb

router = Router()


@router.message(CommandStart())  # обработчик сообщений
async def cmd_start(message: Message):
    # answer - сообщение, reply_markup - открыть клавиатуру
    await message.answer('Привет', reply_markup=kb.main)
    await message.reply('Kak Dela')  # reply - ответ на сообщение


@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('Help')


@router.message(F.text == 'Пароли')
async def password(message: Message):
    await message.answer('Выберите', reply_markup=kb.password)


@router.callback_query(F.data == '1')  # обработчик колбека
async def one(callback: CallbackQuery):
    # уведомление, кнопка не подсвечивается после, show_alert - всплывыющее окно
    await callback.answer('OnEOnE', show_alert=True)
    await callback.message.answer('oneoneoneone')


# авторизация


class Register(StatesGroup):
    name = State()
    age = State()
    number = State()


@router.message(Command('register'))
async def register(message: Message, state: FSMContext):
    await state.set_state(Register.name)
    await message.answer('Введите ваше имя')


@router.message(Register.name)
async def register_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Register.age)
    await message.answer('Введите ваш возраст')


@router.message(Register.age)
async def register_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(Register.number)
    await message.answer('Отправьте номер телефона', reply_markup=kb.get_number)


@router.message(Register.number, F.contact)
async def register_number(message: Message, state: FSMContext):
    await state.update_data(number=message.contact.phone_number)
    data = await state.get_data()
    await message.answer(f'Ваше имя: {data["name"]}\nВаш возраст: {data["age"]}\nНомер: {data["number"]}')
    await state.clear()
