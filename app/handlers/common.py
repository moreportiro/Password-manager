from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from app.handlers.states import AddPassword, ReplacePassword
import app.keyboard as kb

router = Router()


@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Действие отменено.",
        reply_markup=kb.main_inline
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_action", AddPassword.site)
@router.callback_query(F.data == "cancel_action", AddPassword.login)
@router.callback_query(F.data == "cancel_action", AddPassword.password)
@router.callback_query(F.data == "cancel_action", ReplacePassword.login)
@router.callback_query(F.data == "cancel_action", ReplacePassword.password)
async def cancel_action_in_state(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Действие отменено.",
        reply_markup=kb.main_inline
    )
    await callback.answer()
