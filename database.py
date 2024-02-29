import sqlite3 as sq

conn = sq.connect('database.db')
cursor = conn.cursor()


async def database_info():
    cursor.execute("CREATE TABLE IF NOT EXISTS money("
                   "user_id INTEGER PRIMARY KEY, "
                   "username TEXT, "
                   "money INTEGER,  "
                   "buy_attempts INTEGER,"
                   "size INTEGER )")
    conn.commit()


async def add_user(user_id, username, money, buy_attempts, size):
    cursor.execute("SELECT user_id, username, money FROM money WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO money (user_id, username, money, buy_attempts, size) VALUES (?, ?, ?, ?, ?)",
                       (user_id, username, money, buy_attempts, size))
        print("[INFO] Пользователь добавлен в БД.")
