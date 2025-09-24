from aiogram.fsm.state import State, StatesGroup


class AddPassword(StatesGroup):
    site = State()
    login = State()
    password = State()


class ReplacePassword(StatesGroup):
    site = State()
    login = State()
    password = State()
    target_password_id = State()
    confirmation = State()


class MasterPassword(StatesGroup):
    setup_new = State()
    setup_confirm = State()
    enter_existing = State()
    reset_confirm = State()
