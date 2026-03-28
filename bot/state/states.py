from aiogram.fsm.state import StatesGroup, State


class SendTextState(StatesGroup):
    text = State()
    video = State()
    link = State()
    confirm = State()


class AddLink(StatesGroup):
    name = State()
    link = State()


class Contact(StatesGroup):
    phone = State()
    location = State()
    confirm = State()

class Location(StatesGroup):
    location = State()
