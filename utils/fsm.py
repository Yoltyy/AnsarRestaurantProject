from aiogram.fsm.state import StatesGroup, State

class ReservState(StatesGroup):
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_guests = State()
    waiting_for_preference = State()
    confirm_reservation = State()