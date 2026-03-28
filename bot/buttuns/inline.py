from aiogram.types import InlineKeyboardButton, KeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from models import Shop


def language_inl():
    ikb = InlineKeyboardBuilder()
    ikb.add(*[InlineKeyboardButton(text='🇺🇿Uz', callback_data='lang_uz'),
              InlineKeyboardButton(text='🇷🇺Ru', callback_data='lang_rus')])
    ikb.adjust(2)
    return ikb.as_markup()


def shop_setting_menu():
    ikb = InlineKeyboardBuilder()
    ikb.add(*[InlineKeyboardButton(text="Gurux o'zgartirish", callback_data=f'group_setting'),
              InlineKeyboardButton(text='Ortga', callback_data=f'group_back')])
    ikb.adjust(2, repeat=True)
    return ikb.as_markup()


async def shops_button():
    ikb = InlineKeyboardBuilder()
    shops: list[Shop] = await Shop.all()
    ikb.add(*[InlineKeyboardButton(text=i.name_uz, callback_data=f'shop_{i.id}_{i.order_group_id}') for i in
              shops])
    ikb.adjust(1, repeat=True)
    return ikb.as_markup()


async def my_restorator(address, user_id):
    ikb = InlineKeyboardBuilder()
    ikb.add(*[InlineKeyboardButton(text=i.address, callback_data=f'address_{user_id}_{i.lat}_{i.long}_{i.id}') for i in
              address])
    ikb.adjust(1, repeat=True)
    return ikb.as_markup()


def main_menu():
    ikb = InlineKeyboardBuilder()
    ikb.add(*[InlineKeyboardButton(text="🍽Menu🍽", callback_data="menu"),
              InlineKeyboardButton(text="Admin Panel", callback_data="admin")])
    return ikb.as_markup()


def menu(user_id, admin=False):
    ikb = InlineKeyboardBuilder()
    ikb.add(*[InlineKeyboardButton(text="🛒QAZI BOT🛒",
                                   web_app=WebAppInfo(
                                       url=f'https://oka-uz.uz/#/{user_id}'))])
    if admin:
        ikb.add(*[InlineKeyboardButton(text="⚙️Settings⚙️", callback_data='settings')])
    ikb.adjust(1, 2)
    return ikb.as_markup()


def contact():
    ikb = ReplyKeyboardBuilder()
    ikb.row(KeyboardButton(text='📞 Contact 📞', request_contact=True))
    return ikb.as_markup(resize_keyboard=True)


def confirm_inl():
    ikb = InlineKeyboardBuilder()
    ikb.add(*[InlineKeyboardButton(text='✅Tasdiqlash✅', callback_data=f'confirm_network'),
              InlineKeyboardButton(text="❌Toxtatish❌", callback_data=f'cancel_network')])
    ikb.adjust(2, repeat=True)
    return ikb.as_markup()


def get_location():
    kb = ReplyKeyboardBuilder()
    kb.add(*[KeyboardButton(text='📍Locatsiya jonatish📍', request_location=True)])
    return kb.as_markup(resize_keyboard=True)


NEW = "yangi"
IS_PROCESS = "jarayonda"
READY = "tayyor"
IN_PROGRESS = "yetkazilmoqda"
DELIVERED = "yetkazildi"
CANCELLED = "bekor qilindi"


def group_order_btn(order):
    ikb = InlineKeyboardBuilder()
    if order.status == 'NEW':
        ikb.row(InlineKeyboardButton(text='Qabul qilish', callback_data=f'group_add_{order.id}'))
        ikb.row(InlineKeyboardButton(text='Bekor qilish', callback_data=f'group_canceled_{order.id}'))
    elif order.status == "IS_PROCESS":
        ikb.row(InlineKeyboardButton(text='Tayyor', callback_data=f'group_add_{order.id}'))
        ikb.row(InlineKeyboardButton(text='Bekor qilish', callback_data=f'group_canceled_{order.id}'))
    elif order.status == "READY":
        ikb.row(InlineKeyboardButton(text="Yo'lda", callback_data=f'group_add_{order.id}'))
    elif order.status == "IN_PROGRESS":
        ikb.row(InlineKeyboardButton(text="Yetkazildi", callback_data=f'group_add_{order.id}'))
    elif order.status == 'DELIVERED':
        return
    ikb.adjust(2, repeat=True)
    return ikb.as_markup()


