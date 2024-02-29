import random
import os
from datetime import timedelta, datetime
from aiogram import Bot, Dispatcher, executor, types
from dotenv import load_dotenv
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from setting import keyboard as kb
from setting import setting as st
import database as db

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv('TOKEN')


async def on_startup(_):
    await db.database_info()


# Инициализация бота и диспетчера
bot = Bot(TOKEN)
dp = Dispatcher(bot)

# Словари
last_usage_dice = {}
last_usage_money = {}


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton(text='Добавить в чат', url='https://t.me/SisiDevTestBot?startgroup=True')
    keyboard.add(button1)

    if message.chat.type == 'private':
        await message.answer("СисиБот - развлекательный бот для чатов."
                             "\nЖми на кнопку и добавляй меня в беседу!", reply_markup=kb.start_keyboard)
    else:
        await message.answer("Привет! Если хочешь узнать мои команды, вводи - /help")


@dp.message_handler(commands=['help'])
async def help_cmd(message: types.Message):
    if message.from_user.id not in st.admin:
        await message.answer("Список доступных команд:\n"
                             "/help - информация о командах.\n"
                             "/dice - бросить кости.\n"
                             "/money - получение рандомного количества монет.\n"
                             "/size - получение рандомного размера.\n"
                             "/pay - передача денег пользователю. \n"
                             "/buy - покупка дополнительных попыток для игр.")
    else:
        await message.answer("Список доступных команд:\n"
                             "/help - информация о командах.\n"
                             "/dice - бросить кости.\n"
                             "/money - получение рандомного количества монет.\n"
                             "/size - получение рандомного размера.\n"
                             "/pay - передача денег пользователю.\n"
                             "/buy - покупка дополнительных попыток.\n\n"
                             "Команды администратора:\n"
                             "/set_money - выдать деньги пользователю.\n"
                             "<i>Arguments: «ID» «VALUE» </i>\n"
                             "/delete_user - удалить пользователя из БД.\n"
                             "<i>Arguments: «ID» </i>\n"
                             "/setting - произвольная настройка игры в крокодила.",
                             parse_mode='html')


@dp.message_handler(commands=['dice'])
async def dice(message: types.Message):
    if message.chat.type == 'private':
        await message.answer("Использование доступно только в чатах.")
        return

    time_to_free_dice = timedelta(hours=1)

    if message.from_user.id in last_usage_dice:
        time_since_last_use = datetime.now() - last_usage_dice[message.from_user.id]
        if time_since_last_use < time_to_free_dice:
            time_remaining = time_to_free_dice - time_since_last_use
            hours, remainder = divmod(time_remaining.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            await message.answer(f"<b>Повторное использование будет доступно через {hours} часов {minutes} минут</b>",
                                 parse_mode='html')
            return

    message_split = message.text.split()
    if len(message_split) < 2:
        await message.answer("Ошибка использования команды.\n"
                             "<i>Arguments:  «MONEY»</i>",
                             parse_mode='html')
        return

    diller_dice = random.randint(1, 6) + random.randint(1, 6)
    player_dice = random.randint(1, 6) + random.randint(1, 6)

    try:
        bet = int(message_split[1])
        money_result = db.cursor.execute("SELECT money FROM money WHERE user_id = ?",
                                         (message.from_user.id,)).fetchone()[0]

        if len(message_split) == 2:
            if bet > money_result:
                await message.reply("Сумма ставки не должна превышать ваш баланс.")

            elif bet <= money_result:
                if diller_dice == player_dice:
                    await message.reply(f'🎲  Результат броска костей.\n\n'
                                        f'Бот - {diller_dice}\n'
                                        f'Игрок - {player_dice}\n'
                                        f'\nНичья!')

                elif diller_dice > player_dice:
                    last_usage_dice[message.from_user.id] = datetime.now()
                    money_with_win_bet = money_result - bet
                    db.cursor.execute("UPDATE money SET money = ? WHERE user_id = ?",
                                      (money_with_win_bet, message.from_user.id))

                    await message.answer(f"🎲 <b>Результаты броска костей</b>:\n\n"
                                         f"<i>Ставка</i> - {bet} монет.\n"
                                         f"<i>Ваш бросок</i> - {player_dice}.\n"
                                         f"<i>Бросок бота</i> - {diller_dice}.\n\n"
                                         f"<b>Победил бот</b>\n"
                                         f"<i>Новый баланс</i>  - {money_with_win_bet}",
                                         parse_mode="HTML")
                    db.conn.commit()

                elif diller_dice < player_dice:
                    last_usage_dice[message.from_user.id] = datetime.now()
                    money_with_lose_bet = money_result + bet
                    db.cursor.execute("UPDATE money SET money = ? WHERE user_id = ?",
                                      (money_with_lose_bet, message.from_user.id))

                    await message.answer(f"🎲 <b>Результаты броска костей</b>:\n\n"
                                         f"<i>Ставка</i> - {bet} монет.\n"
                                         f"<i>Ваш бросок</i> - {player_dice}.\n"
                                         f"<i>Бросок бота</i> - {diller_dice}.\n\n"
                                         f"<b>Вы победили!</b>\n"
                                         f"<i>Новый баланс</i>  - {money_with_lose_bet}",
                                         parse_mode='html')
                    db.conn.commit()

    except TypeError or ValueError:
        if TypeError:
            await message.answer("Пользователь не найден в БД.")
        elif ValueError:
            await message.answer("Второй аргумент должен быть представлен в виде суммы.")


@dp.message_handler(commands=['money'])
async def money(message: types.Message):
    # Ограничение на чаты.
    if message.chat.type == 'private':
        await message.answer("Использование доступно только в чатах.")
        return

    time_to_free_money = timedelta(hours=6)

    if message.from_user.id in last_usage_money:
        time_since_last_use = datetime.now() - last_usage_money[message.from_user.id]
        if time_since_last_use < time_to_free_money:
            time_remaining = time_to_free_money - time_since_last_use
            hours, remainder = divmod(time_remaining.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            await message.answer(f"<b>Повторное использование будет доступно "
                                 f"через {hours} часов {minutes} минут</b>",
                                 parse_mode='html')
            return

    # Добавление юзера в БД.
    await db.add_user(message.from_user.id, message.from_user.username, 0, 0, 0)

    result = db.cursor.execute('SELECT money FROM money WHERE user_id = ?',
                               (message.from_user.id,)).fetchone()[0]

    random_money = random.randint(1600, 2200)
    new_money = result + random_money

    if random_money in [61, 71]:
        await message.answer(f"👤<b>{message.from_user.first_name}</b>, тебе удалось заработать "
                             f"<i>{random_money} монету</i>."
                             f"\n💰<b>Текущий баланс</b>: <i>{new_money} монет</i>", parse_mode='HTML')

    elif random_money in [60, 65, 66, 67, 68, 69, 70, 75, 76, 77, 78, 79, 80]:
        await message.answer(f"👤<b>{message.from_user.first_name}</b>, тебе удалось заработать "
                             f"<i>{random_money} монет</i>."
                             f"\n💰<b>Текущий баланс</b>: <i>{new_money} монет</i>", parse_mode='HTML')

    else:
        await message.answer(f"👤<b>{message.from_user.first_name}</b>, тебе удалось заработать "
                             f"<i>{random_money} монеты</i>."
                             f"\n💰<b>Текущий баланс</b>: <i>{new_money} монет</i>", parse_mode='HTML')

    db.cursor.execute("UPDATE money SET money = ? WHERE user_id = ?", (new_money, message.from_user.id))
    db.conn.commit()

    last_usage_money[message.from_user.id] = datetime.now()


@dp.message_handler(commands=['buy'])
async def buy(message: types.Message):
    # Стоимость одной попытки
    price = 250

    try:

        result_money = db.cursor.execute("SELECT money FROM money WHERE user_id = ?",
                                         (message.from_user.id,)).fetchone()[0]
        result_buy_attempts = db.cursor.execute("SELECT buy_attempts FROM money WHERE user_id = ?",
                                                (message.from_user.id,)).fetchone()[0]

        if result_money >= price:

            new_attempts = result_buy_attempts + 1
            new_money = result_money - price

            await message.answer(f"<b> {message.from_user.first_name}</b>, "
                                 f"дополнительная попытка приобретена успешно."
                                 f"\n<b> Баланс</b>: {new_money} монет.", parse_mode='HTML')
            db.cursor.execute("UPDATE money SET money = ?, buy_attempts = ? WHERE user_id = ?",
                              (new_money, new_attempts, message.from_user.id))
            db.conn.commit()

        elif result_money < price:
            await message.answer(f"<b> {message.from_user.first_name}</b>, недостаточно монет."
                                 f"\n<b> Баланс</b>: {result_money} монет."
                                 f"\n<b> Стоимость</b>: {price} монет.", parse_mode="HTML")
    except TypeError as e:
        await message.answer(f"{e}")


@dp.message_handler(commands=['pay'])
async def pay(message: types.Message):
    if message.chat.type == 'private':
        await message.answer("Использование доступно только в чатах.")
        return

    split_message = message.text.split()

    # Количество аргументов после ввода < 3: Error: /pay 1; Correct: /pay <Username> <Money>
    if len(split_message) < 3:
        await bot.send_message(message.chat.id,
                               f"{message.from_user.first_name}, количество аргументов должно быть равно 3-ём.\n\n"
                               f"<i>Arguments:  «USERNAME»  «MONEY»</i>",
                               parse_mode='html')
        return

    try:
        transfer_to_user = str(split_message[1])
        transfer_amount = int(split_message[2])
        name_user_use_command = db.cursor.execute("SELECT username FROM money WHERE user_id = ?",
                                                  (message.from_user.id,)).fetchone()[0]

        if transfer_to_user == name_user_use_command:
            await message.answer("Невозможно выполнить перевод самому себе.")
            return

        result_money = db.cursor.execute("SELECT money FROM money WHERE user_id = ?",
                                         (message.from_user.id,)).fetchone()

        result_money = result_money[0]

        if transfer_amount > result_money:
            await message.answer(f"{message.from_user.first_name}, сумма перевода превышает твой баланс.")
            return

        receiver_money = db.cursor.execute("SELECT money FROM money WHERE username = ?", (transfer_to_user,)).fetchone()
        if receiver_money is None:
            await message.answer("Пользователь для перевода не найден в базе данных.")
            return

        receiver_money = receiver_money[0]

        new_sender_balance = result_money - transfer_amount
        new_receiver_balance = transfer_amount + receiver_money
        db.cursor.execute("UPDATE money SET money = ? WHERE user_id = ?", (new_sender_balance, message.from_user.id))
        db.cursor.execute("UPDATE money SET money = ? WHERE username = ?", (new_receiver_balance, transfer_to_user))
        db.conn.commit()

        await bot.send_message(message.chat.id,
                               f"<b>{message.from_user.first_name}</b>, перевод успешно выполнен."
                               f"\n<b>Ваш новый баланс</b>: <i>{new_sender_balance} монет</i>."
                               f"\n<b>Баланс получателя</b>: <i>{new_receiver_balance} монет</i>.",
                               parse_mode='html')

    except TypeError or ValueError:
        if TypeError:
            await message.answer("Пользователь не найден в БД")
        elif ValueError:
            await message.answer("Первый аргумент должен быть типа STRING, второй INTEGER.")


@dp.message_handler(commands=['size'])
async def show_size(message: types.Message):
    if message.chat.type == 'private':
        await message.answer("Использование доступно только в чатах.")
        return

    last_usage_size = {}
    time_to_free_size = timedelta(hours=6)

    if message.from_user.id in last_usage_size:
        time_since_last_use = datetime.now() - last_usage_size[message.from_user.id]
        if time_since_last_use < time_to_free_size:
            time_remaining = time_to_free_size - time_since_last_use
            hours, remainder = divmod(time_remaining.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            await message.answer(f"<b>Повторное использование будет доступно через {hours} часов {minutes} минут</b>",
                                 parse_mode='html')
            return

    try:
        result_size = db.cursor.execute("SELECT size FROM money WHERE user_id = ?",
                                        (message.from_user.id,)).fetchone()[0]
        result_buy_attempts = db.cursor.execute("SELECT buy_attempts FROM money WHERE user_id = ?",
                                                (message.from_user.id,)).fetchone()[0]

        random_size = random.randint(-2, 12)
        new_size = result_size + random_size

        if result_buy_attempts >= 1:
            new_buy_attempts = result_buy_attempts - 1

            if random_size < 0:
                await message.answer(f"👤 <b>{message.from_user.first_name}</b>, размер твоих (🍒)(🍒) "
                                     f"уменьшился на {random_size}"
                                     f"\n🍒 <b>Текущий размер</b>: {new_size} см.", parse_mode='HTML')
            elif random_size > 0:
                await message.answer(f"👤 <b>{message.from_user.first_name}</b>, размер твоих (🍒)(🍒) "
                                     f"увеличился на {random_size} см."
                                     f"\n🍒 <b>Текущий размер</b>: {new_size} см.", parse_mode="HTML")
            elif random_size == 0:
                await message.answer(f"👤 <b>{message.from_user.first_name}</b>, "
                                     f"размер твоих (🍒)(🍒) остался прежним.",
                                     parse_mode="HTML")

            db.cursor.execute("UPDATE money SET size = ? WHERE user_id = ?", (new_size, message.from_user.id))
            db.cursor.execute("UPDATE money SET buy_attempts = ? WHERE user_id = ?",
                              (new_buy_attempts, message.from_user.id))
            db.conn.commit()

        elif result_buy_attempts == 0:
            await message.answer(f"\n\n<i>{message.from_user.first_name}, все попытки были израсходованы</i>.",
                                 parse_mode="HTML")

    except TypeError:
        await message.answer(f"Пользователь не найден в БД.")


@dp.message_handler(commands=['delete_user'])
async def delete_user(message: types.Message):
    # Обработка случая, когда команда пишется в ЛС.
    if message.chat.type == 'private':
        await message.answer("Использование команды доступно только в чатах!")
        return

    # Список для хранения ID пользователей.
    id_in_database = []
    # Выборка всех данных из БД.
    info_in_database = db.cursor.execute("SELECT * FROM money").fetchall()

    # Перебор значений из БД, добавление ID в список.
    for row in info_in_database:
        id_in_database.append(row[0])

    # Разбиение текста на части
    message_split = message.text.split()
    if len(message_split) < 2:
        await message.answer("Ошибка использования команды.")
        return

    try:
        message_id = int(message_split[1])
        if message.from_user.username == 'blessedforuu':
            if message_id not in id_in_database:
                await message.answer(f"Пользователь с ID {message_id} не найден в БД.")
            else:
                db.cursor.execute("DELETE FROM money WHERE user_id = ?", (message_id,))
                db.conn.commit()
                await message.answer(f"Пользователь был успешно удален из БД.")
        else:
            await message.answer("У вас нет доступа.")
    except ValueError:
        await message.answer("Второй аргумент должен быть типа INTEGER.")


@dp.message_handler(commands=['info'])
async def info(message: types.Message):
    if message.chat.type == 'private':
        await message.answer("Использование недоступно в личных сообщениях.")
        return

    try:
        money = db.cursor.execute("SELECT money FROM money WHERE user_id = ?", (message.from_user.id,)).fetchone()[0]
        size = db.cursor.execute("SELECT size FROM money WHERE user_id = ?", (message.from_user.id,)).fetchone()[0]
        all_user = db.cursor.execute("SELECT * FROM money").fetchall()

        info_user = {}

        for i in all_user:
            info_user[i[0]] = i[1]

        if message.from_user.id == 1264189868:
            await message.answer(f"[Информация]\n\n"
                                 f"Имя: {message.from_user.first_name}\n"
                                 f"Баланс: {money}\n\n"
                                 f"[Information for Admin]\n\n"
                                 f"<span class='tg-spoiler'>{info_user}</span>",
                                 parse_mode='html')
        else:
            await message.answer(f"<b>[Информация]</b>\n\n"
                                 f"<b>Имя</b>: <i>{message.from_user.first_name}</i>\n"
                                 f"<b>Монеты</b>: <i>{money} монет</i>\n"
                                 f"<b>Размер</b>: <i>{size} см.</i>\n",
                                 parse_mode='html')

    except TypeError:
        await message.answer("Пользователь не найден в Базе Данных.")


@dp.message_handler(commands=['set_money'])
async def set_money(message: types.Message):
    if message.chat.type == 'private':
        await message.answer("Использование в личных сообщениях недоступно.")
        return

    message_split = message.text.split()

    if len(message_split) < 3:
        await message.answer("Неверное использование команды.")
        return

    try:
        name = str(message_split[1])
        give_money = int(message_split[2])

        name_in_database = []
        for user in db.cursor.execute("SELECT * FROM money").fetchall():
            name_in_database.append(user[1])

        if message.from_user.id == 1264189868:
            if name not in name_in_database:
                await message.answer("Пользователь не найден в БД.")
            else:
                db.cursor.execute("UPDATE money SET money = ? WHERE username = ?", (give_money, name))
                db.conn.commit()
                await message.answer(f"Баланс пользователя {name} изменён.")
        else:
            await message.answer("У вас нет доступа!")

    except ValueError:
        await message.answer("<<Username>> <<Amount>>")


# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
