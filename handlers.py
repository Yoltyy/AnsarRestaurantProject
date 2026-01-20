import os
import hashlib
from aiogram import F
from datetime import datetime, time
from aiogram.types import (Message, ReplyKeyboardRemove, CallbackQuery,
                           InlineKeyboardButton, InlineQuery, LabeledPrice,
                           InlineQueryResultArticle, InputTextMessageContent, PreCheckoutQuery,)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot import router, rest_fsm
from dotenv import load_dotenv
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, CommandStart

from database import save_to_db, get_reservations, del_from_db, check_availability, is_time_available, check_table_availability
from utils.keyboards import get_table_kb, get_time_kb, get_guests_kb
from utils.fsm import ReservState


load_dotenv()
PAYMENT_TOKEN = os.getenv('PAYMENT_API')
RESERVATION_PRICE = 50000


@router.message(CommandStart())
async def start(message: Message):
    await message.answer('Здраствуйте! Это официальный бот для бронирования столиков в ресторане Ansar!')
    await message.answer('Чтобы забронировать столик введите команду "/book"')


@router.message(Command('book'))
async def book(message: Message, state: FSMContext):
    await state.set_state(ReservState.waiting_for_date)
    await message.answer('На какой день вы хотите забронировать столик? Введите дату (ДД.ММ.ГГГГ)')

@rest_fsm.message(ReservState.waiting_for_date)
async def process_date(message: Message, state: FSMContext):
    text = message.text

    try:
        user_date = datetime.strptime(text, "%d.%m.%Y")
        if user_date.date() < datetime.now().date():
            return await message.answer('Эта дата уже прошла!')

        await state.update_data(date=text)
        await state.set_state(ReservState.waiting_for_time)
        await message.answer('Выберите время или введите самостоятельно:', reply_markup=get_time_kb())
    except ValueError:
        await message.answer('Формат: ДД.ММ.ГГГГ')


@rest_fsm.callback_query(ReservState.waiting_for_time, F.data.startswith('time_'))
async def process_time_callback(callback: CallbackQuery, state: FSMContext):
    time_str = callback.data.replace('time_', '')
    data = await state.get_data()

    if not is_time_available(data['date'], time_str):
        await callback.answer(f"❌ Время {time_str} занято!", show_alert=True)
        return

    try:
        full_datetime = datetime.strptime(f"{data['date']} {time_str}", '%d.%m.%Y %H:%M')
        if full_datetime < datetime.now():
            await callback.answer("❌ Это время уже в прошлом!", show_alert=True)
            return
    except:
        pass

    await callback.message.answer(f"✅ Выбрано время: {time_str}")
    await state.update_data(time=time_str)
    await state.set_state(ReservState.waiting_for_guests)
    await callback.message.answer('Сколько гостей?', reply_markup=get_guests_kb())
    await callback.answer()


@rest_fsm.callback_query(ReservState.waiting_for_guests, F.data.startswith('guests_'))
async def process_guests_callback(callback: CallbackQuery, state: FSMContext):
    guests = callback.data.replace('guests_', '')
    await callback.message.answer(f"✅ Гостей: {guests}")
    await state.update_data(guests=guests)
    await state.set_state(ReservState.waiting_for_preference)
    await callback.message.answer('Выберите место:', reply_markup=get_table_kb())
    await callback.answer()


@rest_fsm.callback_query(ReservState.waiting_for_preference, F.data.startswith('table_'))
async def process_table_callback(callback: CallbackQuery, state: FSMContext):
    table_map = {
        'table_outside': 'На улице',
        'table_inside': 'В зале',
        'table_window': 'У окна'
    }
    table_text = table_map.get(callback.data, callback.data)

    data = await state.get_data()

    if not check_table_availability(data['date'], data['time'], table_text):
        await callback.answer(f"❌ Место '{table_text}' занято!", show_alert=True)
        return

    await state.update_data(preference=table_text)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💳 Оплатить бронь 500 руб.", callback_data="pay_now"))
    builder.row(InlineKeyboardButton(text="❌ Заполнить заново", callback_data="confirm_no"))

    confirm_msg = (
        f"📋 **Проверьте вашу бронь:**\n\n"
        f"📅 **Дата:** {data['date']}\n"
        f"⏰ **Время:** {data['time']}\n"
        f"👥 **Гостей:** {data['guests']}\n"
        f"✨ **Место:** {table_text}\n\n"
        f"💵 **Стоимость:** 500 руб.\n"
        f"Бронь подтверждается только после оплаты."
    )

    await state.set_state(ReservState.confirm_reservation)
    await callback.message.answer(confirm_msg, reply_markup=builder.as_markup(), parse_mode='Markdown')
    await callback.answer()


@rest_fsm.callback_query(ReservState.confirm_reservation, F.data == 'pay_now')
async def process_payment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await callback.message.answer_invoice(
        title="Оплата бронирования столика",
        description=f"Столик на {data.get('guests')} гостей на {data.get('date')} в {data.get('time')}",
        provider_token=PAYMENT_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label="Бронирование столика", amount=RESERVATION_PRICE)],
        payload=f"reservation_{callback.from_user.id}_{datetime.now().timestamp()}",
        start_parameter="create_invoice_reservation",
        need_name=True,
        need_phone_number=True
    )
    await callback.answer()


@router.callback_query(ReservState.confirm_reservation, F.data == "confirm_no")
async def finish_retry(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Начнем заново.")
    await book(callback.message, state)
    await callback.answer()


@router.message(Command('mybookings'))
async def mybookings(message: Message):
    user_id = message.from_user.id
    res = get_reservations(user_id)

    if not res:
        return await message.answer("У вас нет активных бронирований.")

    msg = "<b>🗂 ВАШИ БРОНИРОВАНИЯ</b>\n"
    msg += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"

    for i, r in enumerate(res, 1):
        msg += (
            f"<b>Бронь №{i}</b>\n"
            f"📅 <b>Дата:</b> <code>{r[0]}</code>\n"
            f"⏰ <b>Время:</b> <code>{r[1]}</code>\n"
            f"👥 <b>Гостей:</b> <code>{r[2]} чел.</code>\n"
            f"✨ <b>Пожелания:</b> <i>{r[3]}</i>\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        )

    await message.answer(msg, parse_mode='HTML')



@router.message(Command('cancel'))
async def cancel(message: Message):
    user_id = message.from_user.id

    delete = del_from_db(user_id)

    if delete > 0:
        await message.answer('Ваша бронь успешно отменена.')
    else:
        await message.answer('У вас нет активных бронирований.')

@router.inline_query()
async def inline_booking_handler(inline_query: InlineQuery):
    user_id = inline_query.from_user.id
    res = get_reservations(user_id)

    if not res:
        return await inline_query.answer([], is_personal=True, cache_time=5)

    results = []
    for i, r in enumerate(res):
        booking_text = (
            f"📍 **Я иду в ресторан Ansar!**\n"
            f"📅 Дата: `{r[0]}`\n"
            f"⏰ Время: `{r[1]}`\n"
            f"👥 Гостей: `{r[2]}`\n"
            f"✨ Место: {r[3]}"
        )

        results_id = hashlib.md5(f'{user_id}_{r[0]}_{r[1]}'.encode()).hexdigest()

        results.append(InlineQueryResultArticle(
            id=results_id,
            title=f'Бронь на {r[0]} в {r[1]}',
            description=f"Гостей: {r[2]} | Место: {r[3]}",
            input_message_content=InputTextMessageContent(
                message_text=booking_text,
                parse_mode='Markdown'

            )
        )
    )

    await inline_query.answer(results, is_personal=True, cache_time=10)