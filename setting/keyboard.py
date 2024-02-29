from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

start_keyboard = InlineKeyboardMarkup()
button_start_keyboard = InlineKeyboardButton(text='Добавить в беседу',
                                             url='https://t.me/SisiTestDevBot?startgroup=true')
start_keyboard.add(button_start_keyboard)

