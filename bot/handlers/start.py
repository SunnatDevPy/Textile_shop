from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.buttuns.inline import menu
from models import BotUser

start_router = Router()


@start_router.message(CommandStart())
async def command_start(message: Message):
    user = await BotUser.get(message.from_user.id)
    if user:
        if message.from_user.id in [5649321700, ]:
            await message.answer("Assalomu aleykum hush kelibsiz",
                                 reply_markup=menu(user.id, admin=True))
        else:
            await message.answer("Assalom aleykum hush kelibsiz",
                                 reply_markup=menu(user.id))
    else:
        from_user = message.from_user
        user = await BotUser.create(id=from_user.id, first_name=from_user.first_name, last_name=from_user.last_name,
                                    username=from_user.username)

        await message.answer("Assalom aleykum hush kelibsiz",
                             reply_markup=menu(user.id))

#
# @start_router.message(Contact.phone)
# async def register_full_name(msg: Message, state: FSMContext):
#     await state.set_state(Contact.location)
#     if msg.contact:
#         await state.update_data(contact=msg.contact.phone_number)
#         await msg.answer(html.bold("📍Locatsiya yuboring📍"), reply_markup=get_location(), parse_mode="HTML")
#     else:
#         await state.update_data(contact=msg.text)
#         await msg.answer(html.bold("📍Locatsiya yuboring📍"), reply_markup=get_location(), parse_mode="HTML")
#
#
# @start_router.message(Contact.location)
# async def register_full_name(msg: Message, state: FSMContext):
#     if msg.location:
#         await state.update_data(long=msg.location.longitude, lat=msg.location.latitude)
#         await state.set_state(Contact.confirm)
#         data = await state.get_data()
#         await msg.answer(html.bold("Ma'lumotingiz to'g'rimi?"), reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
#         await msg.answer(register_detail(msg, data), parse_mode='HTML',
#                          reply_markup=confirm_register_inl())
#     else:
#         await msg.answer(html.bold("Iltimos locatsiya jo'nating"), parse_mode="HTML")
#
#
# @start_router.callback_query(Contact.confirm, F.data.endswith('_register'))
# async def register_full_name(call: CallbackQuery, state: FSMContext):
#     confirm = call.data.split('_')
#     data = await state.get_data()
#     from_user = call.from_user
#     await call.message.delete()
#     lat = data.get('lat')
#     long = data.get('long')
#     if confirm[0] == 'confirm':
#         user_data = {'id': from_user.id, 'tg_username': from_user.username,
#                      'first_name': from_user.first_name, "last_name": from_user.last_name, "long": long,
#                      "lat": lat, "contact": str(data.get('contact')), "type": "ONE"}
#         location = geolocator.reverse(f"{lat}, {long}")
#         address = location.raw['address']
#         await BotUser.create(**user_data)
#         await MyAddress.create(user_id=from_user.id, lat=data.get('lat'), long=data.get('long'),
#                                name=f"{address['county']}, {address['neighbourhood']}, {address['road']}")
#         if call.from_user.id in [5649321700, ]:
#             messages: Message = await call.message.answer(f'Xush kelibsiz Admin {call.from_user.first_name}',
#                                                           reply_markup=menu(call.from_user.id))
#         else:
#             messages: Message = await call.message.answer(f'Xush kelibsiz {call.from_user.first_name}',
#                                                           reply_markup=menu(call.from_user.id))
#         await asyncio.sleep(60)
#         await messages.delete()
#         await call.message.answer("Bosh sahifa", reply_markup=main_menu())
#
#         await state.clear()
#     else:
#         await state.set_state(Contact.phone)
#         await call.message.answer("Qayta ro'yxatdan o'ting")
#
#
# @start_router.callback_query(F.data == 'menu')
# async def register_full_name(call: CallbackQuery, state: FSMContext):
#     await call.message.delete()
#     user = await BotUser.get(call.from_user.id)
#     address = await MyAddress.get_cart_from_user(call.from_user.id)
#     await call.message.answer("Mahsulotni qayerga jo'natish uchun locatsiya kiriting!", reply_markup=get_location())
#     if address:
#         await call.message.answer("Manzillaringizni tanlang",
#                                   reply_markup=await my_address(address, call.from_user.id))
#     print(call.from_user.id, user)
#     if user.type.value != "one":
#         address = await MyAddress.from_user(user.id)
#         await call.message.answer("Idorangizni tanlang",
#                                   reply_markup=await my_restorator(address, call.from_user.id))
#
#
# @start_router.message(F.location)
# async def register_full_name(message: Message, state: FSMContext):
#     if message.location:
#         data = await state.get_data()
#         location = geolocator.reverse(f"{message.location.latitude}, {message.location.longitude}")
#         address = location.raw['address']
#         name = f"{address['county']}, {address['neighbourhood']}, {address['road']}"
#         check_address = await MyAddress.get_from_name(name)
#         if check_address == None:
#             await MyAddress.create(bot_user_id=message.from_user.id, lat=data.get('lat'), long=data.get('long'),
#                                    address=name)
#         await BotUser.update(message.from_user.id, lat=message.location.latitude, long=message.location.longitude)
#         await message.answer("Xush kelibsiz", reply_markup=ReplyKeyboardRemove())
#         messages: Message = await message.answer("Menu",
#                                                  reply_markup=menu(message.from_user.id, language=data.get('locale')))
#         await asyncio.sleep(60)
#         await messages.delete()
#         await message.answer("Bosh Menu", reply_markup=main_menu())
#         await state.clear()
#     else:
#         await message.answer("Locatsiya kiriting", reply_markup=get_location())
#
#
# @start_router.callback_query(F.data.startswith("address"))
# async def register_full_name(call: CallbackQuery, state: FSMContext):
#     await call.answer()
#     await state.clear()
#     data = call.data.split('_')
#     await BotUser.update(call.from_user.id, long=float(data[3]), lat=float(data[2]))
#     if call.from_user.id in [5649321700, ]:
#         messages: Message = await call.message.answer(f'Xush kelibsiz Admin {call.from_user.first_name}',
#                                                       reply_markup=menu(call.from_user.id))
#     else:
#         messages: Message = await call.message.answer(f'Xush kelibsiz {call.from_user.first_name}',
#                                                       reply_markup=menu(call.from_user.id))
#     await asyncio.sleep(60)
#     await messages.delete()
#     await call.message.answer("Bosh Menu", reply_markup=main_menu())
