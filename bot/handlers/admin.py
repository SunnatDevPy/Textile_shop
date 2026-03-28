from aiogram import Bot, F, Router, html
from aiogram.enums import ChatMemberStatus
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.buttuns.inline import shops_button, shop_setting_menu
from bot.state.states import SendTextState
from models import AdminPanelUser, Shop

admin_router = Router()


@admin_router.callback_query(F.data == 'settings')
async def settings_handler(call: CallbackQuery):
    await call.message.answer("Filialdan birini tanlang", reply_markup=await shops_button())


@admin_router.callback_query(F.data.startswith('shop'))
async def shop_handler(call: CallbackQuery):
    data = call.data.split('_')
    await call.message.edit_text(f"Xozirgi gurux id {data[-1]}", reply_markup=shop_setting_menu())


@admin_router.callback_query(F.data.startswith('shop'))
async def shop_settings(call: CallbackQuery):
    data = call.data.split('_')
    await call.message.edit_text(f"Xozirgi gurux id {data[-1]}", reply_markup=shop_setting_menu())
