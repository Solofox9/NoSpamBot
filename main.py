import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ChatType
import sqlite3

# Config
TOKEN = "8210861967:AAFWXYLVZOgX-SPKkaIzZ_TxSiNfLsw0q2U"
ADMIN_ID = 1573111356

# Logging
logging.basicConfig(level=logging.INFO)

# Bot and Dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher()

# SQLite DB
def init_db():
    conn = sqlite3.connect("mongodb+srv://tdanimehub_db_user:cPdMT253KSZpE11Z@helper.wallqjf.mongodb.net/?retryWrites=true&w=majority&appName=Helper")
    c = conn.cursor()
    c.execute("mongodb+srv://tdanimehub_db_user:cPdMT253KSZpE11Z@helper.wallqjf.mongodb.net/?retryWrites=true&w=majority&appName=Helper"mongodb+srv://tdanimehub_db_user:3fPbmCdShf91FPZ9@storage1.gwel1e6.mongodb.net/?retryWrites=true&w=majority&appName=Storage1"
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            chat_id INTEGER,
            msg_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Command: /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.reply("Spam bot detector is active!")

# Message handler
@dp.message()
async def check_spam(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    conn = sqlite3.connect("spam_bot.db")
    c = conn.cursor()

    # Check or create user
    c.execute("SELECT msg_count FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()

    if row:
        msg_count = row[0] + 1
        c.execute("UPDATE users SET msg_count = ? WHERE user_id = ?", (msg_count, user_id))
    else:
        c.execute("INSERT INTO users (user_id, chat_id, msg_count) VALUES (?, ?, 1)", (user_id, chat_id))
    
    conn.commit()
    conn.close()

    # Spam check
    if row and msg_count > 5:  # Example threshold
        await message.reply(f"User {user_id} might be spamming!")

# Main
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
