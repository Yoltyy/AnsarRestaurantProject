from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_table_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text='На улице')
    builder.button(text='В зале')
    builder.button(text='У окна')
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_time_kb():
    builder = ReplyKeyboardBuilder()

    hours = [f"{i:02d}:00" for i in range(24)]

    for h in hours:
        builder.button(text=h)

    builder.adjust(4)

    return builder.as_markup(resize_keyboard=True)


def get_guests_kb():
    builder = ReplyKeyboardBuilder()

    for i in range(1, 11):
        builder.button(text=str(i))

    builder.adjust(5)
    return builder.as_markup(resize_keyboard=True)