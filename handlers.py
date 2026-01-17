import hashlib
from aiogram import F
from aiogram.types import (Message, ReplyKeyboardRemove, CallbackQuery,
                           InlineKeyboardButton, InlineQuery,
                           InlineQueryResultArticle, InputTextMessageContent)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, CommandStart
from datetime import datetime

from database import save_to_db, get_reservations, del_from_db
from utils.keyboards import get_table_kb, get_time_kb, get_guests_kb
from utils.fsm import ReservState
from bot import rest_fsm, router


@router.message(CommandStart)
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

@rest_fsm.message(ReservState.waiting_for_time)
async def process_time(message: Message, state: FSMContext):
    data = await state.get_data()
    date_str = data.get('date')

    try:
        full_datetime = datetime.strptime(f"{date_str} {message.text}", '%d.%m.%Y %H:%M')
        if full_datetime < datetime.now():
            return await message.answer('Это время уже в прошлом!')

        await state.update_data(time=message.text)
        await state.set_state(ReservState.waiting_for_guests)
        await message.answer('Сколько гостей?', reply_markup=get_guests_kb())
    except ValueError:
        await message.answer('Формат: ЧЧ:ММ (например, 19:00)')


@rest_fsm.message(ReservState.waiting_for_guests)
async def process_guests(message: Message, state: FSMContext):
    text = message.text

    if not text.isdigit():
        return await message.answer('Пожалуйста, введите количество гостей цифрами (от 1 до 10).')

    guests_count = int(text)

    if guests_count < 1 or guests_count > 10:
        return await message.answer('Количество гостей должно быть от 1 до 10.')

    await state.update_data(guests=guests_count)
    await state.set_state(ReservState.waiting_for_preference)
    await message.answer('Где желаете присесть?', reply_markup=get_table_kb())


@rest_fsm.message(ReservState.waiting_for_preference)
async def process_pref(message: Message, state: FSMContext):
    text = message.text

    await state.update_data(preference=text)

    data = await state.get_data()

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Да, подтверждаю", callback_data="confirm_yes"))
    builder.row(InlineKeyboardButton(text="❌ Нет, заполнить заново", callback_data="confirm_no"))

    confirm_msg = (
        f"📋 **Проверьте вашу бронь:**\n\n"
        f"📅 **Дата:** {data.get('date')}\n"
        f"⏰ **Время:** {data.get('time')}\n"
        f"👥 **Гостей:** {data.get('guests')}\n"
        f"✨ **Предпочтение:** {text}"
    )

    await state.set_state(ReservState.confirm_reservation)

    await message.answer("Проверьте данные:", reply_markup=ReplyKeyboardRemove())
    await message.answer(
        confirm_msg,
        reply_markup=builder.as_markup(),
        parse_mode='Markdown'
    )


@router.callback_query(ReservState.confirm_reservation, F.data == "confirm_yes")
async def finish_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    save_to_db(
        user_id=callback.from_user.id,
        date=data.get('date'),
        time=data.get('time'),
        guests=data.get('guests'),
        preference=data.get('preference')
    )
    await callback.message.edit_text("✅ Бронь зарегистрирована!")
    await state.clear()
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

        results = (InlineQueryResultArticle(
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