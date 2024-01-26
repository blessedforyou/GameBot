from aiogram import Bot, Dispatcher, executor, types
from dotenv import load_dotenv
import os

load_dotenv()
token = Bot(os.getenv('TOKEN'))
bot = Dispatcher(token)


@bot.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(f"{message.from_user.first_name}, добро пожаловать в магазин кроссовок!")


@bot.message_handler()
async def answer(message: types.Message):
    await message.reply("Я тебя не понимаю.")


if __name__ == '__main__':
    executor.start_polling(bot)