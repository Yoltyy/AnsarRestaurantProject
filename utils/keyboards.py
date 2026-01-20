from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_table_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text='На улице', callback_data='table_outside')
    builder.button(text='В зале', callback_data='table_inside')
    builder.button(text='У окна', callback_data='table_window')
    builder.adjust(2)
    return builder.as_markup()


def get_time_kb():
    builder = InlineKeyboardBuilder()
    hours = [f"{i:02d}:00" for i in range(8, 23)]

    for h in hours:
        builder.button(text=h, callback_data=f'time_{h}')

    builder.adjust(3)
    return builder.as_markup()


def get_guests_kb():
    builder = InlineKeyboardBuilder()

    for i in range(1, 11):
        builder.button(text=str(i), callback_data=f'guests_{i}')

    builder.adjust(5)
    return builder.as_markup()