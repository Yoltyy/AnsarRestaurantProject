from aiogram import BaseMiddleware
from aiogram.types import Update, Message, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from database import save_to_db
from utils.fsm import ReservState


class PaymentCheckMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data):
        state = data.get('state')

        if isinstance(event, PreCheckoutQuery):
            await event.answer(ok=True)
            return

        if isinstance(event, Message) and event.successful_payment:
            if state:
                data = await state.get_data()
                save_to_db(
                    user_id=event.from_user.id,
                    date=data.get('date'),
                    time=data.get('time'),
                    guests=data.get('guests'),
                    preference=data.get('preference')
                )
                await event.answer("✅ Бронь оплачена!")
                await state.clear()
            return

        if state and await state.get_state() == ReservState.confirm_reservation:
            if event.callback_query and event.callback_query.data not in ['pay_now', 'confirm_no']:
                await event.callback_query.answer("Сначала завершите бронирование")
                return
            if isinstance(event, Message) and event.text:
                await event.answer("Используйте кнопки для оплаты или отмены")
                return

        return await handler(event, data)