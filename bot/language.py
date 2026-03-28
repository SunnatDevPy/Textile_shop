from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ReplyKeyboardRemove

from bot.buttuns.inline import main_menu, contact
from bot.state.states import Contact
from models import BotUser

language_router = Router()


@language_router.callback_query(F.data.startswith('lang_'))
async def language_handler(call: CallbackQuery, state: FSMContext):
    lang_code = call.data.split('lang_')[-1]
    if lang_code == 'rus':
        salom = "Здравствуйте"
        bosh = 'Главное меню'
        davom = "отправьте контакт, чтобы продолжить"
        til = "Язык выбран"

    else:
        til = "Til tanlandi"
        salom = "Assalomu aleykum"
        bosh = 'Bosh menu'
        davom = "davom etish uchun contact yuboring"
    await call.message.delete()
    await state.update_data(locale=lang_code)
    await call.answer(til, show_alert=True)
    user = await BotUser.get(call.from_user.id)
    if not user:
        await state.set_state(Contact.phone)
        await call.message.answer(
            f'{salom} {call.from_user.first_name}, {davom}',
            reply_markup=contact())
    else:
        if call.from_user.id in [5649321700, ]:
            await call.message.answer(f'{salom} Admin {call.from_user.first_name}',
                                      reply_markup=ReplyKeyboardRemove())
            await call.message.answer(bosh,
                                      reply_markup=main_menu())
        else:
            await call.message.answer(f"{salom} {call.from_user.first_name}", reply_markup=ReplyKeyboardRemove())
            await call.message.answer(bosh,
                                      reply_markup=main_menu())
